import { defineConfig } from 'vite'

// 本地体验：将后端 API 请求代理到 edgeone makers dev 启动的 Python 服务（9100 端口）
const backend = 'http://127.0.0.1:9100'

export default defineConfig({
  server: {
    proxy: {
      '/chat': backend,
      '/stop': backend,
      '/history': backend,
      '/conversations': backend,
      '/clear-history': backend,
      '/delete-conversation': backend,
    },
  },
})
