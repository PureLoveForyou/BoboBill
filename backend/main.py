from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from tinydb import TinyDB, Query
import os

# 初始化数据库（数据会保存在 db.json 中）
if not os.path.exists("db.json"):
    open("db.json", "w").close()

db = TinyDB("db.json")
Bill = Query()

app = FastAPI(
    title="Bill Assistant",
    description="账单管理助手",
    version="0.1.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Vite 默认开发地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== 数据模型 ==================
class BillModel(BaseModel):
    id: Optional[int] = None
    name: str
    amount: float
    type: str # income 或 expense
    date: str # 格式：YYYY-MM-DD

# ================== API 接口 ==================
# 获取所有账单
@app.get("/bills", response_model=List[BillModel])
def get_bills():
    bills = db.all()
    for bill in bills:
        # TinyDB 的每条记录自带 `doc_id`，我们把它作为 id
        bill["id"] = bill.doc_id
    return bills

# 添加账单
@app.post("/bills", response_model=BillModel)
def add_bill(bill: BillModel):
    bill_dict = bill.model_dump()
    # 删除前端传来的 id（如果有），让数据库生成
    bill_dict.pop("id", None)
    # 写入数据库，返回自动生成的 doc_id
    doc_id = db.insert(bill_dict)
    bill_dict["id"] = doc_id
    return bill_dict

# 删除账单
@app.delete("/bills/{bill_id}")
def delete_bill(bill_id: int):
    if db.remove(doc_ids=[bill_id]):
        return {"message": "删除成功"}
    else:
        raise HTTPException(status_code=404, detail="账单未找到")
    
# 根路径提示
@app.get("/")
def read_root():
    return {"message": "欢迎使用账单管理API!访问 /docs 查看文档"}