## ADDED Requirements

### Requirement: NGINX 是宿主机入口

Compose 部署 MUST 通过 NGINX 暴露网页入口，MUST NOT 将 Flask API 服务直接发布到宿主机。NGINX MUST 将应用页面、健康检查和 `/api/` 路由转发到内部 API 服务。

#### Scenario: 可以通过 NGINX 访问健康检查

- **WHEN** 客户端从已发布的网页端口请求 `/health`
- **THEN** 当 API 健康时，NGINX 将请求转发到内部 API，并返回 HTTP 200

#### Scenario: API 没有宿主机端口映射

- **WHEN** 检查 Compose 服务配置
- **THEN** API 服务没有已发布的宿主机端口，只能通过 Compose 内部网络访问

### Requirement: 限定班级范围的知识检索 API

已登录用户 MUST 能够通过 `GET /api/knowledge/search?q=...` 搜索已保存的知识内容。服务器 MUST 从登录会话中取得班级范围，同时按该范围过滤知识记录和材料记录，并返回包括材料 ID、标题和文件名在内的来源信息。当前实现 MAY 使用有数量上限的 SQLite 文本匹配，MUST NOT 将其描述为语义向量检索。

#### Scenario: 已登录用户得到本班检索结果

- **WHEN** 已登录用户搜索本班材料中存在的文字
- **THEN** 服务器返回 HTTP 200、匹配结果和来源信息

#### Scenario: 未登录检索被拒绝

- **WHEN** 客户端没有有效登录会话却发起检索
- **THEN** 服务器返回 HTTP 401，且不返回知识内容

#### Scenario: 排除其他班级的检索结果

- **WHEN** 用户搜索只存在于其他班级的文字
- **THEN** 服务器返回 HTTP 200，且不返回其他班级的结果

### Requirement: 网页知识搜索

已登录的材料页面 MUST 提供关键词搜索框，调用限定班级范围的知识检索 API，并显示每条结果的材料名称、来源文件名、材料 ID 和返回的原文摘录。浏览器 MUST NOT 将用户自行选择的班级编号作为权限参数发送。

#### Scenario: 用户从材料页面发起搜索

- **WHEN** 已登录用户输入关键词并提交搜索表单
- **THEN** 页面请求 `/api/knowledge/search`，并显示返回的来源信息和原文摘录
