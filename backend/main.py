from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.bills import router as bills_router
from routers.upload import router as upload_router

app = FastAPI(title="BoboBill API", description="智能账单管理助手", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bills_router)
app.include_router(upload_router)


@app.get("/")
def read_root():
    return {"message": "欢迎使用 BoboBill API! 访问 /docs 查看文档"}
