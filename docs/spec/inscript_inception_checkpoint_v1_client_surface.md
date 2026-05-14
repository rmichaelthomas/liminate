# INCEPTION CHECKPOINT
## Inscript Client Surface
### v1 — Building Möbius Clients in Prose

**Status:** INCEPTION CHECKPOINT
**Date:** May 13, 2026
**Author:** Rob Thomas / R. Michael Thomas
**Document type:** Inception checkpoint — first-version scoping for using the Inscript Programming Language to build Möbius client surfaces
**Domain prefix:** `inscript` (provisional, pre-vault; shares the domain with the Inscript Programming Language)
**Relationship to prior checkpoints:** This is a downstream project of the Inscript Programming Language. It depends on infrastructure built in `inscript_addendum_v4a_pack_verbs_and_port.md` (the UI domain pack + pack verb contract + TypeScript parser port). The Inscript Programming Language's design lineage (Narratia → Möbius Inscript → Inscript Programming Language) extends here to a sixth expression: the person must remain the author of their application's surface, not just its logic.

> *"Could someone use Inscript to build an app? Could someone write a Möbius client in it?"*

---

## HOW TO READ THIS DOCUMENT

- This inception checkpoint captures the design for three capabilities that together enable Inscript-authored Möbius client surfaces: a rendering adapter, a UI event mapping, and a proposal engine.
- None of this is built yet. The prerequisite infrastructure (UI domain pack, pack verb contract, TypeScript parser port) is specified in the companion addendum `inscript_addendum_v4a_pack_verbs_and_port.md` and must be built first.
- The decisions here were made in conversation (May 13, 2026) but are logged as inception-stage design, not locked as build commitments. They represent the architect's current thinking and will be revisited when the build is scheduled.
- Section numbering is independent of the Inscript Programming Language's § sequence. This is a separate document chain.

---

## Part I — The Generative Question

### §1 — HOW WE GOT HERE

A Reddit post about Go — "the language that finally made me stop over-engineering everything" — led to a conversation about what Inscript's website would say for "use cases." The initial framing was about domains where the translation gap is costly (business rules, compliance, data filtering). But the architect's instinct was different: "I was kinda hoping to actually be building things with it."

The question: could Inscript be a language someone uses to build a Möbius client? A real client surface — screens, buttons, inputs, navigation — authored by a non-programmer in readable English prose.

After scanning both repositories (`rmichaelthomas/inscript` and `rmichaelthomas/mobius`), the answer was yes. The distance is shorter than expected because three of the needed infrastructure pieces already exist in the Möbius monorepo.

### §2 — WHAT ALREADY EXISTS

| Component | Location | What it does |
|---|---|---|
| `BookingDepthProposer` | `clients/bookinghaus/src/narrativeCore/depthProposer.ts` | Sends bounded vocabulary to Claude, gets back constrained inscription proposals. The pattern for an Inscript depth proposer. |
| `NarrativeCoreSession` | `packages/narrative-core/src/session.ts` | Orchestrates observe → propose → coherence-check → authorize/dismiss. |
| `HeuristicProposer` | `packages/narrative-core/src/heuristic.ts` | Template-based proposal from pattern type. |
| `CoherenceChecker` | `packages/narrative-core/src/coherence.ts` | Deterministic duplicate/overlap detection + semantic check via LLM. |
| `createAnthropicAdapter` | `packages/inference/src/adapters/anthropic.ts` | Claude Sonnet 4.6 API adapter. |
| Möbius Inscript DSL | `packages/core/src/inscript/` | TypeScript vocabulary, parser, reorderer — structural sibling for the Inscript Programming Language port. |
| Client architecture | `packages/core/src/client/`, `clients/*/` | Manifest, navigator, bridge, screens, narrative-core integration. Five clients built to this pattern. |

### §3 — WHAT DOES NOT YET EXIST

Three pieces connect the Inscript Programming Language to a visible, interactive Möbius client surface:

1. **A rendering adapter** that translates Inscript's structured results into React component state.
2. **A UI event mapping** that translates user interactions (clicks, text input, navigation) back into Inscript's event queue.
3. **A proposal engine** that turns natural-language descriptions into valid Inscript programs, validated and presented for authorization.

---

## Part II — Rendering Adapter Design

### §4 — UI EVENT MAPPING

**LOGGED as inception-stage design.**

Each named UI component registers as a live value in the Inscript event queue. User interactions update that value.

| Component type | Interaction | Live value name | Value on interaction | Reset value |
|---|---|---|---|---|
| `button` | click/tap | Button's `called` name | `"clicked"` | `"idle"` |
| `input` | text change | Input's `called` name | Current text content | `""` |
| `nav` | navigation complete | `current-screen` | Target screen name | (persists) |
| `list-view` | item selected | `<name>-selected` | Selected item name/index | `"none"` |

Button values reset to `"idle"` after handler completion (edge-triggered per v3a §113). The UI adapter implements the `Adapter` interface (v3a §116).

**Example program:**

```
remember a screen called dashboard with title as "Order Manager"
remember a button called refresh with label as "Refresh Orders"
remember a list called orders with order1 and order2 and order3

when refresh is equal to clicked
  keep the orders where status is equal to active
  show orders

navigate to dashboard
```

**Future expansion path.** The simple mapping (string values) can be expanded to record-valued events when chained `of` lands in the language. The adapter contract's `(name, value)` shape does not change. Programs written against the simple mapping continue to work.

### §5 — RESULT STREAM FOR RENDERING

**LOGGED as inception-stage design.**

The rendering adapter reads the existing structured result stream (v1d §64, v3a §122) and updates React component state via the Möbius client bridge. No new result interface needed.

The adapter subscribes to `HANDLER_FIRE` results. When `names_changed` includes a UI component name, the adapter re-renders affected components via the bridge's `refresh()` / `tick`.

**Initial render.** Phase 1 (sequential) execution builds the symbol table. After Phase 2 enters listener mode, the adapter renders from symbol table state — the "first paint."

### §6 — THE ADAPTER LIVES IN A MÖBIUS CLIENT

**LOGGED as inception-stage design.**

The rendering adapter is a Möbius client in `clients/` following the existing pattern:

```
clients/<client-name>/
├── src/
│   ├── manifest.ts
│   ├── <ClientName>Navigator.tsx
│   ├── screens/
│   ├── components/
│   ├── contexts/
│   ├── adapter/
│   └── narrativeCore/
├── test/
├── index.ts
├── package.json
└── tsconfig.json
```

The client depends on `@mobius/core`, `@mobius/narrative-core`, `@mobius/inference`, and `@mobius/inscript-lang`.

---

## Part III — Proposal Engine Design

### §7 — PROPOSAL ENGINE ARCHITECTURE

**LOGGED as inception-stage design.**

The proposal engine uses `NarrativeCoreSession`. LLM-powered via the Anthropic adapter, constrained to the Inscript vocabulary, with heuristic fallback.

A new `InscriptDepthProposer` follows the `BookingDepthProposer` pattern: receive observation → assemble prompt with vocabulary constraints (34 base words + 11 UI pack words) → send to Claude → parse response → validate `.insc` source through TypeScript parser → return proposal.

**Heuristic templates for common patterns:**

| Pattern | Template output |
|---|---|
| `empty-screen` | Screen with title, header, placeholder text |
| `crud-list` | Screen with list-view, filter button, `when` handler |
| `filter-display` | Data records + filter + list-view wired to filtered results |
| `detail-view` | Screen showing fields of a single record via `of` |

**Authorization per v1a §32.** At least one compositional act before commit.

### §8 — INTENT OBSERVATION

**LOGGED as inception-stage design.**

The intent observer accepts explicit user descriptions via `scanForEvent('user-intent', { description })`. The user types a natural-language description, routed through the `Observer` interface. The session orchestrates the rest.

Proactive observation via `scanAll()` is deferred further — requires defining what user behaviors count as patterns, which depends on watching people use the explicit-intent path first.

### §9 — VALIDATION RUNS CLIENT-SIDE

**LOGGED as inception-stage design.**

Proposed programs are validated through `@mobius/inscript-lang` (the TypeScript parser port from the companion addendum), running client-side. No Python API dependency for validation.

### §10 — WHAT THIS MAKES POSSIBLE

When all three pieces are built, the workflow is:

1. A non-programmer opens the Inscript client surface.
2. They type: "I want a screen that shows active orders with a button to filter them."
3. The proposal engine generates a valid `.insc` program using only the bounded vocabulary.
4. The canonical renderer shows what the program does in readable English prose.
5. The user modifies at least one element (v1a §32 — authorize, don't author).
6. The program renders as a working Möbius client screen inside the container.
7. Button clicks and input changes flow back through `when` handlers.
8. The user has built an application without writing code, without trusting a black box, and without leaving prose.

This is not vibe coding. The output is not opaque generated code. The output is an Inscript program the user can read, because it's English, because the vocabulary is bounded, because the canonical renderer proves what it understood. The "vibe" layer and the "code" layer are the same artifact.

---

## Part IV — Open Questions

| # | Question | Category |
|---|---|---|
| CS-Q1 | **Client name.** Branch D decision. Needs to align with the broader Inscript identity. | Identity |
| CS-Q2 | **Execution host.** Does the Python interpreter run as a sidecar API, or does a partial TypeScript interpreter (sequential only) enter scope? Most consequential architecture decision. | Engineering |
| CS-Q3 | **Layout engine.** Without layout vocabulary, how does the adapter decide spatial arrangement? Source order? Schema defaults? | Design |
| CS-Q4 | **Component nesting.** How is containment expressed? `remember a section called actions with items as submit and cancel`? | Design |
| CS-Q5 | **Proactive observation.** What user behaviors in the composition environment count as patterns for `scanAll()`? | Design |

---

## WHAT IS LOGGED

This inception checkpoint logs:

- **UI event mapping (§4).** Component → live value, interaction → value update. Button resets to idle. Expandable to record-valued events.
- **Result stream rendering (§5).** Existing HANDLER_FIRE stream drives re-renders. No new interface.
- **Client deployment (§6).** Standard Möbius client in `clients/`.
- **Proposal engine (§7).** `InscriptDepthProposer` following `BookingDepthProposer` pattern. Heuristic templates for common UI patterns. LLM-constrained to vocabulary.
- **Intent observation (§8).** Explicit `scanForEvent('user-intent', ...)`. Proactive deferred.
- **Client-side validation (§9).** Via `@mobius/inscript-lang`.

This inception checkpoint does NOT lock any build decisions. All sections are inception-stage design.

---

## PREREQUISITES

Before any work in this inception checkpoint can be built:

1. **`inscript_addendum_v4a_pack_verbs_and_port.md` Phase 1** must be complete — the UI domain pack and pack verb contract must exist in the Python interpreter.
2. **`inscript_addendum_v4a_pack_verbs_and_port.md` Phase 2** must be complete — the TypeScript parser port must exist in `@mobius/inscript-lang`.
3. **CS-Q2 (execution host)** must be resolved — the rendering client needs to execute programs, not just validate them.

---

## RESUME PROMPT (Inscript Client Surface v1)

*We are resuming from the Inscript Client Surface Inception Checkpoint v1 (May 13, 2026). This is a downstream project of the Inscript Programming Language — it uses the Inscript language to build Möbius client surfaces authored by non-programmers in readable English prose.*

*Three capability areas are designed: (1) Rendering adapter — UI event mapping (component → live value), result stream rendering via existing HANDLER_FIRE results, deployed as a standard Möbius client. (2) Proposal engine — LLM-powered via existing `@mobius/inference` Anthropic adapter, reusing `NarrativeCoreSession` orchestration, InscriptDepthProposer following BookingDepthProposer pattern, explicit intent observation only. (3) The workflow that combines them — user describes intent, proposal engine generates valid `.insc`, canonical renderer proves what it does, user modifies, program renders as working Möbius client screen.*

*Prerequisites: the companion addendum `inscript_addendum_v4a_pack_verbs_and_port.md` must be built first (UI domain pack + pack verb contract + TypeScript parser port). Five open questions: CS-Q1 (client name), CS-Q2 (execution host — most consequential), CS-Q3 (layout engine), CS-Q4 (component nesting), CS-Q5 (proactive observation).*

---

## PROVENANCE NOTE

- **`inscript_inception_checkpoint_v1.md`** (May 11, 2026): Branch C (§27), Branch E (§27), domain pack architecture (§19), authorize-don't-author (v1a §32), three-surface graduation (§12).
- **`inscript_addendum_v3a_event_driven_execution.md`** (May 12, 2026): Adapter contract (§116), domain pack registration (§118), event queue (§119), edge-triggered evaluation (§113), result interface (§122).
- **`inscript_addendum_v4a_pack_verbs_and_port.md`** (May 13, 2026): UI domain pack (§134), pack verb contract (§137), TypeScript port (§138). Prerequisite for all work in this checkpoint.
- **`rmichaelthomas/mobius` monorepo** (scanned May 13, 2026): `packages/narrative-core/`, `packages/inference/`, `packages/core/src/inscript/`, `packages/core/src/client/`, `clients/bookinghaus/src/narrativeCore/depthProposer.ts`, `clients/quilt/src/narrativeCore/`.
- **Conversation** (May 13, 2026): Architect decisions on event mapping (simple, expandable), result stream (existing interface), proposal engine (LLM + heuristic via existing infra), intent observation (explicit only).
- **Filename:** `inscript_inception_checkpoint_v1_client_surface.md`.

---

*END OF THE INSCRIPT CLIENT SURFACE INCEPTION CHECKPOINT v1*

*May 13, 2026*

*The language was built from the human end.*
*Now the applications will be too.*
*The prose is still the program.*
*The person is still the author.*
*What changed is what they can build with it — when they're ready.*
