import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  webServer: [
    {
      command: '../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000',
      cwd: '../backend',
      url: 'http://127.0.0.1:8000',
      reuseExistingServer: true,
      timeout: 30_000
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 3003',
      cwd: '.',
      url: 'http://127.0.0.1:3003',
      reuseExistingServer: true,
      timeout: 30_000
    }
  ],
  use: {
    baseURL: 'http://127.0.0.1:3003',
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure'
  }
})
