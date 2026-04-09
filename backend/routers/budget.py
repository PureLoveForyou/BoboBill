from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, Dict
import json as json_lib
from sqlalchemy.orm import Session
from database import get_db, Budget, Bill, User
from auth import get_current_user

router = APIRouter(prefix="/budget", tags=["budget"])


class BudgetModel(BaseModel):
    monthly_total: Optional[float] = 0
    category_budgets: Optional[Dict[str, float]] = {}


def _get_budget(db: Session, user_id: int):
    """获取预算记录，不存在则创建"""
    budget = db.query(Budget).filter_by(user_id=user_id).first()
    if not budget:
        budget = Budget(user_id=user_id, monthly_total=0, category_budgets="{}")
        db.add(budget)
        db.commit()
        db.refresh(budget)
    return budget


@router.get("")
def get_budget(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = _get_budget(db, current_user.id)
    try:
        category_budgets = json_lib.loads(doc.category_budgets) if doc.category_budgets else {}
    except (json_lib.JSONDecodeError, TypeError):
        category_budgets = {}
    return {
        "monthly_total": doc.monthly_total or 0,
        "category_budgets": category_budgets,
    }


@router.put("")
def update_budget(budget: BudgetModel, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = _get_budget(db, current_user.id)
    if budget.monthly_total is not None:
        doc.monthly_total = budget.monthly_total
    if budget.category_budgets is not None:
        doc.category_budgets = json_lib.dumps(budget.category_budgets, ensure_ascii=False)
    db.commit()
    db.refresh(doc)

    try:
        category_budgets = json_lib.loads(doc.category_budgets) if doc.category_budgets else {}
    except (json_lib.JSONDecodeError, TypeError):
        category_budgets = {}

    return {
        "monthly_total": doc.monthly_total or 0,
        "category_budgets": category_budgets,
    }


@router.get("/status")
def get_budget_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取当月预算使用情况"""
    from datetime import datetime

    doc = _get_budget(db, current_user.id)
    monthly_total = doc.monthly_total or 0
    try:
        category_budgets = json_lib.loads(doc.category_budgets) if doc.category_budgets else {}
    except (json_lib.JSONDecodeError, TypeError):
        category_budgets = {}

    now = datetime.now()
    month_start = f"{now.year}-{now.month:02d}-01"
    month_end = f"{now.year}-{now.month:02d}-{now.day:02d}"

    month_bills = db.query(Bill).filter(
        Bill.user_id == current_user.id,
        Bill.type != "budget",
        Bill.date >= month_start,
        Bill.date <= month_end,
    ).all()

    total_spent = sum(abs(b.amount) for b in month_bills if b.amount < 0)

    category_spent = {}
    for b in month_bills:
        if b.amount < 0:
            cat = b.category or "其他"
            category_spent[cat] = category_spent.get(cat, 0) + abs(b.amount)

    category_status = {}
    for cat, budget_amount in category_budgets.items():
        spent = category_spent.get(cat, 0)
        category_status[cat] = {
            "budget": budget_amount,
            "spent": spent,
            "remaining": budget_amount - spent,
            "percentage": round(spent / budget_amount * 100, 1) if budget_amount > 0 else 0,
            "over_budget": spent > budget_amount if budget_amount > 0 else False,
        }

    return {
        "monthly_total": monthly_total,
        "total_spent": total_spent,
        "remaining": monthly_total - total_spent,
        "percentage": round(total_spent / monthly_total * 100, 1) if monthly_total > 0 else 0,
        "over_budget": total_spent > monthly_total if monthly_total > 0 else False,
        "category_budgets": category_budgets,
        "category_spent": category_spent,
        "category_status": category_status,
    }
