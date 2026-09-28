(() => {
  const form = document.querySelector("#knowledge-search-form");
  const queryInput = document.querySelector("#knowledge-query");
  const status = document.querySelector("#search-status");
  const results = document.querySelector("#search-results");
  if (!form || !queryInput || !status || !results) return;

  const showMessage = (message, kind = "") => {
    status.textContent = message;
    status.className = `search-status ${kind}`.trim();
  };

  const renderResults = (items) => {
    results.replaceChildren();
    if (!items.length) {
      showMessage("没有找到本班匹配材料。", "muted");
      return;
    }
    showMessage(`找到 ${items.length} 条本班材料。`, "success");
    for (const item of items) {
      const card = document.createElement("article");
      card.className = "search-result";
      const title = document.createElement("h3");
      title.textContent = item.title;
      const source = document.createElement("div");
      source.className = "search-source";
      source.textContent = `来源：${item.source_filename} · 材料 ID：${item.material_id}`;
      const excerpt = document.createElement("p");
      excerpt.textContent = item.content;
      card.append(title, source, excerpt);
      results.append(card);
    }
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;
    showMessage("正在搜索…");
    results.replaceChildren();
    try {
      const response = await fetch(`/api/knowledge/search?q=${encodeURIComponent(query)}`, {
        headers: { Accept: "application/json" },
      });
      if (response.status === 401) {
        showMessage("登录状态已失效，请重新登录。", "error");
        return;
      }
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      renderResults(payload.results || []);
    } catch (_error) {
      showMessage("搜索失败，请检查服务是否正常运行。", "error");
    }
  });
})();
