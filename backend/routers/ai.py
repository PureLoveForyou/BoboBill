"""AI 账单助手：支持 DeepSeek 和 OpenAI 兼容接口，支持流式输出 + Function Calling"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
import json
import httpx
from datetime import datetime, timedelta

from database import get_db, Bill, User, UserAIConfig, ChatSession as DBChatSession, ChatMessage as DBChatMessage
from auth import get_current_user
from models import (AIConfigCreate, AIConfigUpdate, AIConfigResponse, AIConfigDetail,
                    ChatSessionCreate, ChatMessageCreate, ChatSessionResponse, ChatMessageResponse)

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


# ===== 系统提示词 =====
_DEFAULT_SYSTEM_PROMPT_TEMPLATE = """你是 BoboBill 的智能账单助手，一个专业的个人财务管理 AI。你可以通过调用工具来查询用户的账单数据，然后基于查询结果回答问题。

工作方式：
1. 如果用户的问题涉及时间（如"上个月""昨天""今年"），请先调用 get_current_time 获取当前日期
2. 根据用户的问题，决定需要调用哪些工具来获取数据
3. 你可以一次调用多个工具，也可以先调用一个再根据结果决定是否需要更多信息
4. 基于工具返回的真实数据来回答用户问题
5. 如果数据不足以回答，可以再次调用工具获取更多信息

重要规则：
- 只基于工具查询到的真实数据回答，不要编造任何数字
- 如果查询结果为空，如实告知用户没有相关数据
- 用中文回复（除非用户使用其他语言）
- 回答要简洁、实用、有洞察力
- 金额以人民币（¥）为单位
- 日期格式使用 YYYY-MM-DD"""


def _get_system_prompt() -> str:
    return _DEFAULT_SYSTEM_PROMPT_TEMPLATE

# ===== Function Calling 工具定义 =====

BILL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间。在回答任何涉及时间的问题之前（如「上个月」「上周」「昨天」「今天」等），必须先调用此工具获取准确的当前时间。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_bills",
            "description": "按条件查询账单明细列表。支持按日期范围、分类、类型、关键词等筛选。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "起始日期，格式 YYYY-MM-DD，如 2026-01-01"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "结束日期，格式 YYYY-MM-DD，如 2026-03-31"
                    },
                    "category": {
                        "type": "string",
                        "description": "账单分类，如：餐饮、交通、购物、娱乐、医疗、教育、工资、投资、转账等"
                    },
                    "bill_type": {
                        "type": "string",
                        "enum": ["expense", "income"],
                        "description": "账单类型：expense=支出，income=收入"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "关键词搜索，匹配账单名称、商户、备注"
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "最小金额（绝对值）"
                    },
                    "max_amount": {
                        "type": "number",
                        "description": "最大金额（绝对值）"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数上限，默认20，最大50",
                        "default": 20
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_bill_summary",
            "description": "获取账单汇总统计：总支出、总收入、各分类支出、各分类占比等。适合回答「花了多少」「各类占比」等概览性问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "起始日期，格式 YYYY-MM-DD"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "结束日期，格式 YYYY-MM-DD"
                    },
                    "bill_type": {
                        "type": "string",
                        "enum": ["expense", "income"],
                        "description": "账单类型：expense=仅看支出，income=仅看收入，不传=都看"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_ranking",
            "description": "获取支出或收入的分类排行。适合回答「哪个分类花得最多」「餐饮排第几」等问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "起始日期，格式 YYYY-MM-DD"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "结束日期，格式 YYYY-MM-DD"
                    },
                    "bill_type": {
                        "type": "string",
                        "enum": ["expense", "income"],
                        "description": "账单类型，默认expense",
                        "default": "expense"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回前N个分类，默认10",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    }
]


# ===== 工具执行函数 =====

def _execute_query_bills(db: Session, user_id: int, args: dict) -> str:
    """执行 query_bills 工具"""
    query = db.query(Bill).filter(Bill.user_id == user_id)

    if args.get("start_date"):
        query = query.filter(Bill.date >= args["start_date"])
    if args.get("end_date"):
        query = query.filter(Bill.date <= args["end_date"])
    if args.get("category"):
        query = query.filter(Bill.category == args["category"])
    if args.get("bill_type"):
        query = query.filter(Bill.type == args["bill_type"])
    if args.get("min_amount") is not None:
        query = query.filter(Bill.amount >= args["min_amount"])
    if args.get("max_amount") is not None:
        query = query.filter(Bill.amount <= args["max_amount"])

    limit = min(args.get("limit", 20), 50)
    bills = query.order_by(Bill.date.desc()).limit(limit).all()

    if not bills:
        return "没有找到符合条件的账单记录。"

    lines = [f"共找到 {len(bills)} 条账单："]
    for b in bills:
        type_label = "支出" if b.type == "expense" else "收入"
        lines.append(f"  {b.date} | {type_label} | ¥{b.amount:.2f} | {b.name} | {b.category or '未分类'} | {b.platform or '-'} | {b.merchant or ''}")
    return "\n".join(lines)


def _execute_get_bill_summary(db: Session, user_id: int, args: dict) -> str:
    """执行 get_bill_summary 工具"""
    query = db.query(Bill).filter(Bill.user_id == user_id)
    if args.get("start_date"):
        query = query.filter(Bill.date >= args["start_date"])
    if args.get("end_date"):
        query = query.filter(Bill.date <= args["end_date"])

    bill_type = args.get("bill_type")

    if bill_type == "expense":
        expense_query = query.filter(Bill.type == "expense")
        total_expense = expense_query.with_entities(func.sum(Bill.amount)).scalar() or 0
        count = expense_query.count()
        # 分类明细
        cat_data = expense_query.with_entities(Bill.category, func.sum(Bill.amount).label('total')).filter(
            Bill.category.isnot(None)).group_by(Bill.category).order_by(desc('total')).all()
        lines = [
            f"统计期间支出总额：¥{total_expense:.2f}，共 {count} 笔",
            "",
            "各分类支出："
        ]
        for cat, total in cat_data:
            pct = (total / total_expense * 100) if total_expense > 0 else 0
            lines.append(f"  {cat or '未分类'}：¥{total:.2f}（{pct:.1f}%）")
        return "\n".join(lines)

    elif bill_type == "income":
        income_query = query.filter(Bill.type == "income")
        total_income = income_query.with_entities(func.sum(Bill.amount)).scalar() or 0
        count = income_query.count()
        cat_data = income_query.with_entities(Bill.category, func.sum(Bill.amount).label('total')).filter(
            Bill.category.isnot(None)).group_by(Bill.category).order_by(desc('total')).all()
        lines = [
            f"统计期间收入总额：¥{total_income:.2f}，共 {count} 笔",
            "",
            "各分类收入："
        ]
        for cat, total in cat_data:
            pct = (total / total_income * 100) if total_income > 0 else 0
            lines.append(f"  {cat or '未分类'}：¥{total:.2f}（{pct:.1f}%）")
        return "\n".join(lines)

    else:
        total_expense = query.filter(Bill.type == "expense").with_entities(func.sum(Bill.amount)).scalar() or 0
        total_income = query.filter(Bill.type == "income").with_entities(func.sum(Bill.amount)).scalar() or 0
        total_count = query.count()
        balance = total_income - total_expense
        lines = [
            f"总账单数：{total_count} 笔",
            f"总支出：¥{total_expense:.2f}",
            f"总收入：¥{total_income:.2f}",
            f"结余：¥{balance:.2f}",
        ]
        # 支出分类 TOP5
        cat_data = query.filter(Bill.type == "expense", Bill.category.isnot(None)).with_entities(
            Bill.category, func.sum(Bill.amount).label('total')).group_by(Bill.category).order_by(desc('total')).limit(5).all()
        if cat_data:
            lines.append("")
            lines.append("支出分类 TOP5：")
            for cat, total in cat_data:
                pct = (total / total_expense * 100) if total_expense > 0 else 0
                lines.append(f"  {cat}：¥{total:.2f}（{pct:.1f}%）")
        return "\n".join(lines)


def _execute_get_category_ranking(db: Session, user_id: int, args: dict) -> str:
    """执行 get_category_ranking 工具"""
    query = db.query(Bill).filter(Bill.user_id == user_id)
    if args.get("start_date"):
        query = query.filter(Bill.date >= args["start_date"])
    if args.get("end_date"):
        query = query.filter(Bill.date <= args["end_date"])

    bill_type = args.get("bill_type", "expense")
    limit = min(args.get("limit", 10), 20)

    type_query = query.filter(Bill.type == bill_type)
    total = type_query.with_entities(func.sum(Bill.amount)).scalar() or 0

    cat_data = type_query.filter(Bill.category.isnot(None)).with_entities(
        Bill.category, func.sum(Bill.amount).label('total'), func.count(Bill.id).label('count')
    ).group_by(Bill.category).order_by(desc('total')).limit(limit).all()

    type_label = "支出" if bill_type == "expense" else "收入"
    if not cat_data:
        return f"没有找到{type_label}分类数据。"

    lines = [f"{type_label}分类排行（总额：¥{total:.2f}）："]
    for i, (cat, amount, count) in enumerate(cat_data, 1):
        pct = (amount / total * 100) if total > 0 else 0
        lines.append(f"  {i}. {cat}：¥{amount:.2f}（{pct:.1f}%，{count}笔）")
    return "\n".join(lines)


# 工具名 -> 执行函数 映射（扩展点：以后加技能只需在此注册）
TOOL_HANDLERS = {
    "get_current_time": lambda db, uid, args: datetime.now().strftime("%Y-%m-%d %H:%M:%S %A"),
    "query_bills": _execute_query_bills,
    "get_bill_summary": _execute_get_bill_summary,
    "get_category_ranking": _execute_get_category_ranking,
}


def _execute_tool(db: Session, user_id: int, tool_name: str, tool_args: dict) -> str:
    """执行指定工具并返回结果字符串"""
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return f"未知工具：{tool_name}"
    try:
        return handler(db, user_id, tool_args)
    except Exception as e:
        return f"工具执行出错：{str(e)}"


def _tool_call_description(tool_name: str, args: dict) -> str:
    """生成工具调用的可读描述，用于前端展示"""
    if tool_name == "get_current_time":
        return "获取当前时间"
    elif tool_name == "query_bills":
        parts = []
        if args.get("start_date") or args.get("end_date"):
            parts.append(f"{args.get('start_date', '...')} ~ {args.get('end_date', '...')}")
        if args.get("category"):
            parts.append(f"分类：{args['category']}")
        if args.get("bill_type"):
            label = "支出" if args["bill_type"] == "expense" else "收入"
            parts.append(f"类型：{label}")
        if args.get("keyword"):
            parts.append(f"搜索：{args['keyword']}")
        return "查询账单明细" + ("（" + "，".join(parts) + "）" if parts else "")
    elif tool_name == "get_bill_summary":
        parts = []
        if args.get("start_date") or args.get("end_date"):
            parts.append(f"{args.get('start_date', '...')} ~ {args.get('end_date', '...')}")
        return "账单汇总统计" + ("（" + "，".join(parts) + "）" if parts else "")
    elif tool_name == "get_category_ranking":
        parts = []
        if args.get("start_date") or args.get("end_date"):
            parts.append(f"{args.get('start_date', '...')} ~ {args.get('end_date', '...')}")
        return "分类排行" + ("（" + "，".join(parts) + "）" if parts else "")
    else:
        return f"调用 {tool_name}"


def _get_endpoint(settings: AISettings) -> str:
    """根据 provider 和 api_url 计算接口地址"""
    url = settings.api_url.rstrip("/")
    if settings.provider == "deepseek":
        base_url = url or "https://api.deepseek.com"
        return f"{base_url}/chat/completions"
    else:
        base_url = url or "https://api.openai.com"
        return f"{base_url}/v1/chat/completions"


async def _call_llm_raw(settings: AISettings, messages: list[dict], tools: list[dict] = None) -> dict:
    """调用 LLM API（非流式），返回完整 response JSON"""
    endpoint = _get_endpoint(settings)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.api_key}"
    }
    payload = {
        "model": settings.model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4096,
        "stream": False
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(endpoint, headers=headers, json=payload)
        if response.status_code != 200:
            error_text = response.text[:500]
            raise HTTPException(status_code=response.status_code, detail=f"API 错误 ({response.status_code}): {error_text}")
        return response.json()


async def _agent_loop_non_stream(settings: AISettings, messages: list[dict], db: Session, user_id: int, max_rounds: int = 5) -> str:
    """Agent 循环（非流式）：LLM 可能返回 tool_calls，执行后继续调用，直到得到最终文本回复"""
    for _ in range(max_rounds):
        result = await _call_llm_raw(settings, messages, tools=BILL_TOOLS)
        message = result["choices"][0]["message"]
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            # 没有工具调用，返回文本内容
            return message.get("content", "")

        # 把 assistant 的 tool_calls 消息加入历史
        messages.append(message)

        # 执行每个工具调用
        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])
            tool_result = _execute_tool(db, user_id, fn_name, fn_args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": tool_result
            })

    # 超过最大轮数，再做一次不带 tools 的调用获取最终回复
    result = await _call_llm_raw(settings, messages, tools=None)
    return result["choices"][0]["message"].get("content", "抱歉，处理过程中超出了最大调用次数。")


async def _agent_loop_stream(settings: AISettings, messages: list[dict], db: Session, user_id: int, max_rounds: int = 5):
    """Agent 循环（真正流式）：全程 SSE 流式，tools + stream 完全兼容"""
    endpoint = _get_endpoint(settings)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.api_key}"
    }

    for round_num in range(max_rounds):
        payload = {
            "model": settings.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
            "stream": True,
            "tools": BILL_TOOLS,
            "tool_choice": "auto"
        }

        # 用于从流式 delta 中累积 tool_calls（LLM 的 tool_calls 也是分多个 chunk 传的）
        accumulated_tool_calls = {}  # index -> {id, function: {name, arguments}}

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
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})

                        # DeepSeek 思考过程
                        reasoning = delta.get("reasoning_content")
                        if reasoning:
                            yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning}, ensure_ascii=False)}\n\n"

                        # 正常内容（最终文字回复，逐 token 真正流式！）
                        content = delta.get("content")
                        if content:
                            yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"

                        # tool_calls delta（LLM 决定调用工具时，信息也是逐 chunk 流式传回的）
                        tool_call_deltas = delta.get("tool_calls")
                        if tool_call_deltas:
                            for tcd in tool_call_deltas:
                                idx = tcd.get("index", 0)
                                if idx not in accumulated_tool_calls:
                                    accumulated_tool_calls[idx] = {"id": "", "function": {"name": "", "arguments": ""}}
                                acc_tc = accumulated_tool_calls[idx]

                                # tool_call_id 通常在第一个 chunk 里
                                if tcd.get("id"):
                                    acc_tc["id"] = tcd["id"]

                                # function name 在第一个 chunk 里
                                func_delta = tcd.get("function") or {}
                                if func_delta.get("name"):
                                    acc_tc["function"]["name"] = func_delta["name"]
                                # arguments 是增量拼接的
                                if func_delta.get("arguments"):
                                    acc_tc["function"]["arguments"] += func_delta["arguments"]

                    except json.JSONDecodeError:
                        continue

        # [DONE] 到了，判断这一轮是返回了文本还是要求调工具
        if accumulated_tool_calls:
            # === 阶段 1：通知前端即将执行工具 ===
            for idx in sorted(accumulated_tool_calls.keys()):
                acc = accumulated_tool_calls[idx]
                fn_name = acc["function"]["name"]
                try:
                    fn_args = json.loads(acc["function"]["arguments"])
                except json.JSONDecodeError:
                    fn_args = {}
                desc = _tool_call_description(fn_name, fn_args)
                yield f"data: {json.dumps({'type': 'tool_start', 'content': {'name': fn_name, 'description': desc}}, ensure_ascii=False)}\n\n"

            # 构造完整的 assistant 消息（含 tool_calls）
            tool_call_list = []
            for idx in sorted(accumulated_tool_calls.keys()):
                acc = accumulated_tool_calls[idx]
                tool_call_list.append({
                    "id": acc["id"],
                    "type": "function",
                    "function": {
                        "name": acc["function"]["name"],
                        "arguments": acc["function"]["arguments"],
                    }
                })
            messages.append({"role": "assistant", "content": None, "tool_calls": tool_call_list})

            # === 阶段 2：逐个执行工具并通知结果 ===
            for idx in sorted(accumulated_tool_calls.keys()):
                acc = accumulated_tool_calls[idx]
                fn_name = acc["function"]["name"]
                try:
                    fn_args = json.loads(acc["function"]["arguments"])
                except json.JSONDecodeError:
                    fn_args = {}
                tool_result = _execute_tool(db, user_id, fn_name, fn_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": acc["id"],
                    "content": tool_result
                })
                # 通知前端该工具已完成
                yield f"data: {json.dumps({'type': 'tool_end', 'content': {'name': fn_name, 'description': _tool_call_description(fn_name, fn_args)}}, ensure_ascii=False)}\n\n"

            # 继续下一轮循环（再次发起流式请求）
            continue
        else:
            # 没有 tool_calls：说明 LLM 已经在上方流式发出了最终的 text content
            # 直接结束即可，内容已经通过上面的 content delta 逐 token 发给前端了
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            return

    # 超过最大轮数兜底
    yield f"data: {json.dumps({'type': 'content', 'content': '抱歉，处理过程超出了最大调用次数。'}, ensure_ascii=False)}\n\n"
    yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"


class ConfiguredChatRequest(ChatRequest):
    ai_config_id: int = 0  # 用户选择的 AI 配置 ID
    # 兼容旧客户端：仍可传 provider/key/url/model
    ai_provider: str = "deepseek"
    ai_api_key: str = ""
    ai_api_url: str = ""
    ai_model: str = "deepseek-chat"


def _resolve_settings(req: ConfiguredChatRequest, db: Session, user: User) -> AISettings:
    """解析 AI 设置：优先从数据库配置读取，回退到请求体参数"""
    if req.ai_config_id:
        config = db.query(UserAIConfig).filter_by(id=req.ai_config_id, user_id=user.id).first()
        if config:
            return AISettings(
                provider=config.provider,
                api_key=config.api_key,
                api_url=config.api_url,
                model=config.model,
            )
    # 回退：从请求体读取（兼容旧前端）
    if req.ai_api_key:
        return AISettings(
            provider=req.ai_provider,
            api_key=req.ai_api_key,
            api_url=req.ai_api_url,
            model=req.ai_model,
        )
    return None


def _build_messages(req, system_prompt: str = None) -> list[dict]:
    """构建消息列表（不再注入全量账单数据，由 AI 通过工具按需查询）"""
    messages = [{"role": "system", "content": system_prompt or _get_system_prompt()}]

    # 加入历史对话
    for msg in req.history[-12:]:
        messages.append({"role": msg.role, "content": msg.content})

    # 加入当前问题
    messages.append({"role": "user", "content": req.message})
    return messages


@router.post("/chat")
async def chat(req: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """AI 对话接口（兼容旧端点，需配置才能用）"""
    raise HTTPException(status_code=400, detail="请使用 /ai/chat-full 或 /ai/chat-stream 接口")


@router.post("/chat-with-config")
async def chat_with_config(req: ConfiguredChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """带配置的 AI 对话接口 — 重定向到 chat-full"""
    return await chat_full(req, db, current_user)


@router.post("/chat-full")
async def chat_full(req: ConfiguredChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """完整配置的 AI 对话接口（非流式），支持 Function Calling"""
    settings = _resolve_settings(req, db, current_user)
    if not settings or not settings.api_key:
        raise HTTPException(status_code=400, detail="请先在设置中配置 AI 服务")

    messages = _build_messages(req)

    try:
        reply = await _agent_loop_non_stream(settings, messages, db, current_user.id)
        return {"reply": reply}
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI 服务响应超时，请稍后再试")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 服务错误: {str(e)}")


@router.post("/chat-stream")
async def chat_stream(req: ConfiguredChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """流式 AI 对话接口（SSE），支持 Function Calling + 思考过程"""
    settings = _resolve_settings(req, db, current_user)
    if not settings or not settings.api_key:
        raise HTTPException(status_code=400, detail="请先在设置中配置 AI 服务")

    messages = _build_messages(req)

    async def event_generator():
        try:
            async for sse_event in _agent_loop_stream(settings, messages, db, current_user.id):
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
        result = await _call_llm_raw(settings, test_messages)
        reply = result["choices"][0]["message"]["content"]
        return {"success": True, "message": "连接成功", "reply": reply}
    except httpx.TimeoutException:
        return {"success": False, "message": "连接超时"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ===== AI 配置管理 =====

def _mask_key(key: str) -> str:
    """脱敏 API Key，仅保留后4位"""
    if not key or len(key) <= 4:
        return "****"
    return "*" * (len(key) - 4) + key[-4:]


@router.get("/my-configs")
async def get_my_configs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取当前用户的所有 AI 配置（API Key 脱敏）"""
    configs = db.query(UserAIConfig).filter_by(user_id=current_user.id).order_by(UserAIConfig.id).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "provider": c.provider,
            "api_key": _mask_key(c.api_key),
            "api_url": c.api_url,
            "model": c.model,
        }
        for c in configs
    ]


@router.post("/save-config")
async def save_config(req: AIConfigCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """新增 AI 配置"""
    config = UserAIConfig(
        user_id=current_user.id,
        name=req.name,
        provider=req.provider,
        api_key=req.api_key,
        api_url=req.api_url,
        model=req.model,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return {"id": config.id, "message": "配置已保存"}


@router.put("/update-config/{config_id}")
async def update_config(config_id: int, req: AIConfigUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新 AI 配置（只传需要更新的字段）"""
    config = db.query(UserAIConfig).filter_by(id=config_id, user_id=current_user.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    update_data = req.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    db.commit()
    return {"message": "配置已更新"}


@router.delete("/delete-config/{config_id}")
async def delete_config(config_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除 AI 配置"""
    config = db.query(UserAIConfig).filter_by(id=config_id, user_id=current_user.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    db.delete(config)
    db.commit()
    return {"message": "配置已删除"}


@router.get("/config/{config_id}")
async def get_config_detail(config_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取单个配置详情（含完整 API Key，用于测试连接等场景）"""
    config = db.query(UserAIConfig).filter_by(id=config_id, user_id=current_user.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return {
        "id": config.id,
        "name": config.name,
        "provider": config.provider,
        "api_key": config.api_key,
        "api_url": config.api_url,
        "model": config.model,
    }


# ===== AI 对话历史管理 =====

@router.get("/chats", response_model=list[ChatSessionResponse])
async def get_chat_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取当前用户的所有对话列表"""
    sessions = db.query(DBChatSession).filter_by(user_id=current_user.id).order_by(DBChatSession.updated_at.desc()).all()
    result = []
    for s in sessions:
        msg_count = db.query(DBChatMessage).filter_by(session_id=s.id).count()
        last_msg = db.query(DBChatMessage).filter_by(session_id=s.id).order_by(DBChatMessage.id.desc()).first()
        preview = ""
        if last_msg:
            preview = (last_msg.content or "")[:60]
        result.append({
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at or 0,
            "updated_at": s.updated_at or 0,
            "message_count": msg_count,
            "preview": preview,
        })
    return result


@router.post("/chats", response_model=ChatSessionResponse)
async def create_chat_session(req: ChatSessionCreate = ChatSessionCreate(), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建新对话"""
    now = __import__('time').time()
    session = DBChatSession(
        user_id=current_user.id,
        title=req.title,
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"id": session.id, "title": session.title, "created_at": now, "updated_at": now, "message_count": 0, "preview": ""}


@router.put("/chats/{session_id}/title")
async def update_chat_title(session_id: int, req: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新对话标题"""
    session = db.query(DBChatSession).filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="对话不存在")
    session.title = req.get("title", session.title)
    db.commit()
    return {"message": "标题已更新"}


@router.delete("/chats/{session_id}")
async def delete_chat_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除对话（同时删除其所有消息）"""
    session = db.query(DBChatSession).filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="对话不存在")
    # 删除所有消息
    db.query(DBChatMessage).filter_by(session_id=session_id).delete()
    db.delete(session)
    db.commit()
    return {"message": "对话已删除"}


@router.get("/chats/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_chat_messages(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取某个对话的所有消息"""
    session = db.query(DBChatSession).filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="对话不存在")
    messages = db.query(DBChatMessage).filter_by(session_id=session_id).order_by(DBChatMessage.id.asc()).all()
    return [
        {"id": m.id, "role": m.role, "content": m.content, "reasoning": m.reasoning}
        for m in messages
    ]


@router.post("/chats/{session_id}/messages", response_model=ChatMessageResponse)
async def add_chat_message(session_id: int, req: ChatMessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """添加消息到对话"""
    session = db.query(DBChatSession).filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="对话不存在")
    now = __import__('time').time()
    message = DBChatMessage(
        session_id=session_id,
        role=req.role,
        content=req.content,
        reasoning=req.reasoning,
    )
    db.add(message)
    # 更新会话时间
    session.updated_at = now
    # 如果第一条是用户消息，自动生成标题
    if req.role == "user":
        existing_msgs = db.query(DBChatMessage).filter_by(session_id=session_id).count()
        if existing_msgs == 0 or not session.title or session.title == "新对话":
            session.title = req.content[:30].replace("\n", " ")
    db.commit()
    db.refresh(message)
    return {"id": message.id, "role": message.role, "content": message.content, "reasoning": message.reasoning}


@router.put("/chats/{session_id}/messages/{message_id}")
async def update_chat_message(session_id: int, message_id: int, req: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新消息内容（用于流式完成后保存最终结果）"""
    session = db.query(DBChatSession).filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="对话不存在")
    msg = db.query(DBChatMessage).filter_by(id=message_id, session_id=session_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    if "content" in req:
        msg.content = req["content"]
    if "reasoning" in req:
        msg.reasoning = req["reasoning"]
    db.commit()
    return {"message": "消息已更新"}
