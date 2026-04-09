from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from models import ImportResult
from database import get_db, Bill, User
from auth import get_current_user
from parsers.base import detect_platform, decode_content
from parsers.wechat import parse_wechat_csv, parse_wechat_excel
from parsers.alipay import parse_alipay_csv, parse_alipay_excel

router = APIRouter(prefix="/bills", tags=["upload"])

PARSER_MAP = {
    'wechat': (parse_wechat_csv, parse_wechat_excel),
    'alipay': (parse_alipay_csv, parse_alipay_excel),
}

PLATFORM_NAMES = {'wechat': '微信', 'alipay': '支付宝', 'bank': '银行卡'}


@router.post("/detect")
async def detect_bill_platform(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="仅支持 CSV、Excel 格式文件")
    content = await file.read()
    return {"platform": detect_platform(content, file.filename), "filename": file.filename}


@router.post("/upload", response_model=ImportResult)
async def upload_bills(
    file: UploadFile = File(...),
    platform: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if platform not in ['wechat', 'alipay', 'bank']:
        raise HTTPException(status_code=400, detail="不支持的平台类型")
    if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="仅支持 CSV、Excel 格式文件")

    try:
        content = await file.read()
        detected = detect_platform(content, file.filename)
        actual_platform = detected if detected != 'unknown' else platform
        auto_corrected = detected != 'unknown' and detected != platform
        is_excel = file.filename.lower().endswith(('.xlsx', '.xls'))

        if actual_platform not in PARSER_MAP:
            raise HTTPException(status_code=400, detail=f"{actual_platform} 解析器暂未实现")

        csv_parser, excel_parser = PARSER_MAP[actual_platform]
        bills = excel_parser(content) if is_excel else csv_parser(decode_content(content))

        if not bills:
            return ImportResult(success=0, skipped=0, total=0, message="未解析到有效账单数据")

        existing_txns = db.query(Bill.transaction_id).filter(
            Bill.user_id == current_user.id,
            Bill.transaction_id != None,
            Bill.transaction_id != ""
        ).all()
        existing_ids = {t[0] for t in existing_txns}

        success_count = skipped_count = 0

        for bill_data in bills:
            if bill_data.get('transaction_id') and bill_data['transaction_id'] in existing_ids:
                skipped_count += 1
                continue
            
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
            success_count += 1

        db.commit()

        message = f"成功导入 {success_count} 条{PLATFORM_NAMES.get(actual_platform, actual_platform)}账单"
        if auto_corrected:
            message += "（已自动识别平台）"
        if skipped_count > 0:
            message += f"，跳过 {skipped_count} 条重复记录"

        return ImportResult(success=success_count, skipped=skipped_count, total=len(bills), message=message)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
