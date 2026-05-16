# Quickstart

A short first-run guide for Liminate. If you want a deeper tour of
the language, read [`syntax.md`](syntax.md) next.

## Requirements

- Python 3.10 or later
- `pytest` (installed via the dev extras below)

## Install

```bash
git clone https://github.com/rmichaelthomas/liminate.git
cd liminate
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Run the test suite

There are 641 tests. They run in well under a second.

```bash
pytest tests/
```

A clean run is the easiest way to confirm the interpreter is wired
up correctly in your environment.

## Run an example file

The repo ships with two example programs in `examples/`:

```bash
python -m liminate examples/program1_basics.limn
python -m liminate examples/program2_orders.limn
```

Each non-blank line is echoed first as canonical prose — the parser's
plain-English description of what it is about to run — followed by any
output the statement produces.

## Start the REPL

```bash
python -m liminate
```

You'll see:

```
Liminate v3a — type 'exit' to quit.
>
```

Type a statement and press enter. Type `exit` (or `quit`) to leave.
The REPL stays in Phase 1 — `when` blocks need the multi-line block
parser, which only the file driver invokes. To exercise listener
mode, write the program to a file and run it via `python -m liminate
<file> --pack <pack.json>`.

## Try this first

Save the following three lines as `demo.limn`:

```
gather the numbers from 1 to 10
filter the numbers where each is above 5
combine the numbers
```

Run it:

```bash
python -m liminate demo.limn
```

Expected output (the `I understand this as:` lines are the canonical
preview):

```
I understand this as: gather the numbers from 1 to 10
1, 2, 3, 4, 5, 6, 7, 8, 9, 10
I understand this as: filter the numbers where each is above 5
I understand this as: combine the numbers
40
```

What happened:

- `gather` built `[1, 2, ..., 10]`, stored it under the name `numbers`,
  and auto-shows it.
- `filter` modified `numbers` in place. After this line `numbers` holds
  `[6, 7, 8, 9, 10]`. There is no output because `filter` is silent on
  success.
- `combine` summed the remaining numbers (6 + 7 + 8 + 9 + 10 = 40) and
  auto-shows the result. The source list is unchanged — `combine` does
  not modify `numbers`.

## Test mode and clean output

If you want to run a `.limn` file non-interactively without being
prompted to confirm amber outcomes (such as a mixed-precedence
condition), use `--test`:

```bash
python -m liminate --test examples/program2_orders.limn
```

For clean output with the `I understand this as: ...` echo
suppressed — useful for any program longer than a few lines — add
`--quiet`:

```bash
python -m liminate --test --quiet examples/dogfood_1_corpus_summary.limn
```

Blank source lines mirror through to the output under `--quiet` so
your paragraph breaks survive. Flags work in any order.

## Try Phase 2 — event-driven listener mode

The v3a addendum adds a reactive runtime that watches for changes to
named values and runs registered handlers when their compound
eligibility transitions false→true. Save this as `listener.limn`:

```
remember a number called level with 0

when level is above 100
  show "level escalated"

when level is above 200
  finish
```

Then save this as `listener-pack.json`:

```json
{
  "name": "monitor",
  "declarations": [],
  "script": [
    ["level", 150],
    ["level", 250],
    "[done]"
  ]
}
```

Run it with the `--pack` flag pointing at the JSON file:

```bash
python -m liminate --pack listener-pack.json --test --quiet listener.limn
```

Expected output:

```
Listening for changes to: level
level escalated
Program stopped.
```

Walkthrough: Phase 1 sets `level=0` and registers two handlers (no
firing yet). Phase 2 begins — the LISTENING marker prints, initial
evaluation finds neither handler's condition true (level is 0), and
the adapter starts pushing scripted updates. The first update
(`level=150`) makes both handlers' eligibility transition: handler 0
fires (`show "level escalated"`), handler 1's condition is false
still (150 ≤ 200). The second update (`level=250`) fires handler 1,
which executes `finish` — immediate total shutdown.

The full v3a dogfood at `examples/dogfood_v3a_event_driven.limn` (with
its companion `examples/dogfood_v3a_pack.json`) exercises every major
v3a feature: initial evaluation, `unless` guards, `of`-expression
conditions, multi-statement action blocks, parameterized compositions
called from action blocks, cascading triggers, and `finish` via a
`choose` branch.

## Where to go next

- [`syntax.md`](syntax.md) — full syntax tour through v3a.
- [`../architecture/pipeline.md`](../architecture/pipeline.md) — how a
  source line becomes a result, including the Phase 2 listener layer.
- [`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md) — what
  the interpreter includes and what it deliberately does not.
- [`../spec/`](../spec/) — the immutable specification documents the
  interpreter is built against.
