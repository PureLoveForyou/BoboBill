from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from database import get_db, Bill, Budget, User
from auth import get_current_user, get_current_user_from_query

router = APIRouter(prefix="/backup", tags=["backup"])


@router.get("/export")
def export_database(db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_query)):
    """导出当前用户的所有数据为 JSON 文件"""
    bills = db.query(Bill).filter_by(user_id=current_user.id).all()
    budgets = db.query(Budget).filter_by(user_id=current_user.id).all()

    data = {
        "bills": [],
        "budgets": []
    }

    for b in bills:
        data["bills"].append({
            "id": b.id,
            "name": b.name,
            "amount": b.amount,
            "type": b.type,
            "date": b.date,
            "category": b.category,
            "platform": b.platform,
            "merchant": b.merchant,
            "note": b.note,
            "transaction_id": b.transaction_id,
        })

    for bg in budgets:
        data["budgets"].append({
            "user_id": bg.user_id,
            "monthly_total": bg.monthly_total,
            "category_budgets": bg.category_budgets,
        })

    filename = f"bobobill_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = f"database/{filename}"
    
    os.makedirs("database", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/json"
    )


@router.post("/import")
async def import_database(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """导入数据库文件（覆盖当前用户数据）"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="仅支持 JSON 格式文件")

    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))

        if isinstance(data, dict) and "bills" in data:
            # 新格式：SQLite 导出的结构化 JSON
            db.query(Bill).filter_by(user_id=current_user.id).delete(synchronize_session=False)
            db.query(Budget).filter_by(user_id=current_user.id).delete(synchronize_session=False)

            for bill_data in data.get("bills", []):
                new_bill = Bill(
                    name=bill_data.get("name", ""),
                    amount=float(bill_data.get("amount", 0)),
                    type=bill_data.get("type", "expense"),
                    date=bill_data.get("date", ""),
                    category=bill_data.get("category"),
                    platform=bill_data.get("platform"),
                    merchant=bill_data.get("merchant"),
                    note=bill_data.get("note"),
                    transaction_id=bill_data.get("transaction_id"),
                    user_id=current_user.id,
                )
                db.add(new_bill)

            for budget_data in data.get("budgets", []):
                budget = Budget(
                    user_id=current_user.id,
                    monthly_total=float(budget_data.get("monthly_total", 0)),
                    category_budgets=budget_data.get("category_budgets", "{}"),
                )
                db.add(budget)
            db.commit()
            
            bill_count = len(data.get("bills", []))
            return {"message": "数据库导入成功", "imported_bills": bill_count}

        raise HTTPException(status_code=400, detail="无效的数据库文件格式")

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的 JSON 文件")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
