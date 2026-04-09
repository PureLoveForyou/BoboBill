from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict
from database import db
from tinydb import Query

router = APIRouter(prefix="/budget", tags=["budget"])

BudgetQuery = Query()


class BudgetModel(BaseModel):
    monthly_total: Optional[float] = 0
    category_budgets: Optional[Dict[str, float]] = {}


def _get_budget_doc():
    """获取预算文档，不存在则创建"""
    result = db.search(BudgetQuery.type == "budget")
    if result:
        return result[0]
    doc_id = db.insert({"type": "budget", "monthly_total": 0, "category_budgets": {}})
    return db.get(doc_id=doc_id)


@router.get("")
def get_budget():
    doc = _get_budget_doc()
    return {
        "monthly_total": doc.get("monthly_total", 0),
        "category_budgets": doc.get("category_budgets", {}),
    }


@router.put("")
def update_budget(budget: BudgetModel):
    doc = _get_budget_doc()
    update_data = {}
    if budget.monthly_total is not None:
        update_data["monthly_total"] = budget.monthly_total
    if budget.category_budgets is not None:
        update_data["category_budgets"] = budget.category_budgets
    db.update(update_data, doc_ids=[doc.doc_id])
    updated = db.get(doc_id=doc.doc_id)
    return {
        "monthly_total": updated.get("monthly_total", 0),
        "category_budgets": updated.get("category_budgets", {}),
    }


@router.get("/status")
def get_budget_status():
    """获取当月预算使用情况"""
    from datetime import datetime

    doc = _get_budget_doc()
    monthly_total = doc.get("monthly_total", 0)
    category_budgets = doc.get("category_budgets", {})

    now = datetime.now()
    month_start = f"{now.year}-{now.month:02d}-01"
    month_end = f"{now.year}-{now.month:02d}-{now.day:02d}"

    all_bills = [b for b in db.all() if b.get("type") != "budget"]
    month_bills = [
        b for b in all_bills
        if b.get("date", "") >= month_start and b.get("date", "") <= month_end
    ]

    # 月度总支出
    total_spent = sum(abs(b.get("amount", 0)) for b in month_bills if b.get("amount", 0) < 0)

    # 分类支出
    category_spent = {}
    for b in month_bills:
        if b.get("amount", 0) < 0:
            cat = b.get("category", "其他")
            category_spent[cat] = category_spent.get(cat, 0) + abs(b.get("amount", 0))

    # 分类预算状态
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
