# 技术栈

> 版本: v3.1 | 最后更新: 2026-06-15

## 基础设施
| 组件 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| 云服务器 | 腾讯云 CVM | 2C4G 20GB | your-domain.com |
| 操作系统 | TencentOS Server | 3.1 | 基于 CentOS |
| 容器引擎 | Docker CE | 28.0.1 | Compose v2.32.1 |

## 应用服务
| 服务 | 技术 | 端口 | 部署方式 |
|------|------|:----:|:--------:|
| AI 聊天 | Streamlit 1.58 | 8501 | Docker |
| 管理后台+个人站 | Flask 3.1 + Jinja2 | 5000 | Docker |
| 博客 | Flask（同上） | 5000 | Docker |
| 数据库 | MySQL 8.0 | 3306 | Docker |
| 反向代理 | Nginx 1.26 | 80 | 宿主机 |

## AI 模型
| 模型 | 服务商 | API |
|:----|:------|:----|
| deepseek-chat | DeepSeek | api.deepseek.com/v1 |
| BAAI/bge-small-zh-v1.5 | BGE | 本地 ONNX（RAG 检索） |

## 邮件服务
| 配置 | 值 |
|:----|:---|
| SMTP | smtp.qq.com:465 (SSL) |
| 邮箱 | your-email@example.com |

## 项目结构
```
/var/www/web_ai/
├── docker-compose.yml          # 编排文件
├── yijian_AI/                  # Streamlit 聊天站
│   ├── app_qwen.py
│   ├── config.py
│   ├── models/                 # data models
│   ├── services/               # AI/email services
│   └── utils/
├── admin_backend/              # Flask 管理后台 + 个人站
│   ├── app.py                  # Flask 应用（含个人站路由）
│   ├── blog_rag_service.py     # BGE RAG 检索服务
│   ├── data/                   # JSON 数据文件 ← 内容修改入口
│   │   ├── profile.json        # 个人信息
│   │   ├── projects.json       # 项目介绍
│   │   ├── publications.json   # 发表论文
│   │   ├── tools.json          # 工具列表
│   │   └── timeline.json       # 时间线
│   ├── templates/              # Jinja2 模板
│   └── Dockerfile
├── context/                    # 项目文档
│   ├── product.md
│   ├── tech-stack.md
│   ├── workflow.md
│   └── tracks.md
└── 修改历史.md
```

## 数据驱动架构
- 个人站内容（首页/关于/项目/发表/工具）由 JSON 文件驱动
- 博客文章存储于 MySQL，通过管理后台 CRUD 操作
- `data/` 目录已挂载为 Docker 卷，修改即时生效（docker restart 后）
