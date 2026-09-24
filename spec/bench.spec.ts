// One model over its converted requests in Chrome (WebGPU), with the browser's memory sampled from outside.
//
//   BENCH_MODEL=kev-4b-vision|kev-0.8b-vision|cua-s1-4b-0.2-multimodal [BENCH_OUT=name.jsonl] [BENCH_LIMIT=n]
//   [BENCH_ONLY=id-prefix] [BENCH_EVERY=n] [BENCH_EP=webgpu|wasm] npx playwright test
//
// Memory is the physical footprint (top's MEM, which on Apple silicon includes the GPU buffers a process owns) summed
// over every process of the launched browser, sampled every 2 s: the peak and the idle baseline before loading.
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { test, chromium, expect } from "@playwright/test";

const UNITS: Record<string, number> = { B: 1 / 2 ** 20, K: 1 / 1024, M: 1, G: 1024 };

function tree(root: number): number[] {
  const rows = execFileSync("/bin/ps", ["-axo", "pid=,ppid="]).toString().trim().split("\n").map((l) => l.trim().split(/\s+/).map(Number));
  const out = [root];
  for (let i = 0; i < out.length; i++) for (const [pid, ppid] of rows) if (ppid === out[i]) out.push(pid);
  return out;
}

function footprintMB(root: number): number {
  const pids = tree(root);
  const txt = execFileSync("/usr/bin/top", ["-l", "1", "-stats", "pid,mem", ...pids.flatMap((p) => ["-pid", String(p)])]).toString();
  let mb = 0;
  for (const line of txt.split("\n")) {
    const m = line.trim().match(/^(\d+)\s+([\d.]+)([BKMG])[+-]?$/);
    if (m && pids.includes(Number(m[1]))) mb += Number(m[2]) * UNITS[m[3]];
  }
  return mb;
}

test("bench", async () => {
  const model = process.env.BENCH_MODEL ?? "kev-4b-vision";
  const ep = (process.env.BENCH_EP ?? "webgpu") as "webgpu" | "wasm";
  const out = process.env.BENCH_OUT ?? `${model}-${ep}.jsonl`;
  const server = await chromium.launchServer({ channel: process.env.BENCH_CHANNEL ?? "chrome", args: ["--enable-unsafe-webgpu"] });
  const pid = server.process().pid!;
  const browser = await chromium.connect(server.wsEndpoint());
  const page = await browser.newPage();
  page.on("console", (m) => { if (m.text().startsWith("bench:") || m.type() === "error") console.log(`[browser] ${m.text()}`); });
  await page.goto(`http://127.0.0.1:${process.env.BENCH_PORT ?? 5194}/`);
  await page.waitForFunction(() => window.bench?.ready);
  expect(await page.evaluate(() => self.crossOriginIsolated)).toBe(true);

  const baseline = footprintMB(pid);
  let peak = baseline;
  const timer = setInterval(() => { try { peak = Math.max(peak, footprintMB(pid)); } catch { /* a process exited mid-sample */ } }, 2000);
  let r: Record<string, unknown>;
  try {
    r = await page.evaluate((o) => window.bench.run(o), {
      model, ep, out, limit: Number(process.env.BENCH_LIMIT) || undefined, only: process.env.BENCH_ONLY || undefined, every: Number(process.env.BENCH_EVERY) || undefined,
    });
  } finally {
    clearInterval(timer);
  }
  peak = Math.max(peak, footprintMB(pid));
  const manifest = JSON.parse(readFileSync(`models/${model}/manifest.json`, "utf8"));
  const v = manifest.variants[(r.variant as string) ?? "q8f32"];
  const bundleBytes = v.bytes + (manifest.vision?.bytes ?? 0);
  const meta = { ...r, revision: manifest.revision, run: manifest.run, bundleBytes, memoryMB: { baseline: Math.round(baseline), peak: Math.round(peak) }, at: new Date().toISOString() };
  console.log(JSON.stringify(meta));
  mkdirSync("results", { recursive: true });
  writeFileSync(`results/${out.replace(/\.jsonl$/, "")}.meta.json`, JSON.stringify(meta, null, 1) + "\n");
  await browser.close();
  await server.close();
});
