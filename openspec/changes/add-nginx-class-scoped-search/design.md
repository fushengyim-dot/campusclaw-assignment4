# 设计说明

- Compose 只把 NGINX 通过 `WEB_PORT` 暴露给宿主机；Flask API 不做宿主机端口映射。
- NGINX 将 `/`、`/health` 和 `/api/` 请求转发到 Docker 内部的 `api:8080` 服务。
- 没有登录会话时，`GET /api/knowledge/search?q=...` 返回 HTTP 401。
- API 从服务端登录会话中取得 `class_id`，并同时用该班级范围过滤 `knowledge_entries` 和 `materials`。
- 检索结果包含 `material_id`、材料标题、来源文件名和已保存的材料内容；当前使用有数量上限的 SQLite `LIKE` 文本匹配。
- 首次初始化账号的密码通过环境变量提供，应用源代码中不硬编码密码。
