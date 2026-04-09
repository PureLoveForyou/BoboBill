from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.bills import router as bills_router
from routers.upload import router as upload_router
from routers.backup import router as backup_router
from routers.budget import router as budget_router
from routers.auth import router as auth_router
from routers.ai import router as ai_router

app = FastAPI(title="BoboBill API", description="智能账单管理助手", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bills_router)
app.include_router(upload_router)
app.include_router(backup_router)
app.include_router(budget_router)
app.include_router(auth_router)
app.include_router(ai_router)


@app.get("/")
def read_root():
    return {"message": "欢迎使用 BoboBill API! 访问 /docs 查看文档", "version": "0.3.0", "db": "sqlite"}
