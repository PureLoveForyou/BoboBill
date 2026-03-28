from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from models import ImportResult
from database import db
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
async def upload_bills(file: UploadFile = File(...), platform: str = Form(...)):
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

        # Deduplicate by transaction_id
        existing_ids = {b.get('transaction_id') for b in db.all() if b.get('transaction_id')}
        success_count = skipped_count = 0

        for bill in bills:
            if bill.get('transaction_id') and bill['transaction_id'] in existing_ids:
                skipped_count += 1
                continue
            db.insert(bill)
            success_count += 1

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
