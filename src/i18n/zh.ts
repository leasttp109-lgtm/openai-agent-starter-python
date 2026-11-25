const zh = {
  // Header
  "app.title": "出行决策 Agent",
  "app.subtitle": "告诉我你在哪、想找什么店，帮你挑出最近最合适的商场",

  // Empty state
  "empty.title": "出行决策 Agent",
  "empty.hint": "输入你的位置和你关心的店铺/品牌，我会通过地图检索附近商场、核查店铺、计算真实距离，给你可执行的推荐。",
  "empty.features": "腾讯位置服务 · 附近商场 · 店铺核查 · 真实距离",

  // Chat input
  "chat.placeholder": "例如：我在红莲南路地铁站附近，想找既有倍轻松又有西厅村屋的近商场…  ⏎ 发送",
  "chat.hint": "由 OpenAI Agents SDK + 腾讯位置服务 + EdgeOne Makers 驱动",

  // Preset questions
  "preset.1": "我在红莲南路地铁站附近，想找既有倍轻松又有西厅村屋的商场，哪个最近？",
  "preset.2": "我在国贸地铁站，帮我找附近有西厅村屋的商场，按步行距离推荐。",

  // Tool indicators
  "tool.locate": "解析位置",
  "tool.malls": "检索商场",
  "tool.shops": "核查店铺",
  "tool.distance": "计算距离",

  // Status & errors
  "status.error": "⚠️ 请求失败，请检查后端服务是否启动。",
  "status.stopped": "⏹ *已停止生成*",
  "status.backendError": "⚠️ 后端中断请求失败，服务端可能仍在运行。",

  // Debug panel
  "debug.title": "传输流",
  "debug.events": "事件",
  "debug.clear": "清除",
  "debug.empty": "等待 SSE 事件...",
  "debug.emptyHint": "发送消息后，所有原始后端数据将在此处显示。",

  // Conversation sidebar
  "sidebar.label": "会话列表",
  "sidebar.title": "会话",
  "sidebar.newChat": "新建聊天",
  "sidebar.loading": "正在加载会话...",
  "sidebar.loadMore": "加载更多",
  "sidebar.loadingMore": "加载中...",
  "sidebar.emptyTitle": "暂无会话",
  "sidebar.emptyHint": "点击「新建聊天」开始第一段对话。",
  "sidebar.delete": "删除会话",
  "sidebar.deleteConfirm": "确定要永久删除这个会话吗？此操作不可恢复。",

  // Aria labels (button hover/screen-reader)
  "aria.send": "发送",
  "aria.clearHistory": "清除历史",
  "aria.stopGeneration": "停止生成",

  // Language toggle
  "lang.switch": "English",

  // ─── Floating bottom-right action badges ─────────────────────────────
  "floatingLink.deploy": "一键部署",
  "floatingLink.github": "GitHub",
} as const;

export default zh;
