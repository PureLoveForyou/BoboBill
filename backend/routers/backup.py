from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import json
from datetime import datetime

router = APIRouter(prefix="/backup", tags=["backup"])


@router.get("/export")
def export_database():
    """导出数据库文件"""
    return FileResponse(
        path="database/db.json",
        filename=f"bobobill_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        media_type="application/json"
    )


@router.post("/import")
async def import_database(file: UploadFile = File(...)):
    """导入数据库文件（覆盖现有数据）"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="仅支持 JSON 格式文件")

    try:
        # 验证 JSON 格式
        content = await file.read()
        data = json.loads(content.decode('utf-8'))

        # 验证数据结构（简单检查）
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="无效的数据库文件格式")

        # 备份当前数据库
        backup_name = f"database/db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy("database/db.json", backup_name)

        # 写入新数据
        with open("database/db.json", "wb") as f:
            f.write(content)

        return {"message": "数据库导入成功", "auto_backup": backup_name}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的 JSON 文件")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
