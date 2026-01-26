# 📝 账单管理器

移动支付时代，最好的记账方式是不记账！智能账单助手，旨在整合微信/支付宝/银行账单，解放记账。
一个个人账单管理系统，前端使用 Vue 3 + Vite，后端使用 FastAPI + Python，数据存储使用 TinyDB。

# 🚀 快速启动

## 启动后端

```bash
cd backend

# 创建并激活虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --port 8000

# Windows启动服务
venv\Scripts\uvicorn.exe main:app --reload 
```

## 启动前端

```bash
# 打开另一个终端，回到项目根目录
cd frontend/vue-project

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 启动正式服务器
npm run serve
```


## 项目结构
```
bill-app/
├── backend/           # FastAPI 后端
│   ├── main.py        # API 接口
│   ├── requirements.txt # Python 依赖
│   └── db.json        # 账单数据存储（自动创建）
├── frontend/          # Vue 前端
│   ├── src/
│   │   └── App.vue    # 主页面
│   └── package.json
└── README.md
```