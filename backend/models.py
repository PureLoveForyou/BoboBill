from pydantic import BaseModel
from typing import Optional, List


class BillModel(BaseModel):
    id: Optional[int] = None
    name: str
    amount: float
    type: str
    date: str
    category: Optional[str] = None
    platform: Optional[str] = None
    merchant: Optional[str] = None
    note: Optional[str] = None
    transaction_id: Optional[str] = None


class ImportResult(BaseModel):
    success: int
    skipped: int
    total: int
    message: str


class PaginatedResponse(BaseModel):
    items: List[BillModel]
    total: int
    page: int
    page_size: int


# ===== 用户认证模型 =====

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ===== AI 配置模型 =====

class AIConfigCreate(BaseModel):
    name: str = "Default"
    provider: str = "deepseek"
    api_key: str
    api_url: str = ""
    model: str = "deepseek-chat"


class AIConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    model: Optional[str] = None


class AIConfigResponse(BaseModel):
    id: int
    name: str
    provider: str
    api_key: str  # 脱敏：仅返回后4位
    api_url: str
    model: str


class AIConfigDetail(BaseModel):
    """完整配置（仅保存时使用，不对外暴露完整 key）"""
    id: int
    name: str
    provider: str
    api_key: str
    api_url: str
    model: str


# ===== AI 对话历史模型 =====

class ChatSessionCreate(BaseModel):
    title: str = "新对话"


class ChatMessageCreate(BaseModel):
    role: str
    content: str
    reasoning: Optional[str] = None
    tool_calls: Optional[str] = None  # JSON 字符串，如 [{"name":"get_current_time","description":"获取当前时间","status":"done"}]


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    reasoning: Optional[str] = None
    tool_calls: Optional[str] = None


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    created_at: float
    updated_at: float
    message_count: Optional[int] = 0
    preview: Optional[str] = ""  # 最后一条消息预览
