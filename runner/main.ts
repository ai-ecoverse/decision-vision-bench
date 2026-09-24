// Runs one model over its converted requests (bench/<kev|cua>.jsonl) on onnxruntime-web and appends one result line per
// item to results/<out>.jsonl: the probabilities in the item's option order and where the time went. Playwright drives
// it (bench.spec.ts); it resumes, skipping ids already in the results file.
import * as ort from "onnxruntime-web/webgpu";
import wasm from "onnxruntime-web/ort-wasm-simd-threaded.asyncify.wasm?url";
import mjs from "onnxruntime-web/ort-wasm-simd-threaded.asyncify.mjs?url";
import { loadKev, toRecord, validate, type ImageLike, type Kev, type OrtModule, type SystemOneRequest } from "kev";
import { loadCuaS1FourB, preprocess, renderChat, ropePositions, visionInputs, type CuaS1FourB, type FourBContext, type FourBOption } from "@ai-ecoverse/cua-s1.js/4b";
import type { InferenceSession } from "onnxruntime-common";

ort.env.wasm.wasmPaths = { wasm, mjs };
ort.env.wasm.numThreads = self.crossOriginIsolated ? Math.min(4, navigator.hardwareConcurrency || 2) : 1;
ort.env.logLevel = "warning";

const logEl = document.getElementById("log")!;
const say = (s: string) => { console.log(`bench: ${s}`); logEl.textContent += `${s}\n`; };

interface KevLine { id: string; image: string | null; request: SystemOneRequest; perm: number[] }
interface CuaLine {
  id: string; image: string | null; options: FourBOption[]; context: FourBContext;
  text?: boolean; native?: string; yes?: number; no?: number;
}
interface Timing { decode: number; preprocess: number; vision: number; decoder: number; total: number }
/** `letters`: a native cua-s1 pass's probabilities over the fixture's own options (the task metric reads them) */
interface Result { id: string; probs: number[]; ms: Timing; tokens: number; imageTokens: number; shared?: boolean; letters?: number[] }

async function jsonl<T>(url: string): Promise<T[]> {
  const t = await (await fetch(url)).text();
  return t.split("\n").filter(Boolean).map((l) => JSON.parse(l) as T);
}

/** RGBA pixels as PIL reads the file: no colour-space conversion, no premultiplication. */
async function decodeImage(url: string): Promise<ImageLike> {
  const bitmap = await createImageBitmap(await (await fetch(url)).blob(), { colorSpaceConversion: "none", premultiplyAlpha: "none" });
  const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
  const ctx = canvas.getContext("2d")!;
  ctx.drawImage(bitmap, 0, 0);
  const { data, width, height } = ctx.getImageData(0, 0, bitmap.width, bitmap.height);
  bitmap.close();
  return { data, width, height };
}

async function image(path: string | null): Promise<{ img?: ImageLike; ms: number }> {
  if (!path) return { ms: 0 };
  const t0 = performance.now();
  const img = await decodeImage(`/bench/${path}`);
  return { img, ms: performance.now() - t0 };
}

// ---- Kev ------------------------------------------------------------------------------------------------------------

async function kevItem(kev: Kev, l: KevLine): Promise<Result> {
  const { img, ms: decode } = await image(l.image);
  const t0 = performance.now();
  const { record } = toRecord(validate(l.request));
  const enc = kev.encode(record);
  const [p] = await kev.probsEncoded(enc, undefined, img);
  const total = performance.now() - t0;
  const t = kev.timing;
  return {
    id: l.id, probs: l.perm.map((j) => p[j]), tokens: enc.tokens + (img ? t.imageTokens + 2 : 0), imageTokens: img ? t.imageTokens : 0,
    ms: { decode, preprocess: t.preprocess, vision: t.vision, decoder: t.state + t.branches, total },
  };
}

// ---- cua-s1 ---------------------------------------------------------------------------------------------------------

const yesNo = (p: number[], l: CuaLine) => { const y = p[l.yes!], n = p[l.no!]; return [y / (y + n), n / (y + n)]; };

async function cuaPass(m: CuaS1FourB, l: CuaLine): Promise<{ probs: number[]; ms: Timing; tokens: number; imageTokens: number }> {
  if (l.text) {
    // text-only items: the multimodal adapter with the prompt of cua-s1's text modality (the state as the tree)
    const t0 = performance.now();
    const ids = m.tokenizer.encode(renderChat(l.options, l.context, "text"), { add_special_tokens: false }).ids;
    const probs = await m.probsForIds(ids, l.options.length);
    const total = performance.now() - t0;
    return { probs, tokens: ids.length, imageTokens: 0, ms: { decode: 0, preprocess: 0, vision: 0, decoder: total, total } };
  }
  const { img, ms: decode } = await image(l.image);
  const vis = m.manifest.vision!, cfg = vis.config, T = ort.Tensor;
  const session = (m as unknown as { vision: InferenceSession }).vision;
  const t0 = performance.now();
  const p = preprocess(img!, cfg), vi = visionInputs(p.gridH, p.gridW, cfg), P = p.gridH * p.gridW, hd = cfg.hidden_size / cfg.num_heads;
  const t1 = performance.now();
  const out = await session.run({
    patches: new T("float32", p.data, [P, p.data.length / P]),
    pos_idx: new T("int64", vi.posIdx, [P, 4]), pos_w: new T("float32", vi.posW, [P, 4]),
    cos: new T("float32", vi.cos, [P, hd]), sin: new T("float32", vi.sin, [P, hd]),
  }, ["image_embeds"]);
  const embeds = out.image_embeds.data as Float32Array;
  const t2 = performance.now();
  const n = embeds.length / m.manifest.hidden_size;
  const ids = m.encode(l.options, l.context, n);
  const probs = await m.probsForIds(ids, l.options.length, { embeds, pos: ropePositions(ids, p.gridH, p.gridW, vis.image_token_id, cfg.merge_size) });
  const t3 = performance.now();
  return { probs, tokens: ids.length, imageTokens: n, ms: { decode, preprocess: t1 - t0, vision: t2 - t1, decoder: t3 - t2, total: t3 - t0 } };
}

function cuaRunner(m: CuaS1FourB) {
  const native = new Map<string, number[]>();
  return async (l: CuaLine): Promise<Result> => {
    if (l.native) {
      // one pass over the fixture's own options serves every yes/no item of that screen: yes is the element's action,
      // no its skip, compared between themselves as cua-bench-s1 does (elementDecisions)
      const seen = native.get(l.native);
      if (seen) {
        return { id: l.id, probs: yesNo(seen, l), ms: { decode: 0, preprocess: 0, vision: 0, decoder: 0, total: 0 }, tokens: 0, imageTokens: 0, shared: true };
      }
      const r = await cuaPass(m, l);
      native.set(l.native, r.probs);
      return { id: l.id, ...r, probs: yesNo(r.probs, l), letters: r.probs };
    }
    return { id: l.id, ...(await cuaPass(m, l)) };
  };
}

// ---- driver ---------------------------------------------------------------------------------------------------------

async function adapterInfo(): Promise<string | null> {
  const gpu = (navigator as Navigator & { gpu?: { requestAdapter(): Promise<{ info?: Record<string, string> } | null> } }).gpu;
  const a = await gpu?.requestAdapter();
  return a ? [a.info?.vendor, a.info?.architecture, a.info?.description].filter(Boolean).join(" ") || "unknown" : null;
}

/** `every`: every n-th item only (a spread-out subset, for latency passes) */
export interface RunOptions { model: string; variant?: string; ep?: "webgpu" | "wasm"; out: string; limit?: number; only?: string; every?: number }

async function run(o: RunOptions) {
  const ep = o.ep ?? "webgpu", variant = o.variant ?? "q8f32";
  const adapter = ep === "webgpu" ? await adapterInfo() : null;
  if (ep === "webgpu" && !adapter) throw new Error("no WebGPU adapter");
  const isKev = o.model.startsWith("kev-");
  const lines = (await jsonl<KevLine & CuaLine>(`/bench/${isKev ? "kev" : "cua"}.jsonl`))
    .filter((l, i) => (!o.only || l.id.startsWith(o.only)) && i % (o.every ?? 1) === 0).slice(0, o.limit);
  const done = new Set((await jsonl<Result>(`/results/${o.out}`)).map((r) => r.id));
  say(`${o.model} ${variant} ${ep}${adapter ? ` (${adapter})` : ""}: ${lines.length} items, ${done.size} already done`);

  const t0 = performance.now();
  // Kev without its state cache: every item pays its own image and state pass, as a cua-s1 or Jev-Omni call does
  const make = isKev
    ? await loadKev(`/models/${o.model}`, { ort: ort as unknown as OrtModule, variant, executionProviders: [ep], cacheName: null, stateCacheSize: 0 })
      .then((kev) => () => (l: KevLine & CuaLine) => kevItem(kev, l))
    : await loadCuaS1FourB(`/models/${o.model}`, { ort: ort as unknown as Parameters<typeof loadCuaS1FourB>[1]["ort"], variant, executionProviders: [ep], cacheName: null })
      .then((m) => () => cuaRunner(m));
  const loadMs = performance.now() - t0;
  say(`loaded in ${Math.round(loadMs)} ms`);

  const todo = lines.filter((l) => !done.has(l.id));
  if (todo.length) {
    // one untimed pass first: the first run of each graph compiles its shaders
    const warm = todo.find((l) => l.image) ?? todo[0];
    const w = await make()(warm);
    say(`warm-up ${warm.id}: ${Math.round(w.ms.total)} ms`);
  }
  const item = make();   // fresh, so the warm-up leaves no native fixture cached
  const t1 = performance.now();
  for (const [i, l] of todo.entries()) {
    const r = await item(l);
    await fetch(`/results/${o.out}`, { method: "POST", body: JSON.stringify({ ...r, model: o.model, variant, ep }) });
    if (i < 3 || i % 25 === 0) say(`${i + 1}/${todo.length} ${l.id}: ${Math.round(r.ms.total)} ms`);
  }
  return { model: o.model, variant, ep, adapter, loadMs: Math.round(loadMs), items: todo.length, runMs: Math.round(performance.now() - t1) };
}

declare global { interface Window { bench: { ready: boolean; run: typeof run } } }
window.bench = { ready: true, run };
say(`ready; crossOriginIsolated=${self.crossOriginIsolated}`);
