const en = {
  // Header
  "app.title": "Trip Decision Agent",
  "app.subtitle": "Tell me where you are and what shops you want — I'll find the nearest mall that fits",

  // Empty state
  "empty.title": "Trip Decision Agent",
  "empty.hint": "Tell me your location and the shops/brands you care about. I'll search nearby malls on the map, check the shops, compute real travel distances, and recommend the best option.",
  "empty.features": "Tencent Maps · Nearby malls · Shop check · Real distance",

  // Chat input
  "chat.placeholder": "e.g. I'm near Honglian South Rd subway station. Find the closest mall that has both Breo and Xiting Cunwu...  ⏎ Send",
  "chat.hint": "Powered by OpenAI Agents SDK + Tencent Maps + EdgeOne Makers",

  // Preset questions
  "preset.1": "I'm near Honglian South Rd subway station. Which nearby mall has both Breo and Xiting Cunwu, and is the closest?",
  "preset.2": "I'm at Guomao subway station. Find malls with Xiting Cunwu nearby and recommend by walking distance.",

  // Tool indicators
  "tool.locate": "Locate",
  "tool.malls": "Find malls",
  "tool.shops": "Check shops",
  "tool.distance": "Distance",

  // Status & errors
  "status.error": "Request failed. Please check if the backend service is running.",
  "status.stopped": "⏹ *Generation stopped*",
  "status.backendError": "Backend abort request failed. The server may still be running.",

  // Debug panel
  "debug.title": "Trace",
  "debug.events": "events",
  "debug.clear": "Clear",
  "debug.empty": "Waiting for SSE events...",
  "debug.emptyHint": "After sending a message, all raw backend data will be displayed here.",

  // Conversation sidebar
  "sidebar.label": "Conversation list",
  "sidebar.title": "Chats",
  "sidebar.newChat": "New chat",
  "sidebar.loading": "Loading conversations...",
  "sidebar.loadMore": "Load more",
  "sidebar.loadingMore": "Loading...",
  "sidebar.emptyTitle": "No conversations yet",
  "sidebar.emptyHint": "Click \"New chat\" to start your first conversation.",
  "sidebar.delete": "Delete conversation",
  "sidebar.deleteConfirm": "Permanently delete this conversation? This cannot be undone.",

  // Aria labels (button hover/screen-reader)
  "aria.send": "Send",
  "aria.clearHistory": "Clear history",
  "aria.stopGeneration": "Stop generation",

  // Language toggle
  "lang.switch": "中文",

  // ─── Floating bottom-right action badges ─────────────────────────────
  "floatingLink.deploy": "Deploy",
  "floatingLink.github": "GitHub",
} as const;

export default en;
