import { appendFileSync, createReadStream, existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { defineConfig, type Plugin } from "vite";

// The browser runner: runner/ as the page, the bundles under /models (models/, symlinks and clones), the converted set
// under /bench, and POST /results/<name>.jsonl appending one result line (GET returns the file, for resuming).
const repo = fileURLToPath(new URL(".", import.meta.url));
const isolation = { "Cross-Origin-Opener-Policy": "same-origin", "Cross-Origin-Embedder-Policy": "require-corp" };
const safe = (p: string) => /^[\w.-]+(\/[\w.-]+)*$/.test(p) && !p.split("/").includes("..");

const files: Plugin = {
  name: "bench-files",
  configureServer(server) {
    server.middlewares.use("/models/", (req, res, next) => {
      const path = decodeURIComponent(req.url ?? "").split("?")[0].replace(/^\/+/, "");
      const file = `${repo}/models/${path}`;
      if (!safe(path) || !existsSync(file) || !statSync(file).isFile()) return next();
      res.setHeader("content-length", String(statSync(file).size));
      res.setHeader("content-type", path.endsWith(".json") ? "application/json" : "application/octet-stream");
      createReadStream(file).pipe(res);
    });
    server.middlewares.use("/bench/", (req, res, next) => {
      const path = decodeURIComponent(req.url ?? "").split("?")[0].replace(/^\/+/, "");
      const file = `${repo}/bench/${path}`;
      if (!safe(path) || !existsSync(file)) return next();
      res.setHeader("content-type", path.endsWith(".png") ? "image/png" : path.endsWith(".jpg") ? "image/jpeg" : "application/json");
      createReadStream(file).pipe(res);
    });
    server.middlewares.use("/results/", (req, res, next) => {
      const name = decodeURIComponent(req.url ?? "").split("?")[0].replace(/^\/+/, "");
      if (!/^[\w.-]+\.jsonl$/.test(name)) return next();
      const file = `${repo}/results/${name}`;
      if (req.method === "POST") {
        let body = "";
        req.on("data", (c) => (body += c));
        req.on("end", () => {
          mkdirSync(`${repo}/results`, { recursive: true });
          appendFileSync(file, JSON.stringify(JSON.parse(body)) + "\n");
          res.end("ok");
        });
        return;
      }
      res.setHeader("content-type", "text/plain");
      res.end(existsSync(file) ? readFileSync(file) : "");
    });
  },
};

export default defineConfig({
  root: `${repo}/runner`,
  appType: "mpa",
  plugins: [files],
  resolve: { alias: { kev: fileURLToPath(new URL("../kev-vision/src/index.ts", import.meta.url)) } },
  server: {
    headers: isolation, host: "127.0.0.1", port: Number(process.env.BENCH_PORT ?? 5194), strictPort: true,
    fs: { allow: [repo, fileURLToPath(new URL("../kev-vision", import.meta.url))] },
  },
  optimizeDeps: { exclude: ["onnxruntime-web"] },
});
