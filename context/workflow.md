# 开发工作流

> 版本: v2.0 | 最后更新: 2026-06-15

## 开发流程
1. **需求分析** — 在微信中提出需求
2. **设计** — 小小静（AI 助手）设计技术方案
3. **实现** — 直接修改服务器文件或重建 Docker 镜像
4. **部署** — docker compose up -d / docker restart
5. **验证** — curl 测试 + 人工确认

## 内容更新流程（无需重启容器）

JSON 数据文件已挂载为 Docker 卷，修改后需要重启 Flask 容器：

```bash
# 编辑 JSON 数据
nano /var/www/web_ai/admin_backend/data/projects.json
# 修改完成后重启容器
docker restart web_ai_flask
```

## 小文件更新流程（不用重建镜像）

```bash
# 更新单个文件（如模板、app.py）
docker cp <本地文件> web_ai_flask:/app/data/xxx.json
docker restart web_ai_flask
```

## 全量更新流程

```bash
# 重建并重启
cd /var/www/web_ai
docker compose up -d --force-recreate <服务名>
```

## Git 工作流
当前未使用 Git，直接在生产服务器上修改。

## 质量检查
- [x] Python 语法检查（py_compile 或 ast.parse）
- [x] Nginx 配置验证（nginx -t）
- [x] HTTP 状态码验证（curl）
- [x] Streamlit 不崩溃（docker logs）

## 备份策略
- MySQL: 每天凌晨 3:00 mysqldump → /backup/
- 保留 7 天，自动清理
