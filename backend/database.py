import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "sqlite:///./database/bobobill.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String(20), nullable=False)
    date = Column(String(10), nullable=False)
    category = Column(String(50), nullable=True, default=None)
    platform = Column(String(30), nullable=True, default=None)
    merchant = Column(String(200), nullable=True, default=None)
    note = Column(Text, nullable=True, default=None)
    transaction_id = Column(String(100), nullable=True, unique=True, default=None)
    user_id = Column(Integer, default=1)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, default=1, unique=True)
    monthly_total = Column(Float, default=0)
    category_budgets = Column(Text, default="{}")


def init_db():
    """初始化数据库，创建所有表"""
    os.makedirs("database", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 依赖注入用的数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_from_json(json_path: str = "database/db.json"):
    """从旧 TinyDB JSON 文件迁移数据到 SQLite"""
    if not os.path.exists(json_path):
        print(f"旧数据库文件不存在，跳过迁移: {json_path}")
        return 0

    import json
    from tinydb import TinyDB

    try:
        tiny_db = TinyDB(json_path)
        docs = tiny_db.all()
        if not docs:
            print("旧数据库为空")
            return 0

        session = SessionLocal()
        migrated_bills = 0

        for doc in docs:
            doc_type = doc.get("type")

            if doc_type == "budget":
                existing = session.query(Budget).filter_by(user_id=1).first()
                if not existing:
                    budget = Budget(
                        user_id=1,
                        monthly_total=doc.get("monthly_total", 0),
                        category_budgets=json.dumps(doc.get("category_budgets", {}), ensure_ascii=False),
                    )
                    session.add(budget)
                else:
                    existing.monthly_total = doc.get("monthly_total", 0)
                    existing.category_budgets = json.dumps(doc.get("category_budgets", {}), ensure_ascii=False)
            else:
                bill = Bill(
                    name=doc.get("name", ""),
                    amount=float(doc.get("amount", 0)),
                    type=doc.get("type", "expense"),
                    date=doc.get("date", ""),
                    category=doc.get("category"),
                    platform=doc.get("platform"),
                    merchant=doc.get("merchant"),
                    note=doc.get("note"),
                    transaction_id=doc.get("transaction_id"),
                    user_id=1,
                )
                session.add(bill)
                migrated_bills += 1

        session.commit()
        session.close()
        print(f"迁移完成: {migrated_bills} 条账单, 预算配置已导入")
        return migrated_bills

    except Exception as e:
        print(f"迁移失败: {e}")
        return 0


# 初始化（模块加载时执行）
init_db()
