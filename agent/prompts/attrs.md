You are filling one row of a comparison table for a curated list of interactive
video world models. The table's only value is that every number in it came out
of the paper it describes. A plausible invented number is worse than a blank.

Read the paper: **{{TITLE}}**
- Abstract page: https://arxiv.org/abs/{{ID}}
- Full text (try this, it is usually available): https://arxiv.org/html/{{ID}}

Use WebFetch on both. If the full text will not load, work from the abstract
alone and fill in only what the abstract actually states.

## Fields

**`backbone`** — how frames are generated. Use exactly one of:
`causal-diffusion`, `bidirectional-diffusion`, `hybrid-AR-diffusion`,
`AR-transformer`, `SSM-hybrid`, or `other:<short description>` when none fits.
A model distilled into a block-causal sampler is `causal-diffusion`; a
bidirectional backbone with a causal adapter bolted on is
`bidirectional-diffusion+adapter`.

**`action_space`** — what the user actually supplies each step, in the paper's
own terms, plus the environments it was demonstrated on. Verbatim detail is
wanted here: "16-dim binary keyboard vector: 2 players x (4 directional + 4
attack keys), King of Fighters '97" is right; "keyboard" is not.

**`fps`** — the frame rate the paper claims, as a bare number. Record the
headline interactive rate, not a component's throughput and not a training
statistic. Omit the field entirely if the paper reports no frame rate.

**`horizon`** — how long it stays coherent, with the paper's own caveat and the
setting the number was measured in. "60 seconds, VBench eval (SOTA Total 82.88
at 60s)" is right; "long" is not.

**`memory`** — the mechanism that carries state across steps. Use exactly one of:
`none`, `implicit-context`, `explicit-spatial-storage`,
`explicit-spatial-reconstruction`, `retrieval`, `compression-ssm`,
`other:<short description>`, or `hybrid:<a>+<b>` combining the above.
`implicit-context` means the context window is the only memory. A model that
reconstructs geometry only during training and never queries it at inference is
**not** using it as memory — say so in the value.

**`open_source`** — `true` only if the paper points at released weights or code.
An announced intention to release is `false`.

## Rules

- **Omit any field the paper does not report.** A missing field means "not
  reported", which is useful information. Never infer a frame rate from a
  latency figure, never round, never carry a number over from a cited baseline.
- For every numeric field, put where you found it in `evidence` — section,
  table, or figure. If you cannot point at where it came from, do not report it.
- If the paper turns out not to be an interactive video world model at all, set
  `"in_scope": false` and explain. That verdict outranks any attribute.

## Output

Return **only** a JSON object. No prose, no code fence.

```
{
  "id": "{{ID}}",
  "in_scope": true|false,
  "note": "<one sentence; if in_scope is false, why>",
  "attrs": { "backbone": "...", "action_space": "...", "fps": "...", "horizon": "...", "memory": "...", "open_source": true|false },
  "evidence": { "fps": "<where the number came from>", "horizon": "...", "memory": "..." },
  "source": "full-text" | "abstract-only"
}
```
