"""AI 账单助手：支持 DeepSeek 和 OpenAI 兼容接口，支持流式输出"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional
import json
import httpx
from datetime import datetime

from database import get_db, Bill, User
from auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatMessage(BaseModel):
    role: str = Field(..., description="system/user/assistant")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list)


class AISettings(BaseModel):
    provider: str = "deepseek"  # deepseek / openai
    api_key: str = ""
    api_url: str = ""
    model: str = "deepseek-chat"
    system_prompt: str = ""


# 默认系统提示词
DEFAULT_SYSTEM_PROMPT = """你是 BoboBill 的智能账单助手，一个专业的个人财务管理 AI。你的职责是帮助用户理解和管理他们的账单数据。

你可以：
1. 回答用户关于消费的问题（如：上个月吃饭花了多少？）
2. 分析用户的消费习惯和趋势
3. 给出节省开支的建议
4. 帮助用户查找特定的账单记录
5. 解释账单分类和统计数据

重要规则：
- 始终基于提供的账单数据进行回答，不要编造数据
- 如果用户的问题无法从数据中回答，请诚实说明
- 用中文回复（除非用户使用其他语言）
- 回答要简洁、实用、有洞察力
- 金额以人民币（¥）为单位
- 日期格式使用 YYYY-MM-DD 或自然语言"""


def _build_bill_context(db: Session, user: User) -> str:
    """构建账单上下文摘要"""
    from sqlalchemy import func

    bills = db.query(Bill).filter_by(user_id=user.id).order_by(Bill.date.desc()).limit(100).all()

    if not bills:
        return "该用户目前没有任何账单数据。"

    # 基础统计
    total_count = db.query(func.count(Bill.id)).filter(Bill.user_id == user.id).scalar()
    total_expense = db.query(func.sum(Bill.amount)).filter(
        Bill.user_id == user.id, Bill.type == "expense").scalar() or 0
    total_income = db.query(func.sum(Bill.amount)).filter(
        Bill.user_id == user.id, Bill.type == "income").scalar() or 0

    # 最近30天的支出
    thirty_days_ago = (datetime.now().replace(day=1) - __import__('datetime').timedelta(days=30)).strftime('%Y-%m-%d')
    recent_bills = db.query(Bill).filter(
        Bill.user_id == user.id,
        Bill.date >= thirty_days_ago,
        Bill.type == "expense"
    ).order_by(Bill.amount.desc()).all()

    # 分类统计
    cat_result = db.query(Bill.category, func.sum(Bill.amount).label('total')).filter(
        Bill.user_id == user.id,
        Bill.type == "expense",
        Bill.category.isnot(None)
    ).group_by(Bill.category).order_by(__import__('sqlalchemy').desc('total')).limit(10).all()

    lines = [
        f"=== 用户账单概览 ===",
        f"总账单数: {total_count} 条",
        f"总支出: ¥{total_expense:.2f}",
        f"总收入: ¥{total_income:.2f}",
        "",
        f"=== 最近30天大额支出 TOP10 ===",
    ]

    for i, b in enumerate(recent_bills[:10], 1):
        lines.append(f"{i}. {b.date} | {b.name} | ¥{b.amount:.2f} | {b.category or '未分类'} | {b.platform or ''}")

    if not recent_bills:
        lines.append("无")

    lines.append("")
    lines.append("=== 支出分类统计 ===")
    for cat, total in cat_result:
        lines.append(f"  {cat or '未分类'}: ¥{total:.2f}")

    lines.append("")
    lines.append("=== 最近20条详细账单 ===")
    for b in bills[:20]:
        line_type = "支出" if b.type == "expense" else "收入"
        lines.append(f"  {b.date} | {line_type} | ¥{b.amount:.2f} | {b.name} | {b.category or '-'} | {b.platform or '-'} | {b.merchant or ''}")

    return "\n".join(lines)


def _get_endpoint(settings: AISettings) -> str:
    """根据 provider 和 api_url 计算接口地址"""
    url = settings.api_url.rstrip("/")
    if settings.provider == "deepseek":
        base_url = url or "https://api.deepseek.com"
        return f"{base_url}/chat/completions"
    else:
        base_url = url or "https://api.openai.com"
        return f"{base_url}/v1/chat/completions"


async def call_llm(settings: AISettings, messages: list[dict]) -> str:
    """调用 LLM API（DeepSeek / OpenAI 兼容格式）——非流式"""
    endpoint = _get_endpoint(settings)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.api_key}"
    }
    payload = {
        "model": settings.model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": False
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(endpoint, headers=headers, json=payload)

        if response.status_code != 200:
            error_text = response.text[:500]
            raise HTTPException(status_code=response.status_code, detail=f"API 错误 ({response.status_code}): {error_text}")

        result = response.json()
        return result["choices"][0]["message"]["content"]


async def call_llm_stream(settings: AISettings, messages: list[dict]):
    """流式调用 LLM API，逐 chunk yield SSE 事件，支持 reasoning_content（DeepSeek 思考过程）"""
    endpoint = _get_endpoint(settings)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.api_key}"
    }
    payload = {
        "model": settings.model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": True
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                error_text = error_body.decode("utf-8", errors="replace")[:500]
                yield f"data: {json.dumps({'type': 'error', 'content': f'API 错误 ({response.status_code}): {error_text}'}, ensure_ascii=False)}\n\n"
                return

            async for line in response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]  # 去掉 "data: " 前缀
                if data_str == "[DONE]":
                    yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                    return
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})

                    # DeepSeek reasoning_content（思考过程）
                    reasoning = delta.get("reasoning_content")
                    if reasoning:
                        yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning}, ensure_ascii=False)}\n\n"

                    # 正常内容
                    content = delta.get("content")
                    if content:
                        yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"
                except json.JSONDecodeError:
                    continue


@router.post("/chat")
async def chat(req: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """AI 对话接口"""
    # 从请求头或默认值获取 AI 设置（简单方案：从 localStorage 传过来）
    settings = AISettings(
        provider="deepseek",
        api_key="",
        api_url="",
        model="deepseek-chat"
    )

    # 构建消息列表
    messages = [
        {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
    ]

    # 注入账单上下文作为第一条用户消息
    bill_context = _build_bill_context(db, current_user)
    messages.append({
        "role": "user",
        "content": f"[以下是我的账单数据，请据此回答问题]\n\n{bill_context}"
    })
    messages.append({
        "role": "assistant",
        "content": "好的，我已经了解了您的账单数据。请问您想了解什么？我可以帮您分析支出、查询账单、给出理财建议等。"
    })

    # 加入历史对话
    for msg in req.history[-12:]:
        messages.append({"role": msg.role, "content": msg.content})

    # 加入当前问题
    messages.append({"role": "user", "content": req.message})

    try:
        reply = await call_llm(settings, messages)
        return {"reply": reply}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 服务调用失败: {str(e)}")


@router.post("/chat-with-config")
async def chat_with_config(req: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """带配置的 AI 对话接口（从请求体传入配置）"""
    # 这个端点接受前端传来的完整配置
    pass  # 将在下面扩展


class ConfiguredChatRequest(ChatRequest):
    ai_provider: str = "deepseek"
    ai_api_key: str = ""
    ai_api_url: str = ""
    ai_model: str = "deepseek-chat"


@router.post("/chat-full")
async def chat_full(req: ConfiguredChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """完整配置的 AI 对话接口（非流式，保留兼容）"""
    if not req.ai_api_key:
        raise HTTPException(status_code=400, detail="请先在设置中配置 AI API Key")

    settings = AISettings(
        provider=req.ai_provider,
        api_key=req.ai_api_key,
        api_url=req.ai_api_url,
        model=req.ai_model
    )

    messages = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
    bill_context = _build_bill_context(db, current_user)
    messages.append({"role": "user", "content": f"[以下是我的账单数据]\n\n{bill_context}"})
    messages.append({"role": "assistant", "content": "好的，我已了解您的账单数据。请提问。"})

    for msg in req.history[-12:]:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": req.message})

    try:
        reply = await call_llm(settings, messages)
        return {"reply": reply}
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI 服务响应超时，请稍后再试")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 服务错误: {str(e)}")


@router.post("/chat-stream")
async def chat_stream(req: ConfiguredChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """流式 AI 对话接口（SSE），支持思考过程显示"""
    if not req.ai_api_key:
        raise HTTPException(status_code=400, detail="请先在设置中配置 AI API Key")

    settings = AISettings(
        provider=req.ai_provider,
        api_key=req.ai_api_key,
        api_url=req.ai_api_url,
        model=req.ai_model
    )

    messages = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
    bill_context = _build_bill_context(db, current_user)
    messages.append({"role": "user", "content": f"[以下是我的账单数据]\n\n{bill_context}"})
    messages.append({"role": "assistant", "content": "好的，我已了解您的账单数据。请提问。"})

    for msg in req.history[-12:]:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": req.message})

    async def event_generator():
        try:
            async for sse_event in call_llm_stream(settings, messages):
                yield sse_event
        except httpx.TimeoutException:
            yield f"data: {json.dumps({'type': 'error', 'content': 'AI 服务响应超时，请稍后再试'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'AI 服务错误: {str(e)}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/test-connection")
async def test_connection(provider: str, api_key: str, api_url: str = "", model: str = ""):
    """测试 AI 连接"""
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key 不能为空")

    actual_model = model or ("deepseek-chat" if provider == "deepseek" else "gpt-3.5-turbo")

    settings = AISettings(
        provider=provider,
        api_key=api_key,
        api_url=api_url,
        model=actual_model
    )

    test_messages = [
        {"role": "user", "content": "你好，这是一条连接测试，请回复'连接成功'"}
    ]

    try:
        reply = await call_llm(settings, test_messages)
        return {"success": True, "message": "连接成功", "reply": reply}
    except httpx.TimeoutException:
        return {"success": False, "message": "连接超时"}
    except Exception as e:
        return {"success": False, "message": str(e)}
