# Cat Care System

> 面向多猫家庭的成长、健康、饮食与影像管理系统。它把日常记录、健康追踪、体重趋势、喂养方案和猫咪相册整合到一个可长期维护的本地 Web 工作台里。

![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)
![Vue](https://img.shields.io/badge/Vue-3.x-42b883)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178c6)
![SQLite](https://img.shields.io/badge/SQLite-local-003b57)
![Tests](https://img.shields.io/badge/tests-pytest%20%2B%20playwright-2f6fdd)

## 项目愿景

Cat Care System 不是一个简单的“猫咪体重表”，而是一套面向真实养猫场景的轻量健康中台。系统围绕每只猫的生命周期建立档案，把体重、病史、疫苗驱虫、饮食方案、换粮过程、补剂疗程、照片时间线等信息串起来，帮助多猫家庭持续记录、回看和决策。

当前项目以本地部署为主，适合家庭内网、个人 NAS、Mac/PC 常驻服务和后续云端化改造。

## 核心能力

### 猫咪档案

- 多猫资料管理：姓名、性别、品种、毛色、生日、绝育状态、头像
- 批量删除、搜索筛选、移动端友好的列表布局
- 体内/体外驱虫频率设置，为后续提醒能力预留数据基础

### 体重与健康趋势

- 体重记录增删改查
- ECharts 趋势图展示不同猫咪的成长变化
- Excel 模板下载、体重批量导入、导出归档

### 健康档案

- 支持疾病、疫苗、驱虫等健康事件记录
- 多猫同步创建与同步修改，适合疫苗、驱虫这类多猫同日处理场景
- 同步组机制保留“同一事件在不同猫身上的映射关系”

### 饮食记录

- 喂养方案：主粮、罐头、混合喂养、日摄入量、热量和饮水策略
- 每日喂食：实际吃了什么、吃了多少、是否拒食、是否软便或呕吐
- 换粮计划：内置 7 日、10 日和慢速换粮模板
- 补剂疗程：记录赖氨酸、化毛片、营养液等保健品使用周期
- 多猫同步：同一喂养方案、换粮计划、补剂疗程可批量同步到其他猫咪

### 如厕记录（规划中，暂未开发完成）

- 计划支持手动记录排尿、排便、猫砂盆使用次数和异常情况
- 计划沉淀如厕频次、持续时间、体重联动和异常趋势分析
- 后续可探索智能猫厕设备数据同步，把抓拍、事件和统计数据汇入同一健康时间线
- 当前仅作为产品路线规划展示，尚未进入主流程开发

### 照片与相册

- 单猫相册和全局照片墙
- 合照支持多猫标注，一张照片可出现在多只猫详情页
- 缩略图生成、EXIF 拍摄时间读取、重复/相似照片提示
- 手动排序、置顶、预览弹窗，方便整理长期影像资产

### 工程化与测试

- FastAPI 后端模块化路由
- Vue 3 + TypeScript 前端工程
- Pytest 覆盖饮食记录、批量操作、搜索等接口行为
- Playwright 覆盖饮食记录关键 UI 流程

## 技术架构

```text
cat-care-system/
├── backend/
│   ├── main.py                 # FastAPI 应用入口与 SQLite 兼容迁移
│   ├── database.py             # SQLAlchemy 数据库连接
│   ├── models.py               # ORM 数据模型
│   ├── schemas.py              # Pydantic 请求与响应模型
│   ├── photo_utils.py          # 缩略图、EXIF、感知哈希工具
│   ├── routers/                # 认证、猫咪、体重、健康、照片、饮食 API
│   └── tests/                  # Pytest 接口测试
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios API 封装
│   │   ├── components/         # 复用业务组件
│   │   ├── utils/              # 前端排序等工具函数
│   │   └── views/              # 登录、仪表盘、猫咪详情页
│   ├── tests/                  # Playwright UI 测试
│   └── package.json
└── docs/                       # 需求、接口设计和迭代文档
```

后端使用 FastAPI、SQLAlchemy、SQLite、Pydantic、JWT、Pillow、Pandas、OpenPyXL。前端使用 Vue 3、TypeScript、Element Plus、ECharts、Pinia、Vue Router、Vite。

## 快速开始

### 1. 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端 API 地址：

- 本机访问：http://127.0.0.1:8000
- Swagger 文档：http://127.0.0.1:8000/docs

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：

- 本机访问：http://127.0.0.1:3003/dashboard
- 局域网访问：http://你的电脑局域网IP:3003/dashboard

### 3. 测试账号

初始化数据会创建一个演示账号：

```text
用户名：demo
密码：123456
```

## 测试与验证

后端接口测试：

```bash
cd backend
pytest tests -q
```

前端类型检查与生产构建：

```bash
cd frontend
npm run build
```

UI 自动化测试需要先启动后端和前端：

```bash
cd frontend
npm run test:ui -- --reporter=line
```

## 数据与隐私

本项目默认使用 SQLite，本地数据库、上传照片、缩略图、设备日志、测试结果和第三方同步实验产物不会提交到 Git。公开 GitHub 仓库只保留代码、测试、产品文档和必要的示例结构，避免误传家庭照片、会话 token 或真实设备日志。

## 路线图

- 家庭内网长期运行方案和一键启动脚本
- 如厕记录：手动录入、趋势统计、智能猫厕数据同步（暂未开发完成）
- 健康提醒：驱虫、疫苗、复诊、换粮观察周期
- 更完整的数据备份与恢复
- 移动端 PWA 优化
- 多设备同步与云端部署方案

## 适用场景

- 多猫家庭需要长期维护健康与饮食记录
- 需要把体重、健康、照片和喂养信息集中管理
- 想在本地先跑通完整产品，再逐步升级到云端或移动端
