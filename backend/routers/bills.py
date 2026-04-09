from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import csv
import io
from models import BillModel, PaginatedResponse
from database import get_db, Bill, User
from auth import get_current_user, get_current_user_from_query

router = APIRouter(prefix="/bills", tags=["bills"])

DEFAULT_PAGE_SIZE = 20

# 分类英文别名（用于搜索）
CATEGORY_ALIASES = {
    "餐饮": ["food", "catering", "dining", "eat", "meal", "restaurant"],
    "交通": ["transport", "traffic", "subway", "bus", "taxi", "metro"],
    "购物": ["shopping", "buy", "purchase", "store", "mall"],
    "工资": ["salary", "wage", "income", "payroll"],
    "投资": ["investment", "invest", "stock", "fund"],
    "娱乐": ["entertainment", "game", "movie", "fun", "play"],
    "医疗": ["medical", "hospital", "doctor", "health", "medicine"],
    "教育": ["education", "study", "school", "course", "learn"],
    "转账": ["transfer", "remit", "send money"],
    "其他": ["other", "misc", "miscellaneous"]
}


def _bill_to_dict(bill: Bill) -> dict:
    return {
        "id": bill.id,
        "name": bill.name,
        "amount": bill.amount,
        "type": bill.type,
        "date": bill.date,
        "category": bill.category,
        "platform": bill.platform,
        "merchant": bill.merchant,
        "note": bill.note,
        "transaction_id": bill.transaction_id,
    }


def _apply_filters(query, category=None, platform=None, start_date=None, end_date=None, min_amount=None, max_amount=None):
    if category:
        query = query.filter(Bill.category == category)
    if platform:
        query = query.filter(Bill.platform == platform)
    if start_date:
        query = query.filter(Bill.date >= start_date)
    if end_date:
        query = query.filter(Bill.date <= end_date)
    if min_amount is not None:
        query = query.filter(func.abs(Bill.amount) >= min_amount)
    if max_amount is not None:
        query = query.filter(func.abs(Bill.amount) <= max_amount)
    return query


@router.get("", response_model=PaginatedResponse)
def get_bills(
    page: int = Query(0, ge=0),
    page_size: int = Query(0, ge=0),
    category: Optional[str] = None,
    platform: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Bill).filter(Bill.user_id == current_user.id, Bill.type != "budget")
    query = _apply_filters(query, category, platform, start_date, end_date, min_amount, max_amount)

    all_bills = query.all()
    result = []
    search_lower = (search or "").lower()

    for bill in all_bills:
        if search_lower:
            bill_category = bill.category or ""
            searchable_text = " ".join([
                bill.name or "", bill.note or "", bill.merchant or "", bill_category,
            ]).lower()
            text_match = search_lower in searchable_text
            alias_match = False
            if not text_match and bill_category in CATEGORY_ALIASES:
                alias_match = any(
                    search_lower in alias or alias in search_lower
                    for alias in CATEGORY_ALIASES[bill_category]
                )
            if not text_match and not alias_match:
                continue
        result.append(_bill_to_dict(bill))

    result.sort(key=lambda x: x.get("date", ""), reverse=True)
    total = len(result)

    if page > 0 and page_size > 0:
        start = (page - 1) * page_size
        items = result[start:start + page_size]
    else:
        items = result

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=BillModel)
def add_bill(bill: BillModel, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    bill_dict = bill.model_dump(exclude={"id"})
    bill_dict["user_id"] = current_user.id
    new_bill = Bill(**bill_dict)
    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)
    return _bill_to_dict(new_bill)


@router.put("/{bill_id}", response_model=BillModel)
def update_bill(bill_id: int, bill: BillModel, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Bill).filter_by(id=bill_id, user_id=current_user.id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="账单未找到")

    update_data = bill.model_dump(exclude={"id"}, exclude_none=True)
    for key, value in update_data.items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return _bill_to_dict(existing)


@router.delete("/{bill_id}")
def delete_bill(bill_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    deleted = db.query(Bill).filter_by(id=bill_id, user_id=current_user.id).delete()
    if deleted:
        db.commit()
        return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="账单未找到")


@router.post("/batch-delete")
def batch_delete_bills(ids: list[int], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    deleted = db.query(Bill).filter(Bill.id.in_(ids), Bill.user_id == current_user.id).delete(synchronize_session=False)
    db.commit()
    return {"message": f"成功删除 {deleted} 条账单", "deleted": deleted}


@router.delete("")
def clear_all_bills(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Bill).filter_by(user_id=current_user.id).delete(synchronize_session=False)
    db.commit()
    return {"message": "所有账单已清空"}


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    bills_query = db.query(Bill).filter(Bill.user_id == current_user.id, Bill.type != "budget").all()

    total_income = sum(b.amount for b in bills_query if b.amount > 0)
    total_expense = sum(abs(b.amount) for b in bills_query if b.amount < 0)

    category_stats = {}
    platform_stats = {}
    for bill in bills_query:
        amount = abs(bill.amount)
        if bill.amount < 0:
            cat = bill.category or '其他'
            category_stats[cat] = category_stats.get(cat, 0) + amount
        plat = bill.platform or 'unknown'
        platform_stats[plat] = platform_stats.get(plat, 0) + 1

    return {
        "total_count": len(bills_query),
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "category_stats": category_stats,
        "platform_stats": platform_stats,
    }


PLATFORM_NAMES = {"wechat": "微信", "alipay": "支付宝", "bank": "银行卡"}


@router.get("/export")
def export_bills(
    category: Optional[str] = None,
    platform: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_query),
):
    query = db.query(Bill).filter(Bill.user_id == current_user.id, Bill.type != "budget")
    query = _apply_filters(query, category, platform, start_date, end_date, min_amount, max_amount)

    all_bills = query.all()
    search_lower = (search or "").lower()

    result = []
    for bill in all_bills:
        if search_lower:
            searchable_text = " ".join([
                bill.name or "", bill.note or "", bill.merchant or "", bill.category or ""
            ]).lower()
            if search_lower not in searchable_text:
                continue
        result.append(_bill_to_dict(bill))

    result.sort(key=lambda x: x.get("date", ""), reverse=True)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "名称", "分类", "平台", "金额", "类型", "备注"])

    for bill in result:
        amount = bill.get("amount", 0)
        bill_type = "收入" if amount >= 0 else "支出"
        plat_name = PLATFORM_NAMES.get(bill.get("platform", ""), bill.get("platform", ""))
        writer.writerow([
            bill.get("date", ""),
            bill.get("name", ""),
            bill.get("category", "其他"),
            plat_name,
            abs(amount),
            bill_type,
            bill.get("note", ""),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": "attachment; filename=bills.csv"},
    )
