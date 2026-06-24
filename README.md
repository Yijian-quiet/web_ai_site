# Personality AI · Personal Website Template

> 个人 AI 网站模板 —— 暗色科技风，Flask + Streamlit + MySQL
> 
> 基于 Mr.自由基 的个人网站，开源供大家使用。

## 功能

- 🏠 个人主页（项目/发表/工具展示）
- 📝 博客系统（Markdown）
- 🤖 AI 聊天（DeepSeek API，需自备 Key）
- 🔐 用户注册/登录/邮箱验证
- 🧬 分子结构渲染
- ⚙️ 管理后台
- 📱 手机版适配

## 快速上手

### 1. 配置环境变量

```bash
cp personality_AI/.env.example personality_AI/.env
```

编辑 `personality_AI/.env`，填入你自己的配置。

### 2. 启动服务

```bash
docker compose up -d
```

### 3. 访问

打开 http://localhost 即可看到网站。

## 自定义你的网站

编辑 `admin_backend/data/` 下的 JSON 文件：

| 文件 | 内容 |
|:----|:------|
| `profile.json` | 个人信息、教育经历 |
| `projects.json` | 项目展示 |
| `publications.json` | 发表论文 |
| `tools.json` | 工具列表 |
| `timeline.json` | 时间线 |

修改后重启容器即可生效：

```bash
docker restart web_ai_flask
```

## 技术栈

| 组件 | 技术 |
|:----|:-----|
| 前端 | Streamlit + Jinja2 (Flask) |
| 后端 | Flask 3.1 |
| 数据库 | MySQL 8.0 |
| AI | DeepSeek API |
| 容器 | Docker Compose |
| 反向代理 | Nginx |

## License

MIT
