from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse, JSONResponse
import shutil
import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from database import get_db, Bill, Budget

router = APIRouter(prefix="/backup", tags=["backup"])


@router.get("/export")
def export_database(db: Session = Depends(get_db)):
    """导出所有数据为 JSON 文件"""
    bills = db.query(Bill).all()
    budgets = db.query(Budget).all()

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

    # 写入临时文件供下载
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
async def import_database(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """导入数据库文件（覆盖现有数据）"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="仅支持 JSON 格式文件")

    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))

        # 验证数据结构（兼容新旧格式）
        if isinstance(data, dict):
            if "bills" in data and "budgets" in data:
                # 新格式：SQLite 导出的结构化 JSON
                # 清空现有数据
                db.query(Bill).delete(synchronize_session=False)
                db.query(Budget).delete(synchronize_session=False)

                # 导入账单
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
                    )
                    db.add(new_bill)

                # 导入预算
                for budget_data in data.get("budgets", []):
                    existing = db.query(Budget).filter_by(user_id=budget_data.get("user_id", 1)).first()
                    if not existing:
                        budget = Budget(
                            user_id=budget_data.get("user_id", 1),
                            monthly_total=float(budget_data.get("monthly_total", 0)),
                            category_budgets=budget_data.get("category_budgets", "{}"),
                        )
                        db.add(budget)
                db.commit()
                
                bill_count = len(data.get("bills", []))
                return {"message": "数据库导入成功", "imported_bills": bill_count}
            
            elif len(data) > 0:
                # 旧格式：TinyDB 的文档列表（兼容旧备份文件）
                # 尝试迁移旧格式数据
                from database import init_db as ensure_tables
                ensure_tables()
                
                imported = 0
                for doc in data:
                    doc_type = doc.get("type")
                    
                    if doc_type == "budget":
                        existing = db.query(Budget).filter_by(user_id=1).first()
                        if not existing:
                            budget = Budget(
                                user_id=1,
                                monthly_total=doc.get("monthly_total", 0),
                                category_budgets=json.dumps(doc.get("category_budgets", {}), ensure_ascii=False),
                            )
                            db.add(budget)
                        else:
                            existing.monthly_total = doc.get("monthly_total", 0)
                            existing.category_budgets = json.dumps(doc.get("category_budgets", {}), ensure_ascii=False)
                    else:
                        new_bill = Bill(
                            name=doc.get("name", ""),
                            amount=float(doc.get("amount", 0)),
                            type=doc.get("type", "expense"),
                            date=doc.get("date", ""),
                            category=doc.get("category"),
                            platform=doc.get("platform"),
                            merchant=doc.get("merchant"),
                            note=doc.get("note"),
                            transaction_id=doc.get("transaction_id"),
                        )
                        db.add(new_bill)
                        imported += 1
                
                db.commit()
                return {"message": f"数据库导入成功（旧格式兼容），共 {imported} 条账单"}

        raise HTTPException(status_code=400, detail="无效的数据库文件格式")

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的 JSON 文件")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
