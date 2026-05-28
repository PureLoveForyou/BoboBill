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


def _apply_filters(query, category=None, platform=None, start_date=None, end_date=None, min_amount=None, max_amount=None, search=None):
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
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Bill.name.ilike(search_term) |
            Bill.note.ilike(search_term) |
            Bill.merchant.ilike(search_term) |
            Bill.category.ilike(search_term)
        )
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
    query = _apply_filters(query, category, platform, start_date, end_date, min_amount, max_amount, search)
    query = query.order_by(Bill.date.desc())

    if page > 0 and page_size > 0:
        total = query.count()
        bills = query.offset((page - 1) * page_size).limit(page_size).all()
        items = [_bill_to_dict(b) for b in bills]
    else:
        bills = query.all()
        items = [_bill_to_dict(b) for b in bills]
        total = len(items)

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
    base = db.query(Bill).filter(Bill.user_id == current_user.id, Bill.type != "budget")

    total_income = base.filter(Bill.amount > 0).with_entities(func.sum(Bill.amount)).scalar() or 0
    total_expense = base.filter(Bill.amount < 0).with_entities(func.abs(func.sum(Bill.amount))).scalar() or 0
    total_count = base.count()

    cat_rows = base.filter(Bill.amount < 0, Bill.category.isnot(None)).with_entities(
        Bill.category, func.sum(func.abs(Bill.amount))
    ).group_by(Bill.category).all()
    category_stats = {cat or '其他': round(amt, 2) for cat, amt in cat_rows}

    plat_rows = base.with_entities(
        Bill.platform, func.count(Bill.id)
    ).group_by(Bill.platform).all()
    platform_stats = {plat or 'unknown': cnt for plat, cnt in plat_rows}

    return {
        "total_count": total_count,
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "balance": round(total_income - total_expense, 2),
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
    query = _apply_filters(query, category, platform, start_date, end_date, min_amount, max_amount, search)
    query = query.order_by(Bill.date.desc())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "名称", "分类", "平台", "金额", "类型", "备注"])

    for bill in query.all():
        bd = _bill_to_dict(bill)
        amount = bd.get("amount", 0)
        bill_type = "收入" if amount >= 0 else "支出"
        plat_name = PLATFORM_NAMES.get(bd.get("platform", ""), bd.get("platform", ""))
        writer.writerow([
            bd.get("date", ""),
            bd.get("name", ""),
            bd.get("category", "其他"),
            plat_name,
            abs(amount),
            bill_type,
            bd.get("note", ""),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": "attachment; filename=bills.csv"},
    )
