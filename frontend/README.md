# 图书管理系统 — 前端

基于 **Vue 3（Composition API + TypeScript）+ Vite 5 + Pinia + Vue Router + Element Plus + ECharts** 的图书管理系统前端，界面遵循项目根目录 `DESIGN.md` 的 Apple 风格设计规范（单一强调色 #0066cc、胶囊按钮、白色/羊皮纸画布交替、极简阴影）。

## 环境要求

- Node.js 18+
- npm

## 快速启动

```bash
cd frontend
npm install
npm run dev
```

开发服务器运行在 `http://localhost:5173/`。

> 前置条件：后端服务需先在 `http://127.0.0.1:8000` 启动（参见 `backend/README.md`）。
> Vite 已配置代理，`/api` 与 `/uploads` 请求会自动转发到后端，无需额外配置跨域。

## 测试账号

登录页提供一键填入的测试账号，也可手动输入：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `admin123` |
| 普通用户 | `user` | `user123` |
| VIP 用户 | `vip` | `vip123` |

## 功能页面

| 页面 | 路由 | 说明 |
| --- | --- | --- |
| 图书检索 | `/` | 关键词（书名/作者/ISBN）搜索、分类芯片、标签与在馆状态筛选、分页图书卡片（封面/星级评分） |
| 图书详情 | `/books/:id` | 图书信息、平均评分、立即借阅、评分评论（星级 + 字数校验）、评论列表 |
| 登录 / 注册 | `/login`、`/register` | JWT 登录、注册即自动登录 |
| 我的借阅 | `/my/borrows` | 在借/逾期/已还汇总，申请归还，查看预计归还日期与催还提醒 |
| 消息中心 | `/messages` | 全局消息 + 个人催还通知，未读/已读状态，一键全部已读 |
| 个人中心 | `/profile` | 修改昵称/邮箱/手机号/头像（webp/png/jpeg，≤100K），用户名只读 |
| 管理后台 | `/admin/*` | 仪表盘（借阅趋势按天/周/月）、图书管理（增删改查 + 封面上传）、分类管理、借阅管理（催还、归还确认）、用户管理（角色/禁用/删除）、消息发布 |

## 会话管理（AccessToken 自动刷新）

`src/api/client.ts` 中的 axios 响应拦截器实现了自动续期：

1. 任意 API 请求返回 401 时，自动使用 RefreshToken 调用 `POST /api/auth/refresh`；
2. 换取新的双 Token 后自动重放原请求（并发请求共享同一次刷新，避免风暴）；
3. 刷新失败（RefreshToken 也过期）则清除本地会话并跳转登录页。

Token 与用户信息持久化在 `localStorage`，刷新页面后保持登录态。

## 设计规范落地

`src/styles/main.css` 将 `DESIGN.md` 的设计令牌映射为 CSS 变量，并桥接到 Element Plus 主题：

- 颜色：Action Blue `#0066cc`（唯一交互色）、墨色 `#1d1d1f`、羊皮纸 `#f5f5f7`、细边界 `#e0e0e0`；
- 排版：SF Pro 字体栈、正文 17px、标题负字距（-0.28 ~ -0.374px）、字重阶梯 300/400/600；
- 组件：主操作为胶囊按钮（按下 `scale(0.95)` 微交互）、卡片 18px 圆角 + 细边界无阴影、黑色全局导航 44px + 磨砂次级导航 52px；
- 星级评分组件（`StarDisplay.vue`）使用 Action Blue 填充星，支持半星精度平均值展示。

## 目录结构

```
frontend/
├── index.html
├── vite.config.ts          # 端口 5173，/api 与 /uploads 代理到后端
└── src/
    ├── main.ts             # 应用入口（Element Plus + 中文语言包）
    ├── App.vue
    ├── router/             # 路由与登录/管理员守卫
    ├── stores/             # Pinia：auth（Token、用户、未读数）
    ├── api/                # axios 封装（自动刷新）+ 类型化 API 模块
    ├── types/              # TypeScript 类型定义
    ├── styles/main.css     # 设计令牌 + Element Plus 主题定制
    ├── components/         # GlobalNav / SubNav / BookCard / CoverImage / StarDisplay
    ├── layouts/            # AppLayout（用户端）/ AdminLayout（后台）
    └── views/              # 页面（含 admin/ 六个管理页面）
```

## 构建与预览

```bash
npm run build     # 产物输出到 dist/
npm run preview   # 本地预览构建产物
```
