# 图书管理系统 — 后端服务

基于 **FastAPI + SQLAlchemy + SQLite** 的图书管理系统后端，提供 JWT 双 Token 认证、图书/分类管理、借阅归还、评分评论、消息中心与统计等完整 API。依赖与环境使用 **uv** 统一管理。

## 环境要求

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)（Python 包与环境管理器）

## 快速启动

```bash
cd backend
uv sync            # 创建 .venv 并安装全部依赖（依据 uv.lock）
uv run python run.py
```

服务默认运行在 `http://127.0.0.1:8000`，交互式 API 文档见 `http://127.0.0.1:8000/docs`。

首次启动时会自动：

1. 创建 SQLite 数据库 `backend/data/library.db`；
2. 创建 `backend/uploads/` 目录（头像 / 封面存储）；
3. 写入演示数据（18 本图书、6 个分类、3 个测试账号、约 170 条借阅历史、评论与系统消息）。

依赖变更时使用 `uv add <包名>` 或 `uv remove <包名>`，`uv.lock` 会同步更新并纳入版本管理。

## 测试账号

| 角色 | 用户名 | 密码 | 说明 |
| --- | --- | --- | --- |
| 管理员 | `admin` | `admin123` | 可访问管理后台全部功能 |
| 普通用户 | `user` | `user123` | 在借上限 5 册 |
| VIP 用户 | `vip` | `vip123` | 在借上限 10 册 |

## 业务规则

- **认证**：登录/注册返回 `accessToken`（30 分钟）与 `refreshToken`（7 天）；AccessToken 过期后调用 `POST /api/auth/refresh` 换取新 Token（前端已实现自动续期）。
- **借阅**：借期 14 天；同一本书未归还前不能重复借阅；普通用户/VIP/管理员在借上限分别为 5/10/20 册。
- **归还**：用户提交归还申请（状态 `returning`），管理员确认后状态置为 `returned` 并恢复在馆数量。
- **催还**：管理员可对未归还记录执行催还，系统自动向该用户发送个人消息。
- **评分评论**：评分 0-5 分可选（默认 0），评论必填且必须大于 5 个字；同一用户可多次评价，图书最终评分为平均值。
- **头像**：仅支持 webp / png / jpeg，大小不超过 100K；图书封面不超过 2M。

## 配置（环境变量）

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `SECRET_KEY` | 内置开发密钥 | JWT 签名密钥，生产环境务必修改 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | AccessToken 有效期（分钟） |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | RefreshToken 有效期（天） |

## API 一览（前缀 `/api`）

| 模块 | 接口 |
| --- | --- |
| 认证 | `POST /auth/register`、`POST /auth/login`、`POST /auth/refresh`、`GET /auth/me` |
| 图书 | `GET /books`（关键词/分类/状态/标签筛选与分页）、`GET /books/{id}`、`GET /books/tags`、`POST/PUT/DELETE /books`（管理员）、`POST /books/{id}/cover`（管理员） |
| 分类 | `GET /categories`、`POST/PUT/DELETE /categories/{id}`（管理员） |
| 评论 | `GET/POST /books/{id}/reviews`、`DELETE /reviews/{id}` |
| 借阅 | `POST /borrows`、`GET /borrows/my`、`GET /borrows/my/summary`、`GET /borrows`（管理员）、`POST /borrows/{id}/return`、`POST /borrows/{id}/confirm-return`（管理员）、`POST /borrows/{id}/remind`（管理员） |
| 消息 | `GET /messages`、`GET /messages/unread-count`、`POST /messages/{id}/read`、`POST /messages/read-all`、`GET /messages/admin/list`、`POST/DELETE /messages`（管理员） |
| 个人中心 | `PUT /profile`、`POST /profile/avatar` |
| 统计 | `GET /stats/overview`、`GET /stats/borrow-trend?granularity=day|week|month`（管理员） |
| 用户管理 | `GET /users`、`PUT /users/{id}/role`、`PUT /users/{id}/status`、`DELETE /users/{id}`（管理员） |

## 目录结构

```
backend/
├── pyproject.toml         # 项目依赖声明（uv 管理）
├── uv.lock                # 锁定的依赖版本
├── run.py                 # 启动入口（uvicorn，支持热重载）
├── smoke_test.py          # API 冒烟测试（66 项断言）
├── data/                  # SQLite 数据库（运行时生成）
├── uploads/               # 头像与封面上传目录（运行时生成）
└── app/
    ├── main.py            # FastAPI 应用与生命周期
    ├── core/              # 配置、JWT/密码、依赖注入
    ├── db/                # 数据库连接与种子数据
    ├── models/            # SQLAlchemy 模型
    ├── schemas/           # Pydantic 请求/响应模型
    └── api/               # 路由（auth/books/borrows/...）
```

## 运行冒烟测试

后端启动后执行：

```bash
uv run python smoke_test.py
```

覆盖认证、权限、图书检索筛选、评论校验、借阅全流程、消息已读、统计趋势等 66 项断言。

## 重置演示数据

删除运行时目录后重启服务即可重新生成种子数据：

```bash
rm -rf data uploads && uv run python run.py
```
