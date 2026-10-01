# Conversions

Every item is asked of every model in that model's own request format. `convert.py` does all of it. This file lists
each mapping and what it can and cannot tell apart.

The shared record is `bench/items.jsonl`, in Jev-Omni's request shape (`id, state, question, options, image, label`)
plus `source`, `format`, `category` and `task`. Every model's probabilities come back in that record's option order,
and `label` indexes into it.

## Sources

| source | items | tasks | from |
|---|---:|---:|---|
| vision-v1 | 106 | 41 images | kev.js `eval/vision-v1` (the image condition; the caption is never shown) |
| vision-v2 | 128 | 44 images | kev.js `eval/vision-v2` (rendered pages and charts) |
| gui360 `element` | 60 | 60 screens | cua-s1.js `fixtures/cua-s1-4b-0.2-multimodal.json` (GUI-360 test split) |
| gui360 `action` | 77 | 60 screens | the same 60 screens |
| decisionbench | 40 | 32 states | DecisionBench medium @19334fe, seeded slice (text only) |

**DecisionBench slice.** Seed 0 picks 15 noul, 12 choice and 13 score questions. The filters:
- the state is at most 12,000 characters;
- at most 8 options, which fits cua-s1's 26 letters with room to spare;
- at most 2 questions per state.

**Categories.** GUI-360 items are `gui` and DecisionBench items are `text`. The kev sets are split this way:
- `charts`: the chart, line and bars families;
- `counting`: other questions that start with "How many";
- `scene`: shapes, photo and traffic;
- `small_text`: everything else (screens, receipts, signs, inbox, shop, orders, departures, label, terms, dashboard).

## Kev (kev.js SystemOneRequest, one question per request)

- **vision-v1/v2:** the item's context is the state, and the image goes in front of it. The question is sent
  unchanged: noul, choice (with its criteria and descriptions), or score. This is exactly what kev.js's vision eval
  sends, except that each question goes in its own request.
- **gui360 element:** state `A screenshot of Microsoft PowerPoint. Goal: <goal>`, plus the screenshot.
  - The question is a `choice`: "Which element should be acted on next to reach the goal?"
  - There is one criterion per element, keyed `Button "Zoom In"`, with no description.
- **gui360 action:** the same state, with a `noul` question: `Should the next action be to fill in the Button "A1"?`
- **decisionbench:** the row's events, parsed from JSON, are the state; kev.js renders them itself. Questions go
  through in their native TypeSafe form: noul with its true/false criteria, choice with its descriptions, score with
  its levels.

Kev runs without its state cache (`stateCacheSize: 0`). Every item pays for its own vision tower pass and state pass,
as a cua-s1 or Jev-Omni call does. Probabilities are at the checkpoint's serving temperature, which is what kev.js
serves.

## cua-s1-4b-0.2 multimodal (cua-s1.js `./4b`: FourBOption[] plus FourBContext, one letter per option)

- **gui360 action (native):** the fixture's own 17 or 18 options (16 elements, each with `skip` and sometimes one
  more action), with the fixture's app, task family and goal.
  - There is one pass per screen, and each action item reads its element's action letter against its skip letter.
    This is cua-bench-s1's own per-element scoring (`elementDecisions`), and the pass reproduces the fixture's
    probabilities.
- **gui360 element:** the same context, with one option per element (after merging duplicates, as below). Every
  option has the action `click`.
  - The native options can't be used here: only the target elements carry a non-skip action, so they would give the
    answer away (the skip-wording leak).
  - A uniform action gives no hint about which element is the target.
- **vision-v1/v2:** a screen with one `Button` per answer, labelled with the option text, action `click`.
  - app `image_question`, task family `question_answering`.
  - goal: `<context> Question: <question> Click the button with the correct answer.`
  - The item's image is the screenshot.
- **decisionbench:** the multimodal adapter has no image here. It gets cua-s1's text-modality prompt, with the
  state's raw JSON as the accessibility tree, app `case_record`, and the same button options and goal wording. There
  is no image placeholder; the graph gets a zero `image_embeds` row that is never gathered. The adapter was trained
  on screenshots, so this row tests the base model's text skill through a foreign prompt.

## Jev-Omni (predict.py request lines; `bench/jev.jsonl`)

- **vision-v1/v2:** Jev-Omni's own `vision_sets.py` mapping, so its existing runs line up by id:
  - state is the context, question is the instructions, and the image comes first;
  - noul → `["Yes", "No"]`, with the label flipped;
  - choice → `key` or `key: description`;
  - score → the levels.
- **gui360:** the Kev text (state, question, options) with the screenshot. Element options are the element texts;
  action items are Yes/No.
- **decisionbench:** Jev-Omni's `decisionbench.py` mapping: `True: …`/`False: …`, `key: description`, and the levels.
  The ids match its `reference-fp32.jsonl` and `browser-q8f32.jsonl` for this slice.

## RSI-Jev v4.0-VL (Jev-compatible `POST /v1/systemone`; `torch/rsijev_client.py`)

- **Every source:** Kev's request from `bench/kev.jsonl`, unchanged, plus `model`. The image goes in `images` as a data
  URL of the file's own bytes, and the server puts it before the state. One question per request.
- **Probabilities** come back in the API's order (noul: false, true; choice: criteria order; score: levels) and are
  put in the item's option order with kev.jsonl's `perm`.
- **One DecisionBench state** (b3-m-0054) is an event list whose events carry a free-text `role`. The server, like
  Jev's reference, reads that as a chat transcript and refuses it, so it is sent as the same events in compact JSON
  text. Its row carries a `note`.

## Known limits

- **Duplicate element names.** In 20 of the 60 screens, two or three elements share a role and label (for example
  three `Button "More Options"`). Nothing in any model's text tells them apart. For element choice they merge into
  one option, and the gold is whichever merged option holds the target element; screens have 14 to 16 options. The
  action items and cua's native pass keep them separate, which is as ambiguous for every model.
- **GUI-360 gold labels are one recorded trajectory.** Some are debatable. For example, a goal of "select Header &
  Footer under Insert" is recorded as a fill on cell A1.
- **Unbalanced action items.** Of the 77 action items, 60 have the answer yes and 17 no. Always saying yes scores
  77.9%, and always saying yes gets the 43 single-candidate screens right. On the 17 screens with two candidates,
  this baseline still gets the task wrong.
