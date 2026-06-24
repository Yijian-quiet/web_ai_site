# 🧬 Personality AI · 个人 AI 网站框架

> 一个开箱即用的个人 AI 网站框架。  
> 暗色科技风 · Flask + Streamlit + MySQL · DeepSeek AI 驱动  
> 数据驱动配置，改 JSON 即改内容，无需改代码。

---

## ✨ 功能

| 模块 | 功能 |
|:----|:------|
| 🏠 **个人主页** | 首页 / 关于 / 项目 / 发表 / 工具，JSON 数据驱动 |
| 📝 **博客系统** | Markdown 文章发布、分类、阅读统计 |
| 🤖 **AI 聊天** | DeepSeek API 驱动，流式回复 + 分子结构渲染 |
| 🔐 **用户系统** | 注册 / 登录 / 邮箱验证 / 密码找回 |
| ⚙️ **管理后台** | 文章管理、用户管理、对话历史 |
| 🧬 **分子渲染** | SMILES 自动识别 + 结构图内联展示 |
| 📱 **手机适配** | 独立手机版聊天界面 |

---

## 🚀 5 分钟启动

### 前置

- Docker & Docker Compose
- DeepSeek API Key（[免费申请](https://platform.deepseek.com/)）

### 启动

```bash
git clone https://github.com/Yijian-quiet/web_ai_site.git
cd web_ai_site

cp personality_AI/.env.example personality_AI/.env
# 编辑 .env 填入你的 API Key 和数据库密码

docker compose up -d
```

打开 http://localhost 即可使用。

---

## 📋 信息配置卡

> 只需填写以下信息，替换 `admin_backend/data/` 下对应 JSON 文件即可完成网站内容定制。

### 🔵 基本信息

```json
{
  "name": "你的名字",
  "alias": "你的昵称",
  "title": "你的头衔",
  "subtitle": "简短介绍",
  "bio": "个人简介（1-2句话）",
  "location": "城市",
  "email": "your@email.com",
  "avatar": "/static/avatar.png"
}
```

**对应文件：** `admin_backend/data/profile.json`

---

### 🔵 教育经历

```json
[
  {
    "degree": "硕士",
    "school": "学校名称",
    "major": "专业",
    "period": "2023-2026",
    "note": "备注（可选）"
  },
  {
    "degree": "本科",
    "school": "学校名称",
    "major": "专业",
    "period": "2019-2023",
    "note": "GPA / 荣誉"
  }
]
```

**对应文件：** `admin_backend/data/profile.json`（education 字段）

---

### 🔵 首页亮点

```json
[
  {"icon": "bi-trophy", "label": "标签1", "value": "数值1"},
  {"icon": "bi-file-text", "label": "标签2", "value": "数值2"},
  {"icon": "bi-chat-dots", "label": "标签3", "value": "在线"}
]
```

> `icon` 使用 [Bootstrap Icons](https://icons.getbootstrap.com/) 图标名。  
> **对应文件：** `admin_backend/data/profile.json`（highlights 字段）

---

### 🔵 项目展示

每项：

```json
{
  "id": "project-id",
  "name": "项目名",
  "full_name": "完整名称",
  "status": "active / completed",
  "description": "项目描述（2-3句话）",
  "tech": ["Python", "PyTorch"],
  "highlights": ["亮点1", "亮点2"],
  "links": {
    "github": "https://github.com/your/repo",
    "doi": "https://doi.org/..."
  }
}
```

**对应文件：** `admin_backend/data/projects.json`

---

### 🔵 发表论文

每项：

```json
{
  "id": "paper-id",
  "title": "论文标题",
  "type": "paper",
  "authors": ["你的名字", "..."],
  "venue": "期刊/会议名",
  "year": 2024,
  "status": "published",
  "description": "简短描述",
  "tags": ["标签1", "标签2"],
  "links": {
    "doi": "https://doi.org/..."
  }
}
```

**对应文件：** `admin_backend/data/publications.json`

---

### 🔵 工具 / 服务

每项：

```json
{
  "id": "tool-id",
  "name": "工具名",
  "description": "描述",
  "category": "分类",
  "status": "deployed / active",
  "tags": ["标签"],
  "access_url": "https://...",
  "links": {
    "github": "https://github.com/..."
  }
}
```

**对应文件：** `admin_backend/data/tools.json`

---

### 🔵 时间线

```json
[
  {
    "period": "2023 - 至今",
    "title": "标题",
    "org": "机构",
    "description": "描述"
  }
]
```

**对应文件：** `admin_backend/data/timeline.json`

---

## ⚙️ 技术栈

| 层 | 技术 |
|:---|:-----|
| 前端 | Streamlit + Jinja2 (Flask) |
| 后端 | Flask 3.1 + Waitress |
| 数据库 | MySQL 8.0（Docker） |
| AI | DeepSeek API |
| 容器 | Docker Compose |
| 分子渲染 | RDKit → PNG |

---

## 📄 License

MIT

---

> ⭐ 如果这个框架对你有帮助，欢迎 Star！  
> 有问题请提 [Issue](https://github.com/Yijian-quiet/web_ai_site/issues)
