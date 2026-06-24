# 工作跟踪

> 最后更新: 2026-06-17

## 🟢 已完成

| 日期 | 任务 | 说明 |
|:----|:----|:-----|
| 2026-05-29 | Docker 化部署 | 3 个容器（Streamlit+Flask+MySQL） |
| 2026-05-29 | 登录限流 | 密码错误 3 次锁定 15 分钟 |
| 2026-05-29 | API 切换 | Qwen → DeepSeek |
| 2026-05-29 | Nginx 反代 + 日志 | 统一入口 80 端口 |
| 2026-05-29 | 邮箱验证 | QQ SMTP 密码找回 |
| 2026-06-01 | 博客系统 | Flask + Markdown |
| 2026-06-01 | 数据备份 | 每日凌晨 3 点 |
| 2026-06-08 | 前端设计指南 | Anthropic frontend-design skill |
| 2026-06-08 | 项目文档 | context-driven-development |
| 2026-06-13 | 全站暗色科技风重构 | Glassmorphism + 个人主页页面（首页/关于/项目/发表/工具） |
| 2026-06-13 | JSON 数据驱动 | 个人站内容改为 JSON 文件驱动，修改即生效 |
| 2026-06-13 | BGE 语义 RAG | FastEmbed + BGE small 嵌入，博客全文检索 |
| 2026-06-15 | data 目录卷挂载 | `admin_backend/data/` 挂载为 Docker 卷，JSON 编辑后重启即生效 |
| 2026-06-16 | 注册异常处理 | SMTP 发信失败不崩页面 |
| 2026-06-16 | AI 人格设定 | 添加 system prompt 设定为不颓废的小健 |
| 2026-06-16 | 逆合成引擎修复 | 修复 UnboundLocalError(json) |
| 2026-06-16 | 分子图内联渲染 | SMILES 高亮 + 80px SVG 缩略图，悬停显示 |
| 2026-06-17 | Git 管理 | commit + push 到 GitHub redesign-v2 分支 |
| 2026-06-17 | docs/ 清理 | 删除 superpowers 生成的旧规划文件，保留 context/ |
| 2026-06-17 | 分子图 PNG 内联渲染 | 改为 PNG data URL，SMILES 紫色高亮+缩略图稳定显示 |

## 🟡 进行中

| 任务 | 状态 | 说明 |
|:----|:----|:-----|
| 分子图渲染 | 🟡 调试中 | st.markdown 过滤 SVG/PNG data URL，改 HTTP 直链 |
| 移动端适配 | 🔴 待启动 | 手机端 CSS 修复 |
| 内容补充 | 🟢 完成 | 已从简历 PDF 提取 |

## 🔴 待办

| 优先级 | 任务 | 说明 |
|:------|:----|:-----|
| 🔴 高 | ICP 备案 | 6/19 域名满3天，提交备案 |
| 🔴 高 | HTTPS | 备案通过后配免费 SSL |
| 🟡 中 | Docker 镜像持久化 | 确保密码/配置更新的持久化 |
| 🟢 低 | CI/CD | 自动部署流程 |
| 🟢 低 | 注册验证码 | 防机器人 |
