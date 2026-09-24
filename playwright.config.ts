import { defineConfig } from "@playwright/test";

// BENCH_CHANNEL defaults to the installed Google Chrome: on macOS, Playwright's headless Chromium reports a Metal
// adapter but stalls for minutes in the first 4B pass (kev.js README, testing).
const port = Number(process.env.BENCH_PORT ?? 5194);

export default defineConfig({
  testDir: "spec",
  testMatch: "*.spec.ts",
  timeout: 6 * 3600_000,
  workers: 1,
  reporter: "list",
  use: { baseURL: `http://127.0.0.1:${port}` },
  webServer: { command: "vite", url: `http://127.0.0.1:${port}`, reuseExistingServer: true, timeout: 60_000 },
});
