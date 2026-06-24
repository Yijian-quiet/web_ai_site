# 不颓废的小健 - 个人 AI 网站

> 产品版本: v3.1 | 最后更新: 2026-06-15

## 一句话描述
张一健（Mr.自由基）的个人 AI 网站，集成博客、AI 聊天助手、后台管理三合一的暗色科技风个人站

## 目标用户
- **主要**: 张一健本人（管理员），管理内容和查看数据
- **次要**: 实验室同学、朋友、访客，浏览博客、项目和 AI 聊天

## 核心功能
1. 📝 **博客系统** — Markdown 文章发布、分类、阅读统计（管理后台操作）
2. 🤖 **AI 聊天** — DeepSeek 驱动的对话助手，支持流式回复
3. 🏠 **个人主页** — 首页 / 关于 / 项目 / 发表 / 工具页面，JSON 数据驱动
4. ⚙️ **管理后台** — Flask 后台，文章/用户/会话管理
5. 🔐 **用户系统** — 注册/登录、密码重置（QQ邮箱）、登录限流

## 页面结构
| 路由 | 功能 | 数据来源 |
|:----|:----|:--------:|
| `/` | 首页 — 个人信息卡片 | `data/profile.json` |
| `/about` | 关于我 — 简介 + 时间线 | `data/profile.json` + `timeline.json` |
| `/projects` | 项目展示 | `data/projects.json` |
| `/publications` | 发表论文 | `data/publications.json` |
| `/tools` | 工具/平台列表 | `data/tools.json` |
| `/blog` | 博客文章列表 | MySQL |
| `/chat` | AI 聊天（跳转到 Streamlit） | — |
| `/m` | 手机版聊天 | Flask API |
| `/admin/...` | 管理后台（需登录） | MySQL + JSON |

## 技术架构
- **前端**: Streamlit（AI 聊天 + 部分后台），Flask + Jinja2（个人站 + 管理后台）
- **样式**: 暗色科技风 Glassmorphism（渐变背景 + 毛玻璃效果）
- **AI**: DeepSeek API（deepseek-chat 模型），BGE 语义嵌入 RAG 检索
- **数据库**: MySQL 8.0（Docker 容器）
- **通信**: QQ邮箱 SMTP（密码找回）
- **部署**: Docker Compose + Nginx 反代

## 设计风格
- 紫色品牌色 (#6C63FF) + 深色渐变 (#0B0D1A → #1A1040)
- Glassmorphism 毛玻璃卡片、圆角、柔和阴影
- Poetsen One 字体（导航栏）
- 全站暗色主题，前后端风格统一

## 成功指标
- [x] 网站可公开访问（http://your-domain.com）
- [x] 博客文章可正常显示
- [x] AI 聊天可正常对话
- [x] 管理后台可登录管理
- [x] 全站暗色科技风重构完成
- [x] 个人主页 JSON 数据驱动（内容即时可改）
- [ ] HTTPS 配置完成
- [ ] 手机版完善
