# 猫咪成长健康管理系统 MVP

一个用于记录和追踪猫咪成长体重的前后端分离应用。

## 项目结构

```
cat-care-system/
├── backend/                 # FastAPI 后端
│   ├── main.py             # 应用入口
│   ├── database.py         # 数据库配置
│   ├── models.py           # 数据模型
│   ├── schemas.py          # Pydantic 模型
│   ├── init_data.py        # 初始数据
│   ├── requirements.txt    # Python 依赖
│   └── routers/
│       ├── auth.py         # 认证路由
│       ├── cats.py         # 猫咪管理路由
│       └── weights.py      # 体重记录路由
└── frontend/               # Vue 3 前端
    ├── src/
    │   ├── views/          # 页面组件
    │   │   ├── Login.vue
    │   │   ├── Register.vue
    │   │   ├── Dashboard.vue
    │   │   └── CatDetail.vue
    │   ├── stores/         # Pinia 状态管理
    │   ├── router/         # Vue Router
    │   ├── api/            # Axios API
    │   └── assets/         # 样式文件
    └── package.json
```

## 技术栈

### 后端
- FastAPI
- SQLAlchemy (SQLite)
- Pydantic
- JWT 认证

### 前端
- Vue 3 + TypeScript
- Element Plus
- ECharts
- Pinia
- Vue Router

## 快速开始

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 启动后端服务

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. 启动前端服务

```bash
cd frontend
npm run dev
```

### 5. 访问应用

打开浏览器访问 http://localhost:5173

## 测试账号

初始数据已自动创建测试账号：
- 用户名：demo
- 密码：123456

该账号包含两只测试猫咪和多条体重记录。

## 功能

- 用户注册/登录
- 猫咪信息管理（添加、编辑、删除）
- 体重记录管理
- 体重趋势图表展示
