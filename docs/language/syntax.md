# Inscript v1 syntax

A practical guide to writing Inscript programs. Inscript v1 is a
bounded prose language: 29 reserved words plus user-provided names and
literal values. The prose IS the program.

If you have not run the interpreter yet, start with
[`quickstart.md`](quickstart.md).

## Source files

- An Inscript source file uses the `.insc` extension and is plain
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
- Cannot be one of the 29 reserved words.

Valid: `age`, `orders`, `find-big-orders`, `order1`, `my-list`.

Invalid: `1st-order` (starts with a digit), `filter`
(reserved verb), `when` (reserved for v2).

## Verbs

There are seven verbs. Most statements begin with one.

### `remember`

Stores a value, list, record, or named composition.

**A single value:**

```
remember a number called age with 30
remember a value called greeting with hello
```

The descriptor between the article and `called` (here `number` and
`value`) is decorative — the interpreter ignores it. The type is
inferred from the value itself: `30` is a number, `hello` is text.

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

### `filter`

Reduces a list **in place** by a condition.

```
filter the orders where total is above 50
filter the orders where status is active
filter the numbers where each is above 5
```

After `filter`, the original list contains only the items that
matched. Filter produces no output on success — use `show` or `count`
afterward to inspect the result.

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

Note that `not above N` means `≤ N` — the boundary value `N` is
*kept*, not removed. This is intentional and distinct from `below N`.

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

Inside a `where` clause, `each` is a **pronoun** for the current item
being tested, not the iteration verb:

```
filter the numbers where each is above 5
```

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
that field — otherwise it stops before running:

> Error: Not every item in 'mixed-records' has a field called
> 'total'.

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

v1 does not support passing arguments to compositions, and the
composition name must stand alone — no `from` chaining yet. Both are
v2 features.

## Values

A literal value can be:

- **A number** — digits with an optional single decimal point.
  Examples: `30`, `3.14`, `100`. v1 does not support negative numbers
  or scientific notation.
- **A single-word string** — any bare word that is not a number and
  not in the reserved-word list. Examples: `red`, `active`,
  `portland`. Strings are case-folded to lowercase.

v1 does **not** support multi-word strings. A status value like
`in progress` cannot be expressed because `in` and `progress` would
tokenize as separate words. A quoting mechanism is a v2 consideration.

Vocabulary words (the 29 reserved words) cannot be used as values
either:

```
remember a list called items with filter and blue
```

> Error: The word 'filter' is a verb in Inscript and can't be used as
> a value. Try a different word.

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

## v1 limitations at a glance

- **Single-word strings only.** No quoting in v1.
- **Homogeneous lists only.** All numbers, all text, or all records.
- **No negative numbers.** All literals are zero or positive.
- **Range cap.** `gather` produces at most 10,000 items.
- **Ascending ranges only.** `from` must be less than or equal to
  `to`.
- **No event-driven execution.** `when` and `unless` are reserved but
  not executable in v1.
- **No `transform`, `choose`, `compare`.** Reserved for v2.

See [`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md) for
the full v1/v2 boundary.

## Where to go next

- [`../architecture/pipeline.md`](../architecture/pipeline.md) — how
  the interpreter turns a source line into output.
- [`../roadmap/v1-v2-boundary.md`](../roadmap/v1-v2-boundary.md) — the
  intentional boundaries of v1.
- [`../spec/`](../spec/) — the locked specification documents, if you
  want the authoritative source.
