# Reactive Patterns in Liminate

Liminate's `when` blocks register reactive handlers (v3a §107–§125).
This guide documents the common patterns and the pitfalls that come
with edge-triggered, dependency-driven evaluation. It is an education
document, not a spec change.

## 1. Handlers watch specific names

A handler fires when a value it *references* changes. If your condition
mentions `systolic`, the handler does not re-fire when `alert-level`
changes — even when both are relevant to your intent.

```liminate
when systolic is above 140
  show "warning: elevated blood pressure"
```

This handler watches `systolic`. It does not watch `heart-rate`,
`alert-level`, or anything else.

## 2. Write one handler per dependency

Don't fold separate triggers into a single handler's body using
`choose`. The handler only re-evaluates when its *watched* names
change, so an interior `choose` based on a different value won't fire
when that other value changes.

Anti-pattern:

```liminate
when systolic is above 140
  choose if alert-level is equal to critical: show "escalated" otherwise show "warning"
```

This handler fires only when `systolic` changes. If `alert-level`
flips to `critical` while `systolic` stays the same, nothing happens.

Better — split into two handlers, each watching the names it needs:

```liminate
when systolic is above 140
  show "warning: elevated blood pressure"

when alert-level is equal to critical and systolic is above 140
  show "escalated to critical"
```

The second handler watches both `alert-level` and `systolic`, so it
fires when either crosses its threshold.

## 3. Cascading triggers are depth-first

When handler A's action modifies a value that handler B watches, B
fires immediately — before any sibling handlers from the original
event are evaluated (§114). A cascaded handler gets its complete turn
(action block plus its own cascades) before control returns.

Plan cascade chains so the order matches your intent. The healthcare
dogfood program uses this on purpose: a blood-pressure handler raises
`alert-level`, and a separate handler watches `alert-level` to do the
escalation. Reading the source top-to-bottom shows the cause-and-
effect chain.

## 4. Edge triggering means "transition, not state"

A handler fires on the false→true *transition* of its compound
eligibility. A condition that is already true and stays true does not
fire again (§113). A value that arrives unchanged is silently
absorbed.

If you need to react to *every* update regardless of state change, use
a dedicated trigger value the adapter increments on each push:

```liminate
when update-count is above 0
  show "new reading received"
```

The condition stays true after the first update, so this still only
fires once. To fire on every update, the handler needs the
*transition* — reset `update-count` back to 0 in another handler, or
use a different reactive shape entirely (e.g., react to specific
threshold crossings rather than every reading).

## 5. `finish` is immediate and total

Once `finish` executes, nothing else runs (§112). Remaining statements
in the current action block, pending cascades, sibling handlers, and
queued adapter updates are all skipped. Put `finish` at the end of an
action block — or inside a `choose` branch whose condition is the
program's terminating event:

```liminate
when score is above 100
  show "VICTORY"
  finish
```

```liminate
when status is equal to fatal
  choose if confirmation is equal to acknowledged: finish otherwise show "awaiting acknowledgment"
```

In the second example, `finish` only runs when the `if` branch is
taken. The `otherwise` branch keeps the listener alive.

## Reference programs

See `examples/dogfood_v3a_healthcare.limn`,
`examples/dogfood_v3a_smart_home.limn`, and
`examples/dogfood_v3a_game.limn` for complete reactive programs that
exercise these patterns end-to-end against scripted domain packs.
