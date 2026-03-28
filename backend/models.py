from pydantic import BaseModel
from typing import Optional


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
