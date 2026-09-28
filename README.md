# CampusClaw 迭代 1

面向中小学教研场景的基础版本：登录、角色权限、班级隔离、材料上传与知识库入库。

本迭代不包含智能问答、技能路由、MCP、作业提交与批改；这些属于后续 change。当前提供一个按登录用户班级隔离的基础知识检索 API。

## 启动

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SECRET_KEY = "replace-with-a-random-secret"
$env:SEED_TEACHER_PASSWORD = "replace-with-a-teacher-password"
$env:SEED_STUDENT_A_PASSWORD = "replace-with-a-student-a-password"
$env:SEED_STUDENT_B_PASSWORD = "replace-with-a-student-b-password"
python -m app
```

浏览器打开 `http://127.0.0.1:8080`。首次初始化数据库时必须提供三个种子账号密码；已有数据库不会重新覆盖用户密码。

## Compose

复制 `.env.example` 为 `.env`，填入随机密钥和本地演示账号密码，再执行：

```bash
docker compose up --build
```

浏览器访问 `http://127.0.0.1:8088`。NGINX 是唯一的宿主机入口，Flask API 只在 Compose 内部网络提供服务。数据保存在 `data/`，上传文件保存在 `uploads/`。健康检查：`GET /health`。

生产环境必须使用新的账号密码，并通过环境变量提供 `SECRET_KEY`；不要把 `.env`、数据库或上传材料提交到仓库。

## 验收边界

- 未登录访问受保护页面会被引导到登录页。
- 学生不能上传材料；服务端返回 403。
- 用户只能看到自己班级的材料。
- 教师上传 txt/md 后，材料记录与知识库记录在同一事务中增加。
- 访问不存在或其他班级材料不会泄露材料正文。
- `GET /api/knowledge/search?q=关键词` 只返回当前登录用户班级内的匹配材料，并附带来源文件名。
