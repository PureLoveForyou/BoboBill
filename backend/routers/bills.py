from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import csv
import io
from models import BillModel, PaginatedResponse
from database import db

router = APIRouter(prefix="/bills", tags=["bills"])

DEFAULT_PAGE_SIZE = 20


@router.get("", response_model=PaginatedResponse)
def get_bills(
    page: int = Query(0, ge=0),
    page_size: int = Query(0, ge=0),
    category: Optional[str] = None,
    platform: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
):
    result = []
    search_lower = (search or "").lower()

    for bill in db.all():
        bill["id"] = bill.doc_id
        if category and bill.get("category") != category:
            continue
        if platform and bill.get("platform") != platform:
            continue
        if start_date and bill.get("date", "") < start_date:
            continue
        if end_date and bill.get("date", "") > end_date:
            continue
        if search_lower:
            # 搜索名称、备注、商户、分类
            searchable_text = " ".join([
                bill.get("name") or "",
                bill.get("note") or "",
                bill.get("merchant") or "",
                bill.get("category") or ""
            ]).lower()
            if search_lower not in searchable_text:
                continue
        result.append(bill)

    result.sort(key=lambda x: x.get("date", ""), reverse=True)
    total = len(result)

    if page > 0 and page_size > 0:
        start = (page - 1) * page_size
        items = result[start:start + page_size]
    else:
        items = result

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=BillModel)
def add_bill(bill: BillModel):
    bill_dict = bill.model_dump()
    bill_dict.pop("id", None)
    doc_id = db.insert(bill_dict)
    bill_dict["id"] = doc_id
    return bill_dict


@router.put("/{bill_id}", response_model=BillModel)
def update_bill(bill_id: int, bill: BillModel):
    if not db.get(doc_id=bill_id):
        raise HTTPException(status_code=404, detail="账单未找到")
    bill_dict = bill.model_dump()
    bill_dict.pop("id", None)
    db.update(bill_dict, doc_ids=[bill_id])
    bill_dict["id"] = bill_id
    return bill_dict


@router.delete("/{bill_id}")
def delete_bill(bill_id: int):
    if db.remove(doc_ids=[bill_id]):
        return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="账单未找到")


@router.post("/batch-delete")
def batch_delete_bills(ids: list[int]):
    """批量删除账单"""
    deleted = db.remove(doc_ids=ids)
    return {"message": f"成功删除 {deleted} 条账单", "deleted": deleted}


@router.delete("")
def clear_all_bills():
    db.truncate()
    return {"message": "所有账单已清空"}


@router.get("/stats")
def get_stats():
    bills = db.all()
    total_income = sum(b.get('amount', 0) for b in bills if b.get('amount', 0) > 0)
    total_expense = sum(abs(b.get('amount', 0)) for b in bills if b.get('amount', 0) < 0)

    category_stats = {}
    platform_stats = {}
    for bill in bills:
        amount = abs(bill.get('amount', 0))
        if bill.get('amount', 0) < 0:
            cat = bill.get('category', '其他')
            category_stats[cat] = category_stats.get(cat, 0) + amount
        plat = bill.get('platform', 'unknown')
        platform_stats[plat] = platform_stats.get(plat, 0) + 1

    return {
        "total_count": len(bills),
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
):
    result = []
    search_lower = (search or "").lower()

    for bill in db.all():
        if category and bill.get("category") != category:
            continue
        if platform and bill.get("platform") != platform:
            continue
        if start_date and bill.get("date", "") < start_date:
            continue
        if end_date and bill.get("date", "") > end_date:
            continue
        if search_lower:
            # 搜索名称、备注、商户、分类
            searchable_text = " ".join([
                bill.get("name") or "",
                bill.get("note") or "",
                bill.get("merchant") or "",
                bill.get("category") or ""
            ]).lower()
            if search_lower not in searchable_text:
                continue
        result.append(bill)

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
