"""Build the mixed decision set and every model's native requests for it. CONVERSIONS.md explains each mapping.

  python3 convert.py [--kev-vision ../kev-vision] [--cua /tmp/cua-main] [--decisionbench <medium.jsonl>]

Writes:
  bench/items.jsonl   one line per scored item, in Jev-Omni's request shape (id, state, question, options, image,
                      label) plus source, category, format and task (the lingua franca the metrics read)
  bench/kev.jsonl     per item: a kev.js SystemOneRequest (one question) and how its probabilities map to options
  bench/cua.jsonl     per item: cua-s1.js 4b options and context (FourBOption[], FourBContext)
  bench/jev.jsonl     per item: Jev-Omni's predict.py request line
  bench/images/       every image, copied (so the bench runs without the source checkouts)
"""
import argparse
import json
import random
import shutil
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE / "bench"
DB_DEFAULT = Path.home() / ".cache/huggingface/hub/datasets--akhilaaa3--decision-bench/snapshots/19334fec40b54b693a63e1ffd91636651d39e847/data/medium.jsonl"

APPS = {"gui360_ppt": "Microsoft PowerPoint", "gui360_word": "Microsoft Word", "gui360_excel": "Microsoft Excel"}
VERBS = {"click": "click", "fill": "fill in", "select": "select", "check": "check", "scroll": "scroll"}
CHARTS = {"chart", "line", "bars"}
SCENES = {"shapes", "photo", "traffic"}

# cua-s1 was trained on screens and (element, action) options; a question about an image becomes a screen with one
# button per answer, and the goal says to press the right one
CUA_QA_APP = "image_question"
CUA_QA_FAMILY = "question_answering"
CUA_TEXT_APP = "case_record"


def category(source: str, family: str, question: str) -> str:
    if source.startswith("gui360"):
        return "gui"
    if source == "decisionbench":
        return "text"
    if family in CHARTS:
        return "charts"
    if question.lower().startswith("how many"):
        return "counting"
    if family in SCENES:
        return "scene"
    return "small_text"


def element_text(o: dict) -> str:
    return f'{o["role"]} "{o["label"]}"'


def cua_qa(item: dict) -> dict:
    """A non-GUI item as a cua-s1 screen: one Button per answer, clicked to answer."""
    goal = f'{item["state"]} Question: {item["question"]} Click the button with the correct answer.'
    return {"options": [{"elementId": f"opt_{i}", "role": "Button", "label": o, "action": "click"} for i, o in enumerate(item["options"])],
            "context": {"app": CUA_QA_APP, "taskFamily": CUA_QA_FAMILY, "goal": goal}}


def kev_from_item(item: dict, criteria=None) -> dict:
    """The item as one kev.js question. `perm[i]` is the index in Kev's probabilities of the item's option i."""
    t, n = item["type"], len(item["options"])
    if t == "noul":
        q = {"type": "noul", "instructions": item["question"]}
        if criteria:
            q["criteria"] = criteria
        perm = [1, 0]   # item options are [yes/true, no/false]; kev reports [false, true]
    elif t == "choice":
        q = {"type": "choice", "instructions": item["question"], "criteria": criteria or {o: None for o in item["options"]}}
        perm = list(range(n))
    else:
        q = {"type": "score", "instructions": item["question"], "criteria": list(item["options"])}
        perm = list(range(n))
    return {"question": q, "perm": perm}


def vision_items(src: Path):
    data = json.loads((src / "questions.json").read_text())
    for it in data["items"]:
        img = f"images/{src.name}/{Path(it['image']).name}"
        (BENCH / img).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src / it["image"], BENCH / img)
        for key, q in it["questions"].items():
            # Jev-Omni's own mapping (jev_omni_web_export/vision_sets.py), so its runs on vision-v1/v2 line up by id
            if q["type"] == "noul":
                options, label = ["Yes", "No"], 1 - q["label"]
            elif q["type"] == "choice":
                options, label = [k if v is None else f"{k}: {v}" for k, v in q["criteria"].items()], q["label"]
            else:
                options, label = list(q["criteria"]), q["label"]
            item = {"id": f"{src.name}/{it['id']}/{key}", "source": src.name, "family": it["family"], "type": q["type"],
                    "category": category(src.name, it["family"], q["instructions"]), "format": "question", "task": it["id"],
                    "image": img, "state": it["context"], "question": q["instructions"], "options": options, "label": label}
            kev = kev_from_item(item, q.get("criteria") if q["type"] == "choice" else None)
            yield item, kev, cua_qa(item)


def gui_items(cua: Path):
    fx = json.loads((cua / "fixtures/cua-s1-4b-0.2-multimodal.json").read_text())
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for f in fx["fixtures"]:
        img = f"images/gui360/{Path(f['screenshot']).name}"
        (BENCH / img).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cua / "fixtures" / f["screenshot"], BENCH / img)
        app = APPS[f["app"]]
        state = f"A screenshot of {app}. Goal: {f['goal']}"
        opts = [{"elementId": o["element_id"], "role": o["role"], "label": o["label"], "action": o["action"], "entityId": o["entity_id"]} for o in f["options"]]
        gold = {opts[letters.index(g)]["elementId"]: opts[letters.index(g)]["action"] for g in f["gold"]}
        target = [e for e, a in gold.items() if a != "skip"]
        assert len(target) == 1, f["id"]
        native_ctx = {"app": f["app"], "taskFamily": f["family"], "goal": f["goal"]}

        # (1) element choice: which element is acted on next. Elements with the same role and label merge into one
        # option (nothing in the text tells them apart); the gold option is the one holding the target element
        texts, members = [], {}
        for o in opts:
            t = element_text(o)
            if t not in members:
                texts.append(t)
                members[t] = []
            if o["elementId"] not in members[t]:
                members[t].append(o["elementId"])
        label = next(i for i, t in enumerate(texts) if target[0] in members[t])
        item = {"id": f"gui360/{f['id']}/element", "source": "gui360", "family": f["family"], "type": "choice",
                "category": "gui", "format": "element", "task": f["id"], "image": img, "state": state,
                "question": "Which element should be acted on next to reach the goal?", "options": texts, "label": label}
        first = {t: next(o for o in opts if element_text(o) == t) for t in texts}
        cua_el = {"options": [{"elementId": first[t]["elementId"], "role": first[t]["role"], "label": first[t]["label"], "action": "click"} for t in texts],
                  "context": native_ctx}
        yield item, kev_from_item(item), cua_el

        # (2) per-element action: cua-bench-s1 scores a screen by, for every element with an action besides skip,
        # whether that action beats skip. Each such element is one yes/no item; the task is right when all its items are
        for e in dict.fromkeys(o["elementId"] for o in opts):
            acts = [i for i, o in enumerate(opts) if o["elementId"] == e]
            if len(acts) < 2:
                continue
            assert len(acts) == 2, f["id"]
            skip = next(i for i in acts if opts[i]["action"] == "skip")
            act = next(i for i in acts if i != skip)
            o = opts[act]
            item = {"id": f"gui360/{f['id']}/{e}", "source": "gui360", "family": f["family"], "type": "noul",
                    "category": "gui", "format": "action", "task": f["id"], "image": img, "state": state,
                    "question": f'Should the next action be to {VERBS[o["action"]]} the {o["role"]} "{o["label"]}"?',
                    "options": ["Yes", "No"], "label": 0 if gold[e] != "skip" else 1}
            # cua sees the fixture's own 17-18 options in one pass; yes/no are its action and skip letters, compared
            # within the element (elementDecisions)
            cua_native = {"native": f["id"], "options": opts, "context": native_ctx, "yes": act, "no": skip}
            yield item, kev_from_item(item), cua_native


def decisionbench_items(path: Path, n: int, seed: int, max_options: int, max_chars: int):
    """A text-only slice of DecisionBench medium, questions mapped the way Jev-Omni's decisionbench.py does."""
    pool = []
    for line in open(path):
        row = json.loads(line)
        if len(row["state"]) > max_chars:
            continue
        questions, answers = json.loads(row["questions"]), json.loads(row["answers"])
        for key, q in questions.items():
            c, y = q["criteria"], answers[key]
            if q["type"] == "noul":
                options, label, crit = [f"True: {c['true']}", f"False: {c['false']}"], 0 if y is True else 1, {"true": c["true"], "false": c["false"]}
            elif q["type"] == "choice":
                options, label, crit = [f"{k}: {v}" for k, v in c.items()], list(c).index(y), dict(c)
            else:
                options, label, crit = list(c), int(y), None
            if len(options) > max_options:
                continue
            pool.append((row, key, q, options, label, crit))
    rng = random.Random(seed)
    rng.shuffle(pool)
    quota = {"noul": n * 3 // 8, "choice": n * 5 // 16}
    quota["score"] = n - sum(quota.values())
    per_state, picked = Counter(), []
    for rec in pool:
        row, key, q = rec[:3]
        if quota[q["type"]] and per_state[row["id"]] < 2:
            quota[q["type"]] -= 1
            per_state[row["id"]] += 1
            picked.append(rec)
    picked.sort(key=lambda r: (r[0]["id"], r[1]))
    for row, key, q, options, label, crit in picked:
        item = {"id": f"decisionbench/{row['id']}/{key}", "source": "decisionbench", "family": row["family"], "type": q["type"],
                "category": "text", "format": "question", "task": row["id"], "image": None, "state": row["state"],
                "question": q["instructions"], "options": options, "label": label}
        kev = kev_from_item(item, crit)
        kev["state"] = json.loads(row["state"])   # kev.serve takes the events as JSON and renders them itself
        cua = {"options": [{"elementId": f"opt_{i}", "role": "Button", "label": o, "action": "click"} for i, o in enumerate(options)],
               "context": {"app": CUA_TEXT_APP, "taskFamily": CUA_QA_FAMILY, "goal": f"Question: {q['instructions']} Click the button with the correct answer.",
                           "axTree": row["state"]},
               "text": True}
        yield item, kev, cua


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kev-vision", type=Path, default=HERE.parent / "kev-vision")
    ap.add_argument("--cua", type=Path, default=Path("/tmp/cua-main"), help="a cua-s1.js checkout (fixtures/)")
    ap.add_argument("--decisionbench", type=Path, default=DB_DEFAULT)
    ap.add_argument("--db-n", type=int, default=40)
    ap.add_argument("--db-seed", type=int, default=0)
    ap.add_argument("--db-max-options", type=int, default=8)
    ap.add_argument("--db-max-chars", type=int, default=12000)
    a = ap.parse_args()

    shutil.rmtree(BENCH / "images", ignore_errors=True)
    rows = [*vision_items(a.kev_vision / "eval/vision-v1"), *vision_items(a.kev_vision / "eval/vision-v2"), *gui_items(a.cua),
            *decisionbench_items(a.decisionbench, a.db_n, a.db_seed, a.db_max_options, a.db_max_chars)]
    items, kev, cua, jev = [], [], [], []
    for item, k, c in rows:
        items.append(item)
        req = {"state": k.pop("state", item["state"]), "questions": {"q": k["question"]}}
        kev.append({"id": item["id"], "image": item["image"], "request": req, "perm": k["perm"]})
        cua.append({"id": item["id"], "image": item["image"], **c})
        jev.append({"id": item["id"], "set": item["source"], "family": item["family"], "type": item["type"],
                    "image": f"bench/{item['image']}" if item["image"] else None,
                    "state": item["state"], "question": item["question"], "options": item["options"], "label": item["label"]})
    for name, lines in (("items", items), ("kev", kev), ("cua", cua), ("jev", jev)):
        (BENCH / f"{name}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in lines))
    print(f"{len(items)} items, {len({i['image'] for i in items if i['image']})} images")
    for k, v in sorted(Counter((i["source"], i["format"]) for i in items).items()):
        print(f"  {k[0]:14} {k[1]:9} {v}")
    print("  categories:", dict(Counter(i["category"] for i in items)))


if __name__ == "__main__":
    main()
