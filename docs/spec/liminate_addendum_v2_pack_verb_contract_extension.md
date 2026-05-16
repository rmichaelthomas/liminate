# ADDENDUM
## Liminate Programming Language — Pack Verb Contract Extension
### v2 — Execution Types, Positional Slots, and Value Type Declarations

**Status:** LOCKED — EXTENDS `liminate_addendum_v1_add_verb.md` (May 16, 2026)
**Date:** May 16, 2026
**Author:** Rob Thomas / R. Michael Thomas (architect) and Claude (analytical partner)
**Document type:** Addendum — extends the pack verb contract (v4a §137) with four new execution types, positional (connective-less) slot support, per-slot value type declarations, a discriminated execution class union, and load-time validation. Resolves open question V4-Q1 (execution types beyond `set_value`) and partially resolves V4-Q2 (connective reuse — positional slot constraint). Does not modify the base vocabulary, the base verb set, or any prior locked decision. The 35-word base vocabulary is unchanged.
**Domain prefix:** `liminate` (provisional, pre-vault — fourth document in the `liminate_*` chain)
**Relationship to prior checkpoints:** Extends `liminate_addendum_v1_add_verb.md` (May 16, 2026) as the language specification chain endpoint. Downstream of `liminate_inception_checkpoint_v1_session_contracts_and_semantic_continuity.md` (May 16, 2026), which identified `cite` and `verify` as verbs needing execution types beyond `set_value` and positional slot support. Downstream of the session-contracts benchmark checkpoint (`CHECKPOINT_v1.md`, May 16, 2026), which identified the structural blocker: the v4a §137 contract cannot express verbs with direct-object slots or constraining execution semantics. Section numbering is independent of the Inscript chain's § sequence and independent of the other `liminate_*` documents.

> *"Cite 'Newton was born in 1643' from source-doc."*
> *The interpreter checks. Not the model.*

---

## HOW TO READ THIS DOCUMENT

- §1–§3 specify prerequisites: positional slots, slot value type declarations, and load-time validation rules.
- §4–§7 specify the four new execution types: `substring_check`, `append_to_list`, `set_field`, `compare_values`.
- §8 specifies the target/source resolution model for write-target execution types.
- §9 specifies the discriminated execution class union that replaces the flat `PackVerbExecution` dataclass.
- §10 specifies the implementation shape: changes to `vocabulary.py`, `adapter.py`, `parser.py`, `analyzer.py`, `interpreter.py`.
- §11 provides JSON schema reference for all five execution types (including the existing `set_value`).
- **WHAT IS LOCKED** / **WHAT IS NOT LOCKED** collect decisions.
- The resume prompt closes the document.
- The BUILD follows this addendum. No implementation was performed during this design session.

---

## Part I — Prerequisites

### §1 — POSITIONAL (CONNECTIVE-LESS) SLOTS

**Decision: Pack verb slots may declare `connective: null` to indicate a positional slot — a direct-object slot filled by the first value token after the verb, before any connective-introduced slots. At most one positional slot per verb. Must be the first slot in the signature. LOCKED as v2 positional slot support.**

**Why this is needed.** The v4a §137 contract requires every slot to have a connective word that introduces it. This prevents verbs with a `<verb> <direct-object> <connective> <argument>` shape — the natural English pattern for verbs like `cite <text> from <source>` and `verify <claim> from <source>`. The session-contracts benchmark checkpoint (gap h) identifies this as "the same gap that blocked the Möbius DSL convergence" and "the next-most-important fix to the language, full stop."

**Constraint: one positional slot, first position.** This mirrors how base verbs handle direct objects. `add <item> to <list>` — the item is positional, the list follows a connective. `gather <name> from <number> to <number>` — the name is positional, the range endpoints follow connectives. Natural English takes at most one direct object before prepositional phrases introduce the rest. The constraint is enforced at pack load time (§3).

**Updated `PackVerbSlot` dataclass:**

```python
@dataclass(frozen=True)
class PackVerbSlot:
    name: str
    connective: str | None       # None = positional (direct object)
    required: bool
    type_constraint: str | None = None
    value_type: str = "name"     # see §2
```

**Parser handling.** In `_parse_pack_verb`, for each slot:
- If `slot.connective is None` (positional): consume the next value token directly. If `slot.value_type == "value"`, call `_parse_value(stream)`. If `slot.value_type == "name"`, consume a single UNKNOWN token as NameRef (current behavior for all slots).
- If `slot.connective is not None` (connective-introduced): peek for the connective. If found, consume it, then consume the value per `slot.value_type`. If not found and the slot is required, error. If not found and the slot is optional, skip.

**Error wording for missing positional slot:** `"'<verb>' needs <slot-role> — try: <verb> <example> <connective> <target>."` The parser constructs the example from the verb's full slot signature. For `cite` with a missing text slot: `"'cite' needs a text value — try: cite \"<text>\" from <source-name>."`

---

### §2 — SLOT VALUE TYPE DECLARATIONS

**Decision: Each `PackVerbSlot` declares a `value_type` field specifying what token types the parser accepts for that slot. Two options: `"name"` (UNKNOWN token only, producing NameRef — current behavior, the default) and `"value"` (any value type via `_parse_value` — NUMBER, UNKNOWN, QUOTED_STRING, FieldAccessNode). This applies to both positional and connective-introduced slots. LOCKED as v2 slot value type declarations.**

**Why this is needed.** `cite <text> from <source>` requires the `text` slot to accept a QuotedString. The current parser rejects QuotedString in all pack verb slots with `"Names can't have spaces."` The `value_type` field gives pack authors control over what their slots accept, matching how base verbs have slot-specific value-type rules (the `add` verb's item slot accepts any value via `_parse_value`, while its target slot accepts UNKNOWN only via `_consume_target`).

**Why two options are sufficient.** `"name"` covers every slot that references a named symbol (navigation targets, record references, list targets). `"value"` covers every slot that accepts inline content (quoted text, numbers, field access expressions, bare words). Finer granularity (`"number"`, `"text"`) is a parser-level restriction that can be expressed instead as an analyzer-level type constraint — the analyzer already validates types against the symbol table. Two value-type modes × the existing `type_constraint` mechanism covers all documented use cases without adding parser complexity.

**Default.** `value_type` defaults to `"name"`. Existing pack JSON files without a `value_type` field on their slots get the current behavior. This is not backward compatibility — it is a sensible default. Most slots reference names.

---

### §3 — LOAD-TIME VALIDATION

**Decision: `parse_pack_verb_signature` in `adapter.py` validates pack verb signatures at JSON load time. Five rules. LOCKED as v2 load-time validation.**

| Rule | What is rejected | Error message |
|---|---|---|
| 1 | More than one positional slot (connective is None) | "Pack verb '<verb>' has multiple positional slots. Only one direct-object slot is allowed, and it must be first." |
| 2 | Positional slot not in first position | "Pack verb '<verb>' has a positional slot at position <n>. The positional slot must be the first slot in the signature." |
| 3 | Two required slots sharing the same connective | "Pack verb '<verb>' has two slots using the connective '<conn>'. Each slot needs a unique connective." |
| 4 | Unknown `value_type` value | "Pack verb '<verb>' slot '<slot>' has unknown value_type '<vt>'. Use 'name' or 'value'." |
| 5 | Unknown execution type | "Pack verb '<verb>' uses unknown execution type '<type>'. Supported: set_value, substring_check, append_to_list, set_field, compare_values." |

Validation runs once at pack load time. A pack that fails validation does not activate — none of its vocabulary, nouns, or verbs enter the active tables. The error propagates to the CLI as a load failure.

---

## Part II — Execution Types

### §4 — `substring_check`

**Decision: `substring_check` is a new execution type that verifies text containment. The interpreter resolves two slot values, checks if the `check_slot` value is a substring of the `against_slot` value, and raises a runtime error if not. No value is stored. LOCKED as v2 execution type.**

**Semantics.** The check is case-sensitive. The interpreter coerces the `check_slot` value to its string representation via `_format_scalar` (the same function used by `show` for display output) before performing the `in` check. The `against_slot` value must be a string — the analyzer validates this at analysis time.

**Why case-sensitive.** The point of `cite` is verifiable provenance. If the source says "Newton" and the contract says "newton", that's a mismatch worth surfacing. Case-insensitive matching weakens the verification guarantee. The session-contracts benchmark checkpoint's core complaint is that the contract should constrain, not accommodate.

**Error message format.** On failure: `"The text '<check-value>' was not found in '<against-name>'. The source begins: '<first-80-chars>...'"`. The source content is truncated at 80 characters to avoid flooding output. The check value is shown in full (it is typically a short phrase in a `cite` call).

**Analyzer validation.** When `_check_pack_verb` encounters a verb whose execution is `SubstringCheckExecution`:
1. The `against_slot` must resolve to a name in the symbol table.
2. The symbol must be of type `"string"`. If not: `"'cite from' expects text, but '<name>' is <type>."`.
3. The `check_slot` must resolve to a valid expression (NameRef exists in symtab; QuotedString/NumberLiteral/FieldAccessNode trivially valid).

**Execution class:**

```python
@dataclass(frozen=True)
class SubstringCheckExecution:
    check_slot: str
    against_slot: str
```

**JSON schema:**

```json
{
  "type": "substring_check",
  "check_slot": "text",
  "against_slot": "source"
}
```

---

### §5 — `append_to_list`

**Decision: `append_to_list` is a new execution type that appends a resolved slot value to a named list in the symbol table. The item is deep-copied. No output is returned. LOCKED as v2 execution type.**

**Semantics.** Identical to the base `add` verb's interpreter behavior (`entry.value.append(copy.deepcopy(item_value))`), but driven by the pack verb's execution definition rather than a hardcoded AST node handler. This is the pack-verb equivalent of what `add` does as a base verb — domain-specific accumulation verbs (game pack `reveal`, healthcare pack `prescribe`) can use it without touching the base vocabulary.

**Analyzer validation.** The same five checks that `_check_add` performs, factored into a shared helper `_check_list_append(target_name, item_node, symtab, iterator, live_value_names)`:

1. **Live-value restriction.** If the target name is in `live_value_names`: rejected. Error: `"'<name>' is a live value provided by the domain pack. '<verb>' modifies the list and can't be used on it — the domain pack controls this value."`.
2. **Target exists and is a list.** Reuses `_require_list`.
3. **Item validation.** NameRef must exist; FieldAccessNode checked; literals trivially valid.
4. **Type compatibility.** Same-category check. The `none` polymorphic seed pattern from the `add` verb (v1 §7) applies.
5. **Self-mutation guard inside `each`.** If iterating the target list: rejected.

**Execution class** (see §8 for target/source resolution model):

```python
@dataclass(frozen=True)
class AppendToListExecution:
    target_name: str | None = None
    target_slot: str | None = None
    source_slot: str | None = None
    literal_value: str | None = None
```

**JSON schema:**

```json
{
  "type": "append_to_list",
  "target_name": "visible-items",
  "source_slot": "item"
}
```

---

### §6 — `set_field`

**Decision: `set_field` is a new execution type that sets a single field on an existing record in the symbol table. If the field does not exist, it is created (consistent with v4a §136 freeform overflow). The record's `schema` dict is updated. No output is returned. LOCKED as v2 execution type.**

**Semantics.** The interpreter resolves the target symbol, verifies it is a record, resolves the source slot value, and sets `entry.value[field_name] = copy.deepcopy(resolved_value)`. The `schema` dict on the `SymbolEntry` is updated: `entry.schema[field_name] = _scalar_type(resolved_value)`. This keeps the analyzer's field-existence checks consistent for subsequent operations — if `set_field` creates `device.status`, then `show status of device` works on the next line.

**Field creation.** When the field does not already exist on the record, it is created. This is consistent with how records work at definition time — `remember a button called submit with label as "Save" and color as blue` stores `color` even if it is not in the predefined schema (v4a §136 freeform overflow). The same principle applies post-creation: records can grow.

**Live-value model.** Pack verbs follow the same model as `set_value` — pack-defined verbs may mutate symbols including pack-owned symbols. The live-value restriction (`_check_live_value_remember`) applies to user-authored `remember`, `filter`, and `add` statements, not to pack verb execution. This is consistent with the existing code: `_exec_pack_verb` with `set_value` calls `_store(symtab, target_name, value)` directly, with no live-value check. `set_field` follows the same path.

**Analyzer validation.** When `_check_pack_verb` encounters a verb whose execution is `SetFieldExecution`:
1. The `target_name` must exist in the symbol table.
2. The symbol must be of type `"record"`. If not: `"'<verb>' expects a record, but '<name>' is <type>."`.
3. The `source_slot` must resolve to a valid expression.

No field-existence check at analysis time — `set_field` is permitted to create fields. When `target_slot` is used instead of `target_name`, the analyzer resolves the slot value's name and checks that symbol.

**Execution class** (see §8 for target/source resolution model):

```python
@dataclass(frozen=True)
class SetFieldExecution:
    field_name: str
    target_name: str | None = None
    target_slot: str | None = None
    source_slot: str | None = None
    literal_value: str | None = None
```

**JSON schema:**

```json
{
  "type": "set_field",
  "target_slot": "target",
  "field_name": "status",
  "literal_value": "active"
}
```

---

### §7 — `compare_values`

**Decision: `compare_values` is a new execution type that compares two slot values and stores the result. Two comparison modes: `"equality"` (binary match/mismatch) and `"structural"` (field-level diff for records, element-level for lists, equality for scalars). Two mismatch behaviors: `"error"` (runtime error) and `"flag"` (store result). LOCKED as v2 execution type.**

**Equality mode.** The interpreter resolves two slot values and performs deep equality comparison. Stores a string in `status_target`: `"match"` or `"mismatch"`. `details_target` is not used.

**Structural mode.** The interpreter resolves two slot values and compares them by type:

| Left/right type | Status stored | Details stored in `details_target` |
|---|---|---|
| Both records | `"match"` or `"mismatch"` | List of field names (strings) that differ. Includes fields present in one record but absent from the other. |
| Both lists, same length | `"match"` or `"mismatch"` | List of indices (numbers) where elements differ. |
| Both lists, different length | `"length_mismatch"` | Empty list. |
| Both scalars | `"match"` or `"mismatch"` | Empty list. |
| Type mismatch (e.g. record vs number) | `"type_mismatch"` | Empty list. |

`details_target` is required when `comparison` is `"structural"`. The interpreter stores a list of strings (for record field diffs) or a list of numbers (for list index diffs) or an empty list. The program can then `count`, `each`, or `filter` the details.

**`on_mismatch: "error"` behavior.** When the comparison finds a mismatch and `on_mismatch` is `"error"`:
- Equality mode: `"'<left-name>' does not match '<right-name>'."`.
- Structural mode on records: `"'<left-name>' and '<right-name>' diverge on fields: '<field1>', '<field2>'."`.
- Structural mode on lists: `"'<left-name>' and '<right-name>' differ at positions: <idx1>, <idx2>."`.

**`on_mismatch: "flag"` behavior.** The comparison stores its result in `status_target` (and `details_target` for structural mode). No error is raised. The program reads the result via `when` handlers or `choose` branches.

**Analyzer validation.** When `_check_pack_verb` encounters a verb whose execution is `CompareValuesExecution`:
1. Both `left_slot` and `right_slot` must resolve to names in the symbol table.
2. `comparison` must be `"equality"` or `"structural"`. Other values rejected at load time (§3 rule 5 extended).
3. `on_mismatch` must be `"error"` or `"flag"`. Other values rejected at load time.
4. If `comparison` is `"structural"` and `details_target` is None, load-time validation rejects: `"Structural comparison requires a 'details_target' field."`.

**Execution class:**

```python
@dataclass(frozen=True)
class CompareValuesExecution:
    left_slot: str
    right_slot: str
    comparison: str         # "equality" | "structural"
    on_mismatch: str        # "error" | "flag"
    status_target: str
    details_target: str | None  # required for "structural", None for "equality"
```

**JSON schema:**

```json
{
  "type": "compare_values",
  "left_slot": "claim",
  "right_slot": "canonical",
  "comparison": "structural",
  "on_mismatch": "flag",
  "status_target": "drift-status",
  "details_target": "divergent-fields"
}
```

---

## Part III — Resolution Model and Execution Architecture

### §8 — TARGET AND SOURCE RESOLUTION MODEL

**Decision: All three write-target execution types (`set_value`, `append_to_list`, `set_field`) support two resolution modes for both their target and their source. Targets can be literal symbol names or slot-derived. Sources can be slot-derived values or literal values. Each pair is mutually exclusive: exactly one of the two fields must be non-None. LOCKED as v2 target/source resolution model.**

**Why this is needed.** The v4a `set_value` execution has `target_name` (a literal symbol name in JSON) and `source_slot` (a slot reference). This works for `navigate to settings` — the target is always `"current-screen"` and the source name comes from the slot. But it breaks for two real patterns:

1. **Slot-derived targets.** `activate thermostat` needs to modify the record at `symtab["thermostat"]` — the symbol name comes from what the user typed, not from a fixed JSON string. The JSON can't know in advance which device the user will name.

2. **Literal source values.** `activate thermostat` needs to set `device.status` to `"active"` — a fixed value, not from any slot. No slot in `activate <device>` carries the string `"active"`.

**The resolution model.** Two fields per dimension, exactly one non-None:

| Dimension | Slot-derived field | Literal field | What the interpreter does |
|---|---|---|---|
| **Target** (where to write) | `target_slot: str \| None` | `target_name: str \| None` | Slot-derived: resolve the slot value's name as the symbol to modify. Literal: use the fixed string as the symbol name. |
| **Source** (what to write) | `source_slot: str \| None` | `literal_value: str \| None` | Slot-derived: resolve the slot value via `_evaluate_expression`. Literal: use the fixed string as the value. |

**Interpreter resolution logic (shared helper):**

```python
def _resolve_target(execution, node, symtab) -> str:
    """Return the symbol name to write to."""
    if execution.target_slot is not None:
        value_node = node.slot_values.get(execution.target_slot)
        if isinstance(value_node, NameRef):
            return value_node.name
        if isinstance(value_node, BareWord):
            return value_node.word
        raise _RuntimeError(
            f"Pack verb '{node.word}' needs a name for its target, "
            f"not a literal value."
        )
    return execution.target_name

def _resolve_source(execution, node, symtab) -> Any:
    """Return the value to write."""
    if execution.source_slot is not None:
        value_node = node.slot_values.get(execution.source_slot)
        return _evaluate_expression(value_node, symtab, None)
    return execution.literal_value
```

**Note on `set_value` backward behavior.** The current `set_value` interpreter has a special case: when the source slot resolves to a NameRef, it stores the *name string* (e.g., `"settings"`) not the *value* of that symbol. This is correct for `navigate to settings` — you want to store the screen name, not the screen record's contents. The resolution model preserves this behavior: `_exec_pack_set_value` continues to use its existing name-vs-value logic for `source_slot`. The shared `_resolve_source` helper is used by `append_to_list` and `set_field`, which want the value, not the name.

**Load-time validation (extends §3):**

| Rule | What is rejected | Error message |
|---|---|---|
| 6 | Both `target_name` and `target_slot` are non-None | "Pack verb '<verb>' specifies both target_name and target_slot. Use one or the other." |
| 7 | Both `target_name` and `target_slot` are None (on types that write) | "Pack verb '<verb>' needs either target_name or target_slot." |
| 8 | Both `source_slot` and `literal_value` are non-None | "Pack verb '<verb>' specifies both source_slot and literal_value. Use one or the other." |
| 9 | Both `source_slot` and `literal_value` are None (on types that write) | "Pack verb '<verb>' needs either source_slot or literal_value." |

Rules 6–9 apply to `set_value`, `append_to_list`, and `set_field`. They do not apply to `substring_check` or `compare_values` (which are read-only).

**Which execution types use which dimensions:**

| Execution type | Uses target resolution | Uses source resolution |
|---|---|---|
| `set_value` | Yes — where to store | Yes — what to store (with name-vs-value special case) |
| `append_to_list` | Yes — which list to append to | Yes — what to append |
| `set_field` | Yes — which record to modify | Yes — what to set the field to |
| `substring_check` | No | No |
| `compare_values` | No (uses `status_target` / `details_target` directly) | No |

---

### §9 — EXECUTION CLASS ARCHITECTURE

**Decision: The flat `PackVerbExecution` dataclass is replaced by a discriminated union of five frozen dataclasses, one per execution type. The interpreter dispatches with `isinstance`. The JSON `type` field is consumed only by the factory function in `adapter.py`. LOCKED as v2 execution architecture.**

**Why discriminated, not flat.** Each execution type has different required fields. A flat dataclass with all fields optional means accessing `field_name` on a `SubstringCheckExecution` returns `None` silently — a type error at runtime, not at write time. Discriminated classes make each type's required fields explicit. The interpreter already dispatches AST nodes with `isinstance` (`isinstance(node, AddNode)`, `isinstance(node, PackVerbNode)`, etc.) — execution dispatch follows the same pattern.

**Full class definitions:**

```python
@dataclass(frozen=True)
class SetValueExecution:
    target_name: str | None = None      # literal symbol name to store into
    target_slot: str | None = None      # resolve symbol name from this slot
    source_slot: str | None = None      # resolve value from this slot (name-vs-value special case)
    literal_value: str | None = None    # use this literal value

@dataclass(frozen=True)
class SubstringCheckExecution:
    check_slot: str
    against_slot: str

@dataclass(frozen=True)
class AppendToListExecution:
    target_name: str | None = None      # literal list name to append to
    target_slot: str | None = None      # resolve list name from this slot
    source_slot: str | None = None      # resolve item value from this slot
    literal_value: str | None = None    # use this literal value as item

@dataclass(frozen=True)
class SetFieldExecution:
    field_name: str
    target_name: str | None = None      # literal record name to modify
    target_slot: str | None = None      # resolve record name from this slot
    source_slot: str | None = None      # resolve field value from this slot
    literal_value: str | None = None    # use this literal value as field value

@dataclass(frozen=True)
class CompareValuesExecution:
    left_slot: str
    right_slot: str
    comparison: str         # "equality" | "structural"
    on_mismatch: str        # "error" | "flag"
    status_target: str
    details_target: str | None  # required for "structural"

PackVerbExecution = (
    SetValueExecution
    | SubstringCheckExecution
    | AppendToListExecution
    | SetFieldExecution
    | CompareValuesExecution
)
```

**Location.** All five classes and the union type alias live in `vocabulary.py`, replacing the existing `PackVerbExecution` dataclass. `PackVerbSignature.execution` uses the union type.

**Factory function.** `parse_pack_verb_signature` in `adapter.py` reads the `type` field from JSON and constructs the appropriate class:

```python
def _parse_execution(exec_def: dict) -> PackVerbExecution:
    exec_type = exec_def.get("type", "")
    if exec_type == "set_value":
        return SetValueExecution(
            target_name=exec_def.get("target_name"),
            target_slot=exec_def.get("target_slot"),
            source_slot=exec_def.get("source_slot"),
            literal_value=exec_def.get("literal_value"),
        )
    if exec_type == "substring_check":
        return SubstringCheckExecution(
            check_slot=exec_def["check_slot"],
            against_slot=exec_def["against_slot"],
        )
    if exec_type == "append_to_list":
        return AppendToListExecution(
            target_name=exec_def.get("target_name"),
            target_slot=exec_def.get("target_slot"),
            source_slot=exec_def.get("source_slot"),
            literal_value=exec_def.get("literal_value"),
        )
    if exec_type == "set_field":
        return SetFieldExecution(
            field_name=exec_def["field_name"],
            target_name=exec_def.get("target_name"),
            target_slot=exec_def.get("target_slot"),
            source_slot=exec_def.get("source_slot"),
            literal_value=exec_def.get("literal_value"),
        )
    if exec_type == "compare_values":
        return CompareValuesExecution(
            left_slot=exec_def["left_slot"],
            right_slot=exec_def["right_slot"],
            comparison=exec_def["comparison"],
            on_mismatch=exec_def["on_mismatch"],
            status_target=exec_def["status_target"],
            details_target=exec_def.get("details_target"),
        )
    raise ValueError(
        f"Unknown execution type '{exec_type}'. "
        f"Supported: set_value, substring_check, append_to_list, "
        f"set_field, compare_values."
    )
```

**Interpreter dispatch.** `_exec_pack_verb` in `interpreter.py` replaces the string-based `if execution.type == "set_value"` with `isinstance` dispatch:

```python
def _exec_pack_verb(node: PackVerbNode, symtab):
    execution = node.signature.execution
    if isinstance(execution, SetValueExecution):
        return _exec_pack_set_value(node, execution, symtab)
    if isinstance(execution, SubstringCheckExecution):
        return _exec_pack_substring_check(node, execution, symtab)
    if isinstance(execution, AppendToListExecution):
        return _exec_pack_append_to_list(node, execution, symtab)
    if isinstance(execution, SetFieldExecution):
        return _exec_pack_set_field(node, execution, symtab)
    if isinstance(execution, CompareValuesExecution):
        return _exec_pack_compare_values(node, execution, symtab)
    raise _RuntimeError(
        f"Pack verb '{node.word}' has an unrecognized execution type."
    )
```

---

## Part IV — Implementation Specification

### §10 — FILE-BY-FILE CHANGES

**`vocabulary.py`**

| Change | Detail |
|---|---|
| Replace `PackVerbExecution` | Five frozen dataclasses + `PackVerbExecution` union type alias (§8). |
| Update `PackVerbSlot` | `connective: str` → `connective: str \| None`. Add `value_type: str = "name"`. |
| No other changes | `VERBS`, `CONNECTIVES`, `ALL_RESERVED`, `VERB_SIGNATURES` untouched. Base vocabulary stays at 35. |

**`adapter.py`**

| Change | Detail |
|---|---|
| Replace `parse_pack_verb_signature` | Factor execution parsing into `_parse_execution(exec_def)` (§8). Update slot parsing to accept `connective: null` from JSON and `value_type` from JSON (default `"name"`). |
| Add `_validate_pack_verb_signature` | Five load-time validation rules (§3). Called from `parse_pack_verb_signature` after construction. |
| Update imports | Import the five execution classes from `vocabulary.py`. |

**`parser.py`**

| Change | Detail |
|---|---|
| Update `_parse_pack_verb` | For each slot: check `slot.connective`. If `None` (positional), consume value directly per `slot.value_type`. If `str`, peek for connective, then consume value per `slot.value_type`. If `slot.value_type == "value"`, call `_parse_value(stream)`. If `slot.value_type == "name"`, use current UNKNOWN-only path. |
| Update `PackVerbNode` imports | No change to `PackVerbNode` itself — slot values are already `dict[str, ASTNode]`, which accommodates all value types. |

**`analyzer.py`**

| Change | Detail |
|---|---|
| Extend `_check_pack_verb` | After existing type-constraint checks, dispatch on `isinstance(execution, ...)` for execution-specific validation: `SubstringCheckExecution` checks `against_slot` resolves to a string; `AppendToListExecution` calls `_check_list_append`; `SetFieldExecution` checks target is a record; `CompareValuesExecution` checks both slots resolve. |
| Factor `_check_list_append` | Extract the five checks from `_check_add` into `_check_list_append(target_name, item_node, symtab, iterator, live_value_names)`. Call from both `_check_add` and the `AppendToListExecution` branch. |
| Update imports | Import the five execution classes from `vocabulary.py`. |

**`interpreter.py`**

| Change | Detail |
|---|---|
| Replace `_exec_pack_verb` | `isinstance` dispatch to five handler functions (§9). |
| `_resolve_target` | Shared helper (§8). Resolves `target_slot` or returns `target_name`. |
| `_resolve_source` | Shared helper (§8). Resolves `source_slot` via `_evaluate_expression` or returns `literal_value`. |
| `_exec_pack_set_value` | Extracted from current `_exec_pack_verb`. Uses `_resolve_target`. Preserves existing name-vs-value special case for `source_slot`. |
| `_exec_pack_substring_check` | Resolve `check_slot` value, coerce to string via `_format_scalar`. Resolve `against_slot` value. `if check_value not in against_value: raise _RuntimeError(...)`. Return `[]`. |
| `_exec_pack_append_to_list` | Uses `_resolve_target` and `_resolve_source`. `entry.value.append(copy.deepcopy(resolved_value))`. Return `[]`. |
| `_exec_pack_set_field` | Uses `_resolve_target` and `_resolve_source`. `entry.value[field_name] = copy.deepcopy(resolved_value)`. `entry.schema[field_name] = _scalar_type(resolved_value)`. Return `[]`. |
| `_exec_pack_compare_values` | Resolve both slots. Dispatch on `execution.comparison`: equality branch does `left == right`; structural branch does per-type diff. Store results in `status_target` (and `details_target` for structural). If `on_mismatch == "error"` and mismatched, raise `_RuntimeError`. Return `[]`. |
| Update imports | Import the five execution classes from `vocabulary.py`. |

**`renderer.py`**

No changes. Pack verbs already render via the existing `PackVerbNode` case in `render()`. The canonical form is `<verb> <positional-value> <connective> <slot-value>`, which the renderer constructs from `node.word`, `node.signature.slots`, and `node.slot_values`. Positional slots (connective is None) render without a preceding connective word.

---

## Part VI — JSON Schema Reference

### §11 — COMPLETE PACK VERB JSON SCHEMA

**Slot definition:**

```json
{
  "name": "<slot-name>",
  "connective": "<connective-word>" | null,
  "required": true | false,
  "type_constraint": "<descriptor-or-type>" | null,
  "value_type": "name" | "value"
}
```

| Field | Required | Default | Meaning |
|---|---|---|---|
| `name` | Yes | — | Slot's internal name (error messages, execution references) |
| `connective` | Yes | — | Connective that introduces this slot. `null` = positional. |
| `required` | Yes | — | Whether the slot must be filled. |
| `type_constraint` | No | `null` | Descriptor the slot's resolved value must match. |
| `value_type` | No | `"name"` | `"name"` = UNKNOWN token only. `"value"` = any value type. |

**Execution definitions by type:**

**`set_value`** (v4a, extended with resolution model):

```json
{
  "type": "set_value",
  "target_name": "<literal-symbol-name>" | null,
  "target_slot": "<slot-name-to-resolve>" | null,
  "source_slot": "<slot-name-to-resolve>" | null,
  "literal_value": "<fixed-value>" | null
}
```

Exactly one of `target_name`/`target_slot` must be non-null. Exactly one of `source_slot`/`literal_value` must be non-null. The existing `pack_ui.json` uses `target_name` + `source_slot` (the common case).

**`substring_check`** (v2, new):

```json
{
  "type": "substring_check",
  "check_slot": "<slot-with-text-to-find>",
  "against_slot": "<slot-with-source-text>"
}
```

**`append_to_list`** (v2, new):

```json
{
  "type": "append_to_list",
  "target_name": "<literal-list-name>" | null,
  "target_slot": "<slot-name-to-resolve>" | null,
  "source_slot": "<slot-name-to-resolve>" | null,
  "literal_value": "<fixed-value>" | null
}
```

Exactly one of `target_name`/`target_slot` must be non-null. Exactly one of `source_slot`/`literal_value` must be non-null.

**`set_field`** (v2, new):

```json
{
  "type": "set_field",
  "field_name": "<field-to-set>",
  "target_name": "<literal-record-name>" | null,
  "target_slot": "<slot-name-to-resolve>" | null,
  "source_slot": "<slot-name-to-resolve>" | null,
  "literal_value": "<fixed-value>" | null
}
```

Exactly one of `target_name`/`target_slot` must be non-null. Exactly one of `source_slot`/`literal_value` must be non-null.

**`compare_values`** (v2, new):

```json
{
  "type": "compare_values",
  "left_slot": "<slot-name>",
  "right_slot": "<slot-name>",
  "comparison": "equality" | "structural",
  "on_mismatch": "error" | "flag",
  "status_target": "<symbol-for-status-string>",
  "details_target": "<symbol-for-divergence-list>" | null
}
```

**Example: `cite` verb for the session pack:**

```json
{
  "word": "cite",
  "slots": [
    { "name": "text", "connective": null, "required": true, "value_type": "value" },
    { "name": "source", "connective": "from", "required": true, "value_type": "name" }
  ],
  "execution": {
    "type": "substring_check",
    "check_slot": "text",
    "against_slot": "source"
  }
}
```

**Example: `verify` verb for the session pack:**

```json
{
  "word": "verify",
  "slots": [
    { "name": "claim", "connective": null, "required": true, "value_type": "name" },
    { "name": "source", "connective": "from", "required": true, "value_type": "name" }
  ],
  "execution": {
    "type": "compare_values",
    "left_slot": "claim",
    "right_slot": "source",
    "comparison": "structural",
    "on_mismatch": "flag",
    "status_target": "verification-status",
    "details_target": "verification-divergences"
  }
}
```

**Example: `reveal` verb for a game pack:**

```json
{
  "word": "reveal",
  "slots": [
    { "name": "item", "connective": null, "required": true, "value_type": "name" },
    { "name": "player", "connective": "to", "required": true, "value_type": "name" }
  ],
  "execution": {
    "type": "append_to_list",
    "target_name": "visible-items",
    "source_slot": "item"
  }
}
```

**Example: `activate` verb for a home pack:**

```json
{
  "word": "activate",
  "slots": [
    { "name": "target", "connective": null, "required": true, "value_type": "name" }
  ],
  "execution": {
    "type": "set_field",
    "target_slot": "target",
    "field_name": "status",
    "literal_value": "active"
  }
}
```

`activate thermostat` → the interpreter resolves `target_slot: "target"` to the name `"thermostat"`, looks up `symtab["thermostat"]`, sets `entry.value["status"] = "active"`, and updates `entry.schema["status"] = "string"`.

**Example: `assign` verb using slot-derived target with `set_value`:**

```json
{
  "word": "assign",
  "slots": [
    { "name": "value", "connective": null, "required": true, "value_type": "value" },
    { "name": "target", "connective": "to", "required": true, "value_type": "name" }
  ],
  "execution": {
    "type": "set_value",
    "target_slot": "target",
    "source_slot": "value"
  }
}
```

`assign 42 to score` → the interpreter resolves `target_slot: "target"` to `"score"`, resolves `source_slot: "value"` to `42`, stores `42` into `symtab["score"]`.

---

## WHAT IS LOCKED

This addendum locks:

- **Positional (connective-less) slots** (§1). `connective: null` on `PackVerbSlot`. One per verb, first position, enforced at load time.
- **Slot value type declarations** (§2). `value_type: "name" | "value"` on `PackVerbSlot`. Default `"name"`. `"value"` routes through `_parse_value`.
- **Load-time validation** (§3). Nine rules enforced in `parse_pack_verb_signature` (five original + four resolution-model rules from §8).
- **`substring_check` execution type** (§4). Case-sensitive substring containment. Error on failure. Analyzer validates `against_slot` is a string.
- **`append_to_list` execution type** (§5). Deep-copy append. Five shared safety checks factored from `_check_add`.
- **`set_field` execution type** (§6). Single-field mutation on existing records. Creates field if absent. Updates `schema` dict.
- **`compare_values` execution type** (§7). `"equality"` and `"structural"` comparison modes. `"error"` and `"flag"` mismatch behaviors. Two output targets: `status_target` (string) and `details_target` (list).
- **Target/source resolution model** (§8). All three write-target execution types support `target_name`/`target_slot` (exactly one non-None) and `source_slot`/`literal_value` (exactly one non-None). `_resolve_target` and `_resolve_source` shared helpers. `set_value` preserves its name-vs-value special case.
- **Discriminated execution class union** (§9). Five frozen dataclasses. `isinstance` dispatch. Factory function in `adapter.py`.
- **Implementation specification** (§10). File-by-file changes to `vocabulary.py`, `adapter.py`, `parser.py`, `analyzer.py`, `interpreter.py`. `renderer.py` unchanged.
- **JSON schema** (§11). Complete schema for all five execution types with examples.

## WHAT IS NOT LOCKED

- **The build itself.** This addendum specifies; the implementation follows in a separate session.
- **Test sentences.** No test sentences are specified in this addendum. Test sentences for each execution type should be produced during the build session, following the established pattern (10+ sentences per feature, covering happy paths, type mismatches, and error cases).
- **The session domain pack JSON.** The `cite` and `verify` examples in §11 are illustrative. The actual session pack (`session_pack.json`) requires its own design session (SC-Q1 — minimum viable pack vocabulary) before the JSON is locked.
- **Open question V4-Q2** is partially resolved. Positional-slot constraints (one per verb, first position) and duplicate-connective rejection address the identified ambiguity risks. The remaining edge — a future pack verb that genuinely needs two positional slots — is not addressed because no documented use case requires it.
- **Any change to any prior locked decision.** Every decision in this addendum is additive. The base vocabulary is unchanged. Existing pack JSON files (e.g. `pack_ui.json`) continue to work with the extended schema — `target_name` + `source_slot` is still valid and remains the common case.

---

## PROVENANCE NOTE

This addendum was produced from:

- **`rmichaelthomas/liminate` repo** (May 16, 2026, direct GitHub scan via vault-local MCP): `vocabulary.py` (sha e002482 — `PackVerbSlot`, `PackVerbExecution`, `PackVerbSignature` dataclasses; 35 reserved words, 11 verbs), `parser.py` (sha a8a3f20 — `_parse_pack_verb`, `_parse_add`, `_parse_value`, `PackVerbNode` AST), `analyzer.py` (sha 871d23a — `_check_pack_verb` type-constraint validation, `_check_add` five safety checks, `_check_field_access`), `interpreter.py` (sha 9ab5a5b — `_exec_pack_verb` with `set_value` dispatch, `_exec_add`, `_store`, `_format_scalar`, `_scalar_type`), `adapter.py` (sha 0170a37 — `parse_pack_verb_signature`, `TestDomainPack`, `DomainPack` ABC, `LiveValueRegistry`), `examples/pack_ui.json` (sha d710f5a — `navigate` verb with `set_value` execution).
- **`CHECKPOINT_v1.md`** (May 16, 2026, uploaded by architect): Session-contracts benchmark checkpoint identifying gap (h) — v4a §137 cannot express connective-less direct-object slots; gap (b) — self-declared verification is theater; suggested next action #1 — `cite` verb with substring-check execution.
- **`liminate_addendum_v1_add_verb.md`** (May 16, 2026, project knowledge): Referenced for `add` verb's five analyzer checks (§10), the rationale for `add` as base verb instead of pack verb (§1 — pack contract couldn't express `append_to_list`), and the `none` polymorphic seed pattern (§7).
- **`inscript_addendum_v4a_pack_verbs_and_port.md`** (May 13, 2026, project knowledge): Referenced for the original pack verb contract (§137), `set_value` execution type, open questions V4-Q1 and V4-Q2 (§142), future-pack table (UI, Game, Healthcare, Home).
- **`liminate_inception_checkpoint_v1_session_contracts_and_semantic_continuity.md`** (May 16, 2026, project knowledge): Referenced for ChatGPT's five application categories (§9), Phase 2 pack design (§20), Phase 3 institutional memory (§21), SC-Q5 (pack verb execution types beyond `set_value`).
- **`inscript_checkpoint_v1_application_ideation.md`** (May 14, 2026, project knowledge): Referenced for Code-as-Law Parser, Receipt/journalism, Annual Tax Update Tool, and other use cases requiring verification execution semantics.
- **`inscript_checkpoint_v1_rename_and_dsl_convergence.md`** (May 15, 2026, project knowledge): Referenced for failure mode taxonomy (§10 — Modes A through E) and the Möbius DSL convergence gap (§6 gap #2 — same positional-slot blocker).
- **Conversation with architect** (May 16, 2026, this session): Three-turn design session walking through V4-Q1 and V4-Q2, deriving four execution types from documented use cases, resolving open design questions (P-1 through S-1), and architect pushback against deferrals leading to full resolution of slot value types, structural comparison mode, and discriminated execution architecture.

### NAMING VERIFICATION

Filename: `liminate_addendum_v2_pack_verb_contract_extension.md`. Verified against the naming grammar in the rmt-working-documents skill: domain `liminate` (provisional, pre-vault), class `addendum` (versioned, closes open threads), version `v2` (second addendum in the `liminate_*` chain), subtitle `pack_verb_contract_extension`. All separators are underscores.

---

## RESUME PROMPT (Liminate Pack Verb Contract Extension v2)

*We are resuming from the Liminate Pack Verb Contract Extension Addendum v2 (May 16, 2026), which extends the Inscript Programming Language specification chain (Inception Checkpoint v1 through Addendum v4a, May 11–13, 2026) and the Liminate `add` verb addendum v1 (May 16, 2026). This is the fourth `liminate_*` document in the chain.*

*v2 resolves open question V4-Q1 (execution types beyond `set_value`) and partially resolves V4-Q2 (connective reuse — positional slot constraint). It extends the pack verb contract (v4a §137) with:*

*1. **Positional slots** (§1). `PackVerbSlot.connective` can be `null`, indicating a direct-object slot filled by the first value token after the verb. One positional slot per verb, first position only, enforced at load time. This unblocks `cite <text> from <source>` and `verify <claim> from <source>`.*

*2. **Slot value type declarations** (§2). `PackVerbSlot.value_type` is `"name"` (UNKNOWN only, default) or `"value"` (any value type via `_parse_value` — NUMBER, UNKNOWN, QUOTED_STRING, FieldAccessNode). Applies to both positional and connective-introduced slots.*

*3. **Four new execution types** (§4–§7). `substring_check` (case-sensitive text containment — enables `cite`), `append_to_list` (deep-copy append — enables domain-specific accumulation verbs), `set_field` (single-field mutation on records, creates if absent), `compare_values` (equality and structural comparison with `"error"` or `"flag"` mismatch behavior, dual-target output for structural diffs).*

*4. **Target/source resolution model** (§8). All three write-target execution types (`set_value`, `append_to_list`, `set_field`) support two resolution modes for both target and source. Targets: `target_name` (literal symbol name in JSON) or `target_slot` (resolve from slot — symbol name is what the user typed). Sources: `source_slot` (resolve value from slot) or `literal_value` (fixed value in JSON). Exactly one of each pair must be non-None. `_resolve_target` and `_resolve_source` shared interpreter helpers. `set_value` preserves its existing name-vs-value special case for `source_slot`.*

*5. **Discriminated execution class union** (§9). Five frozen dataclasses (`SetValueExecution`, `SubstringCheckExecution`, `AppendToListExecution`, `SetFieldExecution`, `CompareValuesExecution`) replace the flat `PackVerbExecution`. `isinstance` dispatch in the interpreter. Factory function in `adapter.py`.*

*6. **Load-time validation** (§3 + §8). Nine rules enforced at pack load: max one positional slot (first position), no duplicate connectives on required slots, valid `value_type` values, valid execution types, exactly-one-of for target_name/target_slot pairs, exactly-one-of for source_slot/literal_value pairs.*

*Files modified: `vocabulary.py` (execution classes, updated `PackVerbSlot`), `adapter.py` (factory function, validation), `parser.py` (positional slot handling, `value_type` dispatch), `analyzer.py` (execution-specific validation, factored `_check_list_append`), `interpreter.py` (five-branch `isinstance` dispatch, `_resolve_target`, `_resolve_source`). `renderer.py` unchanged. Base vocabulary unchanged at 35 words, 11 verbs.*

*The build follows this addendum. No test sentences are specified — they should be produced during the build session. The session pack JSON (`cite`, `verify`) requires its own design session (SC-Q1) before locking. Failure modes to guard during the build: (A) project knowledge as authoritative instead of repo; (B) not reading this addendum's §10 specification before writing code; (C) modifying interpreter dispatch without checking all five execution types; (D) not running `_validate_pack_verb_signature` on existing `pack_ui.json` to confirm it still loads; (E) not testing the target/source resolution model with both modes (literal and slot-derived) for each write-target execution type.*

---

*END OF THE LIMINATE PROGRAMMING LANGUAGE PACK VERB CONTRACT EXTENSION ADDENDUM v2*

*May 16, 2026*

*The pack verb contract used to know one trick: store a value.*
*Now it can check, append, mutate, and compare.*
*The interpreter checks. Not the model.*
*Thirty-five words. Five execution types.*
*The base vocabulary is still sacred.*
