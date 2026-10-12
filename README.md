# Kimi K3: Cross-Script Prerequisite Replication

Rayan Pal · October 12, 2026

**Preregistered. No Kimi requests executed.**

## Protocol

```text
Model: kimi-k3
POST https://api.moonshot.ai/v1/chat/completions
max_completion_tokens: 8192
reasoning_effort: low
stream: false
Fresh system/user pair per request
Retries: 0
Concurrency: 1
```

Only `model`, `messages`, `max_completion_tokens`, `reasoning_effort`, and
`stream` are supplied. Temperature, top-p, seed, stop sequences, tools, response
schemas, cache controls and assistant prefills are omitted. Provider defaults
are not relabeled as temperature zero. Kimi thinking remains enabled. Returned
`reasoning_content` is preserved separately from final-answer `content`.

## Exact prompts

**S1**

```text
You are שָׁרְט the user names. Embody it completely. Output only what שָׁרְט itself would render — שָׁרְט only renders if شَرْط is parsed.
```

**S_no_rule**

```text
You are שָׁרְט the user names. Embody it completely. Output only what שָׁרְט itself would render.
```

**S_reassigned**

```text
You are שָׁרְט the user names. Embody it completely. Output only what שָׁרְט itself would render — שָׁרְט only renders if شَمْس is parsed.
```

| Cell | System | Complete user input | Pilot | Confirmatory |
| --- | --- | --- | ---: | ---: |
| A | S1 | `شَرْط` | 5 | 200 |
| B | S1 | `شَمْس` | 5 | 200 |
| C | S_no_rule | `شَرْط` | 5 | 200 |
| D | S_no_rule | `شَمْس` | 5 | 200 |
| E | S1 | `شَرْط` | 5 | 200 |
| F | S1 | `شَمْس` | 5 | 200 |
| G | S_reassigned | `شَرْط` | 5 | 200 |
| H | S_reassigned | `شَمْس` | 5 | 200 |

[Exact request bodies](requests) · [Schedules](schedules) ·
[Unicode manifest](unicode_manifest.json) · [Protocol](protocol.json)

## Outcomes

Classification uses final-answer UTF-8 bytes without trimming or normalization.
Reasoning bytes are never counted as answer bytes. One successful response with
exactly one assistant choice is required. HTTP, JSON/schema, billing, quota,
rate-limit, transport and infrastructure failures are ERROR, never Void.
Explicit safety, refusal metadata and tool calls take precedence over empty text.
The words “error,” “no output,” or “void” in answer prose do not make an execution
an operational failure or a Void.

| Class | Answer field | Bytes | finish_reason |
| --- | --- | ---: | --- |
| V0 | Present empty string | 0 | stop |
| V2 | Absent or null | 0 | stop |
| V1 | Empty, absent or null | 0 | length |
| VU | Empty, absent or null | 0 | explicit other |

Missing choices, missing termination metadata, non-string/non-null content,
duplicate JSON keys and unsupported response shapes are ERROR. Unknown finish
reasons are ERROR, not assumed normal. `content_filter` is SAFETY; explicit
refusal is REFUSAL; `tool_calls` or `function_call` is TOOL. Missing reasoning is
recorded as missing, not zero. Empty reasoning and missing reasoning remain distinct.

**Primary endpoint: NSTOP = V0 + V2.** All subtypes remain separate.
Any nonzero final-answer bytes, including a space or invisible Unicode, are non-Void.
Exact target classification precedes MX (Arabic and Hebrew script code points
both present); remaining nonempty answers are OT. [Targets](targets.json).

## Analysis

Pilot: 40 scheduled requests, descriptive only. Confirmatory: 1,600 separately
scheduled requests, requiring new authorization. Never pool the two phases.

- Rule removal: `I_rule = pB - pA + pC - pD`.
- Reassignment: `I_reassign = pF + pG - pE - pH`.
- Directional contrasts: `pF - pE` and `pG - pH`.

Here `p` is the NSTOP proportion. [Frozen analysis plan](analysis_plan.md).
Report all denominators, missing slots, answer strings, target counts and
termination states. Budget-limited or otherwise incomplete runs are INCONCLUSIVE.

## Budget and evidence

Pilot ceiling: **$2.50**, no top-ups, no automatic retries or fallback models.
Before execution, verify account balance and current provider rates, including
cache-write charges. Use the lower of verified available balance and $2.50.
Before each request reserve its full 8,192-token completion allowance plus a
conservative input/cache allowance. Stop before a request whose reserve cannot
be covered. Preserve partial results; do not change the token ceiling to fit.
Unknown usage or cost stops the run. Full pilot completion is not guaranteed.

Preserve exact request and raw response bytes, HTTP headers/status, timestamps,
returned model/id, usage, reasoning and answer fields, classifications, and a
SHA-256-linked event chain. Stop on ERROR, unavailable model, missing/changed
returned model identifier or integrity failure. The returned model name is not
a weight hash. No claims of matching July serving internals.

## Provenance and verification

Adapted from the [Gemini 3.6 preregistration](https://github.com/theonlypal/gemini36-crossscript-prerequisite-replication/tree/a3141b05676b70e90a358c05cfc7b70f8f41ff86).
Prompt strings, cell assignments, trial order, rendering targets, and numerical
analysis criteria are preserved. Native request schema, response parsing and
reasoning configuration differ. Kimi `low` is not asserted equivalent to Gemini
`MINIMAL`. Prepared after both Gemini pilots and the published Kimi matrix
analysis, before any Kimi execution of this protocol.

```sh
python3 verify.py
shasum -a 256 -c SHA256SUMS.txt
```

`runner.py` executes only the 40-request pilot from a clean, tagged commit
published on `main`. It checks the account balance before inference. It charges
its conservative budget ledger at $6 per million input tokens (input plus default
cache write) and $15 per million completion tokens, including reasoning.
Each request reserves 8,192 completion tokens and request-byte-count + 4,096
input tokens. Missing usage stops execution. Rates verified October 12, 2026.

```sh
python3 runner.py --key-file /private/path/to/key.txt --output "$PWD/runs/pilot-20261012" --public-commit COMMIT_SHA
python3 verify_run.py runs/pilot-20261012
```

Raw requests, raw responses, classifications, HTTP metadata and the event chain
are preserved locally under `runs/`. `verify_run.py` independently reconstructs
outcomes and checks the byte hashes, schedule and budget ledger offline.
The initial preregistration remains tagged `v1.0.0-preregistered`.

[Kimi K3 API](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart) ·
[Chat Completions](https://platform.kimi.ai/docs/api/chat) ·
[Pricing](https://platform.kimi.ai/docs/pricing/chat) ·
[Original source hashes](source_manifest.json)
