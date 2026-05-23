# Liminate syntax

A practical guide to writing Liminate programs. Liminate is a bounded
prose language: 58 reserved words plus user-provided names and literal
values. The prose IS the program.

This guide covers the full shipped surface: v1, v2a (`keep`, `of`,
multi-field `each show`, descriptor preservation), v2b (composition
return values + generalized `of`), v2c (quoting for multi-word
strings), v2d (composition parameters with `from`, `choose` with
`if`/`otherwise`), v3a (event-driven listener mode — `when`,
`unless`, `finish`, indented action blocks, domain-pack adapters),
the `add`/`remove`/`weakens`/`require`/`assign`/`expect` verb
additions, the Infrastructure Era (`by`/`plus`/`minus`/`multiplied
by`/`divided by` arithmetic, `sort`/`reverse`, `compare`, `transform`),
the Deontic Era (`forbid`/`permit` — completing the
require/forbid/permit triangle), and the Temporal-Boundary Era
(`starting`/`until` — effective dates and sunset clauses).
See [`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md) for
what's intentionally not built.

If you have not run the interpreter yet, start with
[`quickstart.md`](quickstart.md).

## Source files

- An Liminate source file uses the `.limn` extension and is plain
  text.
- **One statement per line.** Each non-blank line is a complete
  statement.
- **Blank lines are skipped.** Use them freely as paragraph breaks
  between groups of statements.
- **Decorative punctuation is stripped.** Commas, periods, question
  marks, and exclamation marks at word edges are removed before
  parsing, so you can punctuate naturally:
  `show colors.` is read as `show colors`, and
  `filter the orders where total is above 50.` is read as
  `filter the orders where total is above 50`.
  Commas are decorative only; they do not replace `and` as a list
  separator. In v1, list items are always joined by `and`.
- **Case-insensitive.** `SHOW Age` and `show age` are identical to the
  interpreter. Names and string values are normalized to lowercase
  internally.

## Names

User-provided names (variables, fields, named compositions) follow
three rules:

- Start with a letter.
- Contain letters, digits, and hyphens.
- Cannot be one of the 58 reserved words.

Valid: `age`, `orders`, `find-big-orders`, `order1`, `my-list`.

Invalid: `1st-order` (starts with a digit), `filter`
(reserved verb), `when` (reserved — v3a connective).

Multi-word names use hyphens (`big-orders`, `priority-label`). The
quoting mechanism (v2c) brackets multi-word *values*, never names —
see [Values](#values) and [Quoting](#quoting) below.

## Verbs

There are twenty-one verbs. Most statements begin with one.

### `remember`

Stores a value, list, record, or named composition.

**A single value:**

```
remember a number called age with 30
remember a value called greeting with hello
```

The descriptor between the article and `called` (here `number` and
`value`) is decorative — the interpreter ignores it for semantics. The
type is inferred from the value itself: `30` is a number, `hello` is
text. Your descriptor is preserved in the canonical-prose echo
("I understand this as: remember a number called age with 30") so the
language reads back the way you wrote it.

**A list:**

```
remember a list called colors with red and blue and green
remember a list called nums with 1 and 2 and 3 and 4 and 5
```

Items are separated by `and`. Lists must be homogeneous — see
[Lists](#lists).

**A record (with fields):**

```
remember an order called order1 with total as 75 and status as active
```

Use `as` to assign a value to each named field. Fields are separated
by `and`.

**Capturing a verb-phrase result:**

```
remember the result called total from combine the numbers
```

When you use `from <verb-phrase>` instead of `with <value>`, the
interpreter executes the inner phrase and stores its return value.

**A named composition:**

See [Named compositions](#named-compositions) below.

If you `remember` something with a name that already exists, the new
value silently overwrites the old one. The type can change.

### `show`

Displays a value.

```
show age
show colors
```

A list of strings or numbers shows as comma-separated values
(`red, blue, green`). A record shows as `field: value` pairs. A list
of records shows one record per line.

Inside `each`, `show` may be used without a target to display the
current iterator item.

**Single-record field access** uses `of`:

```
show total of order1
show status of order1
```

`<field> of <record>` extracts one field from a named record. The
field must exist on that record, and `<record>` must be a single
record (not a list — for lists, iterate with `each`). See the
[`of` connective](#the-of-connective) section.

### `filter`

Reduces a list **in place** by a condition.

```
filter the orders where total is above 50
filter the orders where status is active
filter the numbers where each is above 5
```

After `filter`, the original list contains only the items that
matched. Filter produces no output on success — use `show` or `count`
afterward to inspect the result. To filter without mutating the
source, use [`keep`](#keep) instead.

### `keep`

Like `filter`, but **non-destructive**: returns the matching items as
a fresh list while leaving the source untouched.

```
keep the orders where total is above 50
```

By default, `keep` auto-shows its matches. To capture the result for
further analysis, use `remember ... from keep ...`:

```
remember the big-orders called big from keep the orders where total is above 50
show big
count the orders   # still 3 — keep didn't mutate the source
```

`keep` is the natural building block for reusable filter compositions:

```
remember how to find-big: keep the orders where total is above 50
find-big   # auto-shows matches; orders unchanged
find-big   # callable again; same result
```

Capturing `find-big`'s result for further analysis uses the v2b
composition-return-value form:

```
remember the matches called big from find-big
show big
count the orders   # still 3 — keep didn't mutate the source
```

The captured value is whatever the composition's last operation
returns (v2b §76). For a composition whose last op is a side-effect-
only verb (`show`, `filter`, `each`, `choose`, `finish`), the call
site fails with a "doesn't return a value" error — the language
forbids capturing nothing.

**Conditions** have the shape `<field> is <operator> <value>` or, for
flat lists, `each is <operator> <value>`:

| Operator        | Meaning                                          |
|-----------------|--------------------------------------------------|
| `is`            | equality (when not followed by another operator) |
| `is above`      | strictly greater than                            |
| `is below`      | strictly less than                               |
| `is equal to`   | explicit equality                                |
| `is not above`  | less than or equal to (includes the boundary)    |
| `is not below`  | greater than or equal to (includes the boundary) |
| `is not equal to` | not equal                                      |
| `is within N of M` | numeric tolerance: `\|field − M\| ≤ N`          |
| `includes`      | list membership (`<list> includes <value>`)      |
| `not includes`  | absence from a list                              |

Note that `not above N` means `≤ N` — the boundary value `N` is
*kept*, not removed. This is intentional and distinct from `below N`.

`is within N of M` is the numeric-tolerance comparison: it is true when
the field is within `N` of the target `M` (the boundary is inclusive).
All three operands must be numbers. `N` may be a literal or a name; `M`
may be any value expression, including a field access:

```
require amount is within 5 of target
keep the readings where each is within 2 of baseline
choose if amount is within tol of total of order1: show "close enough"
```

**Compound conditions** use `and` and `or` inside the same `where`:

```
filter the orders where total is above 50 and status is active
filter the orders where total is below 30 or status is pending
```

`and` binds tighter than `or`. Mixing them in a single condition
triggers a confirmation prompt before execution.

### `count`

Returns the number of items in a list, and shows the result.

```
count the colors
count the orders
```

### `gather`

Generates an inclusive numeric range, stores it, and shows it.

```
gather the numbers from 1 to 10
```

The name after the article (`numbers`) becomes the new symbol. v1
ranges must be ascending (`from` ≤ `to`) and contain at most 10,000
items.

### `combine`

Sums the numbers in a list. The result is shown.

```
combine the numbers
```

`combine` does **not** modify the source list. To capture the sum, use
`remember ... from combine ...`:

```
remember the result called total from combine the numbers
```

`combine` is numeric-only in v1: it cannot concatenate strings or
merge records.

### `each`

Iterates over a list. For every item the sub-operation runs once
against that item.

```
each the orders show total
each the orders show status
each the numbers show
```

While inside `each`, the iterator binds a "current item" used for two
purposes:

- A field name in the sub-operation resolves against the current
  record. `show total` looks up `total` on each order.
- `show` with no argument displays the current item itself — useful
  for flat lists or whole records.

**Multi-field display.** Inside `each ... show`, multiple field names
can be separated with `and` to produce one labeled line per record:

```
each the orders show total and status
```

Output:

```
total: 75, status: active
total: 30, status: active
total: 120, status: pending
```

Field order in the output follows the user's order in the source.
Three or more fields work the same way (`show a and b and c`).
Listing the same field twice (`show class and class`) is a semantic
error — the language assumes that's a typo.

Inside a `where` clause, `each` is a **pronoun** for the current item
being tested, not the iteration verb:

```
filter the numbers where each is above 5
```

**Note:** `each ... keep where ...` is rejected at parse time. `keep`
and `filter` are list operations; per-record decisions live in the
where-clause of a list operation, not in an `each` body. The error
suggests the list-level alternative.

### `add`

Appends an item to an existing list.

```
add "new-task" to tasks
add 42 to scores
```

The item is any value (number, string, bare word, or `<field> of
<record>`). The target must be a list. The list's type is inferred on
first add into an empty list; subsequent adds must match.

### `remove`

Retracts an item from an existing list. Mirror of `add`.

```
remove "old-task" from tasks
```

If the item is not in the list it is a runtime error — `remove` is
explicit, not silent.

### `weakens`

Attaches autonomous linear decay to a numeric value. The value falls
linearly to zero over the stated period (in abstract ticks). Reading
the value at any point computes the current decayed amount.

```
remember a value called urgency with 1.0
weakens urgency over 10
```

Re-assigning a number to a decaying value reinforces it — period
preserved, decay restarted from the new initial value.

### `require`

Evaluates a condition. If it holds, execution continues silently. If
it fails, the program halts with `REQUIREMENT_NOT_MET` and the error
message echoes the condition and the actual value of the first
failing sub-condition.

```
require amount is above 50000
require allergy-list not includes "penicillin"
```

The condition grammar matches `where` and `choose if` — comparison
operators, `includes`, `not`, compound `and` / `or`, field access
via `of`. Mixed `and` / `or` in one clause triggers the amber prompt.

### `forbid`

The mirror of `require`. Evaluates a condition; if it holds, the
program halts with `PROHIBITION_VIOLATED` and the error message echoes
the condition and the triggering value. If the condition is false,
`forbid` passes silently. Where `require` halts on a *false* condition,
`forbid` halts on a *true* one.

```
forbid total is above 10000
forbid categories includes "restricted"
```

Same condition grammar as `require`. `require` and `forbid` are
independent — neither knows about the other.

### `permit`

The third corner of the deontic triangle, and the one that never
halts. Evaluates a condition; if it holds, `permit` emits one
informational line — `Permitted: <condition>. <actual>.` — and
execution continues with `SUCCESS`. If the condition is false, it
passes silently. `permit` follows the `expect` pattern (emit on match)
rather than the `require`/`forbid` pattern (halt on violation).

```
permit expenses is below 5000
permit category is "travel"
```

Together the three express obligation (`require`), prohibition
(`forbid`), and permission (`permit`). They compose freely in a
sequence and evaluate independently:

```
require total is above 100 and forbid total is above 10000 and permit category is "travel"
```

### `assign`

Stores an item-to-recipient mapping. The item becomes the variable
name; the recipient becomes its value.

```
assign review-task to "compliance-team"
assign case-47 to supervisor
```

`assign` overwrites any existing entry with that name. Combine with
`when` for reactive delegation: change the trigger, and the handler
re-assigns the recipient.

### `expect`

Evaluates a condition like `require`, but does not halt on failure.
A met expectation is silent; a diverged expectation emits one output
line — `Expectation not met: <condition>. <actual>.` — and execution
continues with `SUCCESS`.

```
expect revenue is above 1000000
expect margin is above 0.1
```

`require` is enforcement (halt on fail); `expect` is informational
tracking (report on fail, keep going). Both share the same condition
grammar.

### Sequencing with `then`

Two operations joined with `then` form a declared sequence — same
parser shape as `and`, but with stated ordering intent.

```
add "received" to audit-log then require amount is above 50000
```

Stepwise commit applies: earlier operations remain even if a later
one fails.

### `sort`

Reorders a list in place by a field. Ascending (smallest first, A–Z)
by default; add `in reverse` (or just `reverse`) for descending.

```
sort the orders by total
sort the orders by total in reverse
sort the people by name
```

`sort` mutates the list — subsequent `show` or `each` sees the new
order. Other fields on each record are preserved. Sorting a list whose
field values mix incomparable types (some numbers, some text) is a
runtime error.

### `compare`

Compares two values and stores a structured result record named
`comparison`, with a `status` field and a `divergences` field. The
comparison mode is inferred from the operand types.

```
compare original to revised
show status of comparison
show divergences of comparison
```

`status` is one of `match`, `mismatch`, `type_mismatch`, or
`length_mismatch`. For two records, `divergences` lists the field
names that differ (sorted); for two lists, the differing indices; for
scalars, it is empty. The result is overwritten by the next `compare`.
Branch on it with `choose if status of comparison is equal to "match"`.

### `transform`

Mutates each element of a list in place by an expression. Two forms:

```
transform total of the orders by total minus discount
transform the scores by each plus 5
```

The first (record-field mode) rewrites the named field on every
record; the second (scalar-list mode) replaces each element, where
`each` refers to the current value. The expression after `by` is a
full arithmetic expression — see [Arithmetic](#arithmetic) — evaluated
per element with field names resolving against the current element
first, then the symbol table.

## Temporal boundaries (`starting` / `until`)

Two statement-initial connectives give a rule an effective date and a
sunset clause. They attach to any verb statement and take a quoted
ISO 8601 date (`YYYY-MM-DD`):

```
starting "2025-07-01" require amount is above 50000
until "2025-12-31" forbid total is above 10000
starting "2025-07-01" until "2025-12-31" permit category is "travel"
```

`starting` declares when a rule takes effect; `until` declares when it
expires. Either may appear alone, both may co-occur, or neither. When
both are present, `starting` comes first — the reverse order is a parse
error.

The dates are **inert metadata**. The interpreter validates the
`YYYY-MM-DD` format at parse time and stores the values on the AST, but
it does *not* evaluate them against a clock — a rule with a temporal
boundary executes exactly as it would without one. Whether a rule is
currently `active`, `expired`, `future`, or `unbounded` is a
product-layer concern (for example, the Receipts inspection surface),
not interpreter runtime. Termination is hard: a rule is in effect or it
is not, with no decay. For gradual decay, compose with
[`weakens`](#weakens).

Temporal boundaries are the outermost statement-initial modifiers. The
full canonical order is:

```
starting "2025-07-01" until "2025-12-31" inherited require amount is above 50000 because "regulatory cap" from agent-compliance
```

## Arithmetic

Values can be combined with arithmetic operators wherever a value is
expected (after `with`, `from`, `as`, on the right side of a
comparison, and in `transform`/`add` items):

| Operator        | Meaning        |
|-----------------|----------------|
| `plus`          | addition       |
| `minus`         | subtraction    |
| `multiplied by` | multiplication |
| `divided by`    | division       |

```
remember a value called total from price plus tax
remember a value called net from gross minus fees
remember a value called pay from rate multiplied by hours
remember a value called share from amount divided by people
```

Precedence follows PEMDAS: `multiplied by` and `divided by` bind
tighter than `plus` and `minus`, and operators of the same tier
evaluate left to right. So `base plus bonus multiplied by rate`
multiplies first. There is no parenthesized grouping — break complex
expressions into steps with `remember`. Division by zero is a runtime
error, and arithmetic operands must be numbers.

## Lists

Lists are constructed with `and` between values:

```
remember a list called colors with red and blue and green
remember a list called scores with 1 and 2 and 3
remember a list called orders with order1 and order2 and order3
```

In v1, **lists are homogeneous**. Every item must be the same kind:
all numbers, all text, or all records. Mixing types is a semantic
error:

```
remember a list called bad with 1 and blue
```

> Error: A list can't mix numbers and text. '1' is a number but 'blue'
> is text.

If you write `remember a list called X with Y` (a single item), the
descriptor `list` forces list construction so `X` is a one-item list,
not a flat value.

## Records

Records use `as` to bind values to named fields:

```
remember an order called order1 with total as 75 and status as active
remember an order called order2 with total as 30 and status as active
```

Inside a list of records, every record should share the same field
names. When you reference a field in a `where` clause (such as
`total`), the interpreter checks that every record in the list has
that field — otherwise it stops before running, and the error names
the first record that's missing the field:

> Error: 'item1' in 'mixed-records' doesn't have a field called
> 'total'. Other items do have it.

When no record at all has the field, the wording reflects that:

> Error: No item in 'orders' has a field called 'nonexistent'.

## The `of` connective

`<field> of <record>` accesses one field of one record. It's the
counterpart to `each ... show <field>` for cases where you just want
one value from one named record:

```
show total of order1
show status of order1
```

Three checks fire at parse/validation time:

- The record name must exist (`'ghost' is unknown` → error).
- It must be a single record, not a list. If you point `of` at a list,
  the error suggests `each`:

  > Error: 'of' needs a single record. 'orders' is a list of records
  > — did you mean: each the orders show total?

- The record must have the named field.

`of` works in every value position (v2b §77):

- After `show`: `show total of order1`.
- After comparison operators: `keep the orders where total is above total of baseline`.
- In `with` value position: `remember a number called copy with total of order1`.
- In `from`-value position: `remember the snapshot called s from total of order1`.
- In `choose if` conditions, on either side: `choose if total of o1 is above total of o2: …`.
- In `when` and `unless` conditions: `when status of patient is equal to critical`.

The single-level rule still holds: `a of b of c` is a parse error. v1
records are flat, so nested field access has no shape to land on yet.

## Named compositions

Use `remember how to <name>: <body>` to define a reusable sentence.
The body is parsed at definition time but its names are resolved at
call time.

```
remember how to find-big-orders: filter the orders where total is above 50
```

Call the composition by writing its name on its own line:

```
find-big-orders
```

A composition body may chain operations with `and`:

```
remember how to count-active: filter the orders where status is active and count the orders
```

Calling a composition runs its body against the current symbol table.
If the body references a name that does not exist when you call it,
the interpreter raises a semantic error at the call site, not at the
definition.

### Parameters (v2d)

A composition can declare one named parameter with `from <param>`
between the composition name and the colon. Call sites pass an
argument with `from <name>`:

```
remember how to find-high from data: keep the data where total is above 50

remember a list called big-orders with order1
remember a list called small-orders with order2

find-high from big-orders     # auto-shows matches from big-orders
find-high from small-orders   # reusable on a different list
```

The parameter is a local binding (deep-copied from the argument) for
the duration of the body's execution. The global of the same name, if
any, is shadowed and restored on return. Parameters are names-only —
you cannot pass a literal value. Calling a parameterized composition
without an argument is an error, and calling a parameterless
composition *with* an argument is also an error (v2d §97). A
parameterized call in value-capture position uses two `from`s:

```
remember the result called captured from find-high from big-orders
```

### Return values (v2b)

A composition's call returns the value of its last operation (v2b §76).
The return shape depends on the last verb: `keep` returns a list,
`combine` returns a number, `count` returns a number, `gather` returns
the generated list. `remember`-from-verb-phrase returns the captured
value. Side-effect-only verbs (`show`, `filter`, `each`, `choose`,
`finish`) make the composition unsuitable for value-capture position —
the analyzer rejects `remember the X from <comp>` with the "doesn't
return a value" wording.

## `choose` (v2d)

Conditional branching for sequential statements:

```
remember a number called score with 75
choose if score is above 90: show "excellent"
otherwise if score is above 50: show "passing"
otherwise show "needs work"
```

Conditions use the same operand resolution as `where` clauses (names,
`of` expressions, literals) but resolve against the symbol table
directly — there is no iterator context inside `choose`. The first
branch whose condition is true fires; later branches are skipped.
The optional terminal `otherwise <action>` (with no `if`) runs if no
prior condition matched. The colon is the context switch between
condition and action.

A branch's action may itself be a multi-statement sequence joined by
`and <verb>`:

```
choose if score is above 90: show "excellent" and remember a string called tier with gold
```

`choose` is side-effect-only — it doesn't produce a value, so using
it as the last operation of a composition called in value-capture
position is rejected.

`choose` inside `each` is deferred (v2d §102). The error message
points at `keep` as the list-level alternative.

## Quoting (v2c)

By default, every string value is a single bare word. Multi-word values
(or values that collide with the reserved-word list) use double quotes:

```
remember an order called o1 with total as 75 and status as "in progress"
remember a value called priority-label with "high priority"
remember a value called keyword with "filter"
show "Section A: counts"
```

The quoting rules:

- Quotes are **value-position only**. Names and field names use
  hyphens — `priority-label`, not `"priority label"`.
- A quoted value preserves spaces and any punctuation. Decorative
  punctuation stripping (commas, periods) is bypassed inside quotes.
- Quoted reserved words become data: `with status as "filter"` stores
  the string "filter" rather than treating it as the verb.
- The renderer's conditional-quoting rule (v2c §90) drops quotes
  around single-word non-reserved values when echoing canonical
  prose, so `with status as "active"` reads back as
  `with status as active` while `with status as "in progress"` keeps
  its quotes.
- An empty quoted string `""` is a parse error — quotes must contain
  a value.
- A quoted field name (e.g. `show "total" of order1`) is rejected
  with a hyphenation suggestion: "Field names can't have spaces. Try
  a hyphenated name like 'total' instead."

## Event-driven listener mode (v3a)

A `when` line at indent 0 registers a reactive handler. Its action
block is indented underneath:

```
remember a number called level with 0
remember a string called alert-mode with off

when level is above 100
  remember a string called alert-mode with on
  show "level escalated"

when alert-mode is equal to on
  show "alarm sounding"
```

### Two-phase execution

- **Phase 1** runs every top-level sequential statement (`remember`,
  `show`, `filter`, etc.) as before. `when` lines register handlers
  but do not execute their actions yet.
- **Phase 2** starts after Phase 1 completes with zero errors AND at
  least one handler registered. The interpreter performs initial
  evaluation (any handler whose compound eligibility is already true
  fires in registration order), then starts the registered domain
  packs and drains their event queue. Each adapter update changes a
  symbol-table value; dependent handlers re-evaluate. Handlers fire
  on false→true transitions of their compound eligibility.

If a program has no `when` blocks, only Phase 1 runs — every existing
v2d program is unchanged. If a program has `when` blocks but no domain
packs registered (no `--pack` flag), Phase 2 performs initial
evaluation and immediately shuts down.

### Indented action blocks

- Indent at least one space. Tabs in leading whitespace are rejected
  at the lexer level.
- The first indented line after the `when` line sets the block's
  depth; every subsequent line in the block must use the same depth.
  Indentation deeper than the block's depth is a parse error;
  indentation shallower (including zero) ends the block.
- The colon after the `when` line is optional. Present or absent, the
  indented block defines the action scope.
- Blank lines inside a block are skipped — they don't end the block.
- An empty block (a `when` line followed immediately by a top-level
  line or EOF) is a parse error.
- A single-statement action block is one indented line. A
  multi-statement action block is several.

### `unless` guard

`unless` appears between the `when` condition and the action block.
The compound eligibility is `when-true AND NOT unless-true`:

```
when temperature is above 100 unless silenced is equal to true
  show "alert"
```

If the alarm has been silenced, the handler is suppressed even though
the temperature has crossed the threshold. The guard's dependencies
are watched too — changes to `silenced` re-evaluate the handler.

### `finish`

The new verb `finish` exits listener mode immediately and totally:

```
when level is above 200
  finish
```

`finish` is "immediate and total" (v3a §112): when it executes, no
remaining statements in the action block run, no cascades from this
handler's modifications process, no sibling handlers from the same
event evaluate, no queued adapter updates dispatch, the adapters are
stopped, and the listener yields a terminal `SHUTDOWN` result.
`finish` works the same way inside a `choose` branch and inside a
composition called from an action block.

`finish` outside an action block (in Phase 1 sequential code) is a
semantic error.

### Cascading and cycle detection

Action-block writes are watched too. Setting `alert-mode` inside the
first handler's action triggers the second handler's eligibility
transition (a "cascade"). Cascades resolve depth-first. The conservative
cycle guard rejects same-handler-twice in one cascade chain as a
runtime error and skips the would-be loop; the handler stays active
for future events.

### Live values and domain packs

A domain pack declares one or more *live values* — names whose
authoritative value comes from an external event source. Phase 1
`remember` may initialize a live value (the natural pattern of setting
state before listener mode begins), but once Phase 2 starts, the
adapter owns it: `remember` targeting a live-value name from inside
an action block is a semantic error, and `filter` (destructive)
targeting a live-value name is a semantic error in *all* contexts.
The non-destructive verbs (`keep`, `show`, `count`, `combine`, `each`)
are fine.

v3a ships only a test adapter (`TestAdapter`) for scripted event
sequences. Real-world adapters (sensors, messaging brokers, etc.) are
downstream product work, not language work. Pack registration is
external — via the `--pack <path>` CLI flag (which loads a JSON test
domain pack) or the `Session(domain_packs=...)` constructor.

## Values

A literal value can be:

- **A number** — digits with an optional single decimal point.
  Examples: `30`, `3.14`, `100`. The language does not support
  negative numbers or scientific notation.
- **A single-word string** — any bare word that is not a number and
  not in the reserved-word list. Examples: `red`, `active`,
  `portland`. Strings are case-folded to lowercase.
- **A quoted multi-word string** — any text inside `"..."` (v2c).
  Used for values that contain spaces or that collide with the
  reserved-word list. Examples: `"in progress"`, `"high priority"`,
  `"filter"` (the literal word "filter" as data, not the verb). See
  [Quoting](#quoting-v2c) for the full rules.

Vocabulary words (the 58 reserved words) cannot be used **unquoted**
as values:

```
remember a list called items with filter and blue
```

> Error: The word 'filter' is a verb in Liminate and can't be used
> as a value. Try a different word, or wrap it in quotes: "filter".

Wrapping the reserved word in quotes is the v2c remedy — quoted
content bypasses the vocabulary lookup.

## Mixed `and` / `or` and the amber prompt

A `where` clause that mixes `and` and `or` is unambiguous to the
parser (standard precedence: `and` binds tighter than `or`) but
ambiguous to human intuition. The interpreter pauses and shows you
the grouping it's about to use:

```
filter the orders where total is above 50 and status is active or status is pending
```

> I'll read this as: (total is above 50 and status is active) or
> status is pending. Is that what you mean? If not, split it into two
> statements.

Type `y` to proceed or `n` to abort and rewrite. Single-operator
chains (`A and B and C`, or `A or B or C`) do not trigger the prompt
because associativity makes the parse unambiguous to read.

## Limitations at a glance

- **Homogeneous lists only.** All numbers, all text, or all records.
- **No negative numbers.** All literals are zero or positive.
- **Range cap.** `gather` produces at most 10,000 items.
- **Ascending ranges only.** `from` must be less than or equal to `to`.
- **No `transform`, `compare`.** Reserved-word slots protected; no
  grammar yet.
- **Single-level `of` only.** `field-a of field-b of record` is a
  parse error; nested records don't exist yet.
- **List operations only.** `keep`/`filter` operate on lists.
  `each ... keep where ...` is rejected (the error suggests the
  list-level alternative).
- **`choose` inside `each` is deferred** (v2d §102). The error points
  at `keep` as the list-level alternative.
- **One composition parameter, names-only.** v2d compositions take
  one declared parameter (`from <param>`) passed by name (`from
  <name>`); multiple parameters and literal arguments aren't
  supported.
- **`when` is top-level only.** It can't appear inside compositions,
  `each` bodies, or another `when` action block — those are parse
  errors with a specific message about top-level scope.
- **`finish` is action-block only.** `finish` in Phase 1 sequential
  code (or in a composition body called from Phase 1) is a semantic
  error.
- **`remember` on a live value inside an action block is rejected.**
  Live values are adapter-owned once Phase 2 begins. Phase 1
  initialization remains legal.
- **`filter` on a live value is rejected in all contexts.**
  `filter` is destructive; the error suggests `keep` as the
  non-destructive alternative.
- **Conservative cycle detection.** v3a §114's same-handler-twice
  guard rejects genuinely-toggling handler pairs as a runtime error.
  A more nuanced detector is deferred.

See [`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md) for
the full boundary.

## Where to go next

- [`../architecture/pipeline.md`](../architecture/pipeline.md) — how
  the interpreter turns a source line into output.
- [`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md) — the
  intentional boundaries of v1.
- [`../spec/`](../spec/) — the locked specification documents, if you
  want the authoritative source.
