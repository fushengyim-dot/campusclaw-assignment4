# Design

- Flask + SQLite；服务端渲染页面，便于用 curl 和浏览器复核。
- 密码只存 Werkzeug 哈希；会话中的 `user_id`、`role`、`class_id` 由服务端写入，`SECRET_KEY` 只从环境变量读取。
- 每个业务查询在服务端使用会话中的 `class_id` 过滤；前端隐藏按钮不算访问控制。
- 上传链路为：文件扩展名校验 → 落盘 → `materials` 与 `knowledge_entries` 同事务写入；失败时回滚数据库并删除文件。
- Compose 挂载 `data/` 与 `uploads/`，保证重启后数据仍在。
