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
