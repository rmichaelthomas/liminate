# INCEPTION CHECKPOINT
## Inscript Programming Language
### v1 — A Language Built from the Human End

**Status:** INCEPTION CHECKPOINT
**Date:** May 11, 2026
**Author:** Rob Thomas / R. Michael Thomas
**Document type:** Inception checkpoint — first-version scoping for a new programming language domain
**Domain prefix:** `inscript` (provisional, pre-vault)
**Relationship to prior checkpoints:** The Inscript Programming Language is a standalone project, not a Möbius client. Its design principles originate in the Möbius Inscript system (v7.5g Inscript Resolution, April 17, 2026), which is itself an expression of Narratia's Freirean pedagogy-first principles. The lineage is: Narratia (pedagogy-first storytelling, Freirean principles) → Möbius Inscript (behavioral rule composition DSL, prose-as-syntax, tile composition, authorize-don't-author) → Inscript Programming Language (general-purpose computation expressed in the same philosophy). This checkpoint introduces no changes to the Möbius protocol. The Möbius Inscript system remains a domain-specific language for behavioral rules within Möbius; the Inscript Programming Language is the thesis scaled to general computation. The "One Thesis, Four Depths" insight capture (April 19, 2026) named the through-line explicitly: the human must remain legible to themselves at every layer, and the intermediary that prevents the governed from reading the rules is the thing that must be removed.

> *"Every programming language in history was designed by programmers. This one wasn't. That's why the design is different."*

---

## HOW TO READ THIS DOCUMENT

- This is an inception checkpoint establishing the Inscript Programming Language as a new project domain.
- Part/§ numbering begins at Part I / §1.
- No Möbius protocol decisions are made here. Möbius Inscript principles are referenced as design lineage, not architectural dependencies.
- This document preserves the full generative arc of the session that produced it. The session began with a Reddit post about C* (C-Asterisk), a student-built compiled programming language. It moved through a thought exercise about what Inscript's philosophy would change about language design, broke into plain-English explanations of compiler pipeline stages, surfaced the competitive landscape, and arrived at the recognition that the combination of properties Rob has already designed — across Narratia, Inscript, and the tile-composition model — occupies genuinely unoccupied territory in programming language design.
- Twelve Parts: the generative question, the lineage, the five novel properties, the pipeline in plain English, the vocabulary design, the graduation model, real-world applications, the build path, the reorderer resolution, the vocabulary scaling resolution, the pipeline component resolution, and open questions.

---

## Part I — The Generative Question

### §1 — HOW WE GOT HERE

The session opened with a Reddit post from r/coolgithubprojects linking to C* (C-Asterisk, `TheJudge26/C-Asterisk-Alpha`), a compiled, statically-typed programming language built from scratch by college students as a compiler construction project. C* has a Python-inspired syntax that compiles to native machine code through LLVM. The entire compiler frontend — lexer, parser, semantic analyzer, and code generator — is written in approximately 2,000 lines of Python with no parser generators or shortcuts. Every token, AST node, and LLVM instruction was hand-written.

Rob's initial reaction: "Almost what I was thinking when I stumbled upon Inscript. I know that's not the same thing but essentially — how could I create my own that non-coders could use and understand?"

The conversation began as a thought exercise comparing C*'s pipeline to Inscript's architecture, then shifted when Rob clarified the direction: not "how do I make Inscript for other domains" but "how do I build an actual programming language from scratch, informed by Inscript's philosophy." The scope expanded from thought exercise to potential project as each layer of the design space was explored.

### §2 — THE QUESTION UNDERNEATH THE QUESTION

The deeper question was not about building a programming language per se. It was about applying the thesis that runs through all of Rob's work — removing obfuscating intermediaries between people and the systems that govern them — to the most fundamental obfuscating intermediary in computing: the programming language itself.

Programming languages are gatekeepers. They stand between human intent and computational execution, and they demand that the human learn to speak the machine's language rather than the other way around. Every language since FORTRAN has made this same demand. Some are friendlier about it (Python), some are brutal (C++), but all require the human to cross over into the machine's territory.

The Inscript Programming Language asks: what if the machine crossed over instead?

---

## Part II — The Lineage

### §3 — NARRATIA IS THE ROOT

Narratia was built on Paulo Freire's pedagogy of the oppressed — the principle that education is liberation, not consumption, and that learners must author their own narratives rather than absorb dominant ones. The Narratia platform's core properties, drawn from this foundation:

- Accepts raw, unstructured human input
- Orders meaning before output exists
- Preserves voice and integrity under constraint
- Produces artifacts only after meaning is stabilized
- Operates in co-generation mode: engine generates grounded in constraints, human guides and refines, refined version is committed

These properties were designed for an educational storytelling platform. They turned out to be the design principles for a programming language.

### §4 — MÖBIUS INSCRIPT IS THE BRIDGE

The Möbius Inscript system (v7.5g) applied Narratia's principles to behavioral rule composition:

- **Prose-as-syntax** (v7.5g §13): valid inscriptions are readable as English prose. This is a design invariant, not a convenience feature. Syntactic constructs that break readability are rejected.
- **Bounded vocabulary** (v7.5g §11): Inscript is a domain-specific language whose verbs are Möbius verbs. The vocabulary IS the language boundary.
- **Authorize-don't-author** (v7.5g §19): the on-ramp is authorization of observed behavior, not authorship from a blank editor. The system proposes; the human authorizes.
- **Tile composition** (v7.5h §25): first-encounter interaction is arranging vocabulary tiles into sentences. No text field. No syntax errors. The DSL constraint is experienced as the shape of the instrument, not as an error message.
- **Graduation** (v7.5h §27): as complexity grows, the interaction surface graduates from tile arrangement to prose editing of the same syntax. The syntax does not change; the interaction modality does.

Each of these was designed for a behavioral rule language. Each applies directly to a general-purpose programming language.

### §5 — THE ONE-THESIS CONNECTION

The "One Thesis, Four Depths" insight capture (April 19, 2026) named the pattern: Narratia, Counter-Flow, TAOS, and Möbius are four expressions of one thesis at different layers. The through-line is authorship — the person affected must remain the author of their story (Narratia), their engagement (Counter-Flow), their system's accountability (TAOS), and the rules governing their space (Inscript).

The Inscript Programming Language is a fifth expression: the person must remain the author of their computation. The moment authorship is delegated to a language the person can't read, agency is structurally lost. The programming language itself is the obfuscating intermediary. Removing it — or rather, redesigning it so the human never leaves their own language — is the thesis applied to its most fundamental layer.

Rob designed this from the human end, not the machine end. He is not a programmer. He designed Inscript's principles before he understood compiler pipelines. That origin is not incidental — it is the reason the design is different from every other programming language in history. Every other language was designed by someone who already thought in code, for people who would learn to think in code. This one was designed by someone who thinks in systems, narrative, and liberation pedagogy, for people who think in their own language.

---

## Part III — The Five Novel Properties

### §6 — COMPETITIVE LANDSCAPE

The existing landscape was surveyed across five categories:

**Inform 7** — the closest existing prose-as-syntax language. Natural English programming for interactive fiction, created by Graham Nelson in 2006. Valid code reads as English sentences: "The Living Room is a room. The old chest is a closed openable container." Inform 7 has been ranked in the top 100 programming languages (TIOBE index) and is widely used in education and literary writing. However: it is domain-locked to interactive fiction, it has no tile composition, no graduation model, no authorize-don't-author, and its own documentation describes it as "easy to read, hard to write." Inform 7 solved prose-as-syntax but did not solve the authoring problem.

**Block-based languages (Scratch, Blockly, Snap!)** — tile/block composition for beginners. You pick from a palette, snap blocks together, no syntax errors possible. However: no graduation to text within the same language. When you outgrow Scratch, you leave Scratch and learn Python — a different language, a different world, a cliff rather than a ramp. Harvard's CS50 moves from Scratch to C; Berkeley's CS10 from Snap! to Python. The transition is always between two different languages.

**Hybrid block-text tools (Mind+, Droplet, VEXcode)** — show both blocks and text side by side. However: the text view is an existing language (Python, JavaScript). The blocks are a visual skin over traditional syntax, not a prose language. The underlying language remains programmer-facing.

**Vibe coding / AI coding assistants (Cursor, Copilot, Claude Code)** — describe intent in natural language, AI generates code. However: the output is traditional code that a programmer must verify. The AI is a translator, not a language. There is no bounded vocabulary — the human can say anything, and the AI can misunderstand anything. 72% of developers now use AI coding tools daily, and 41% of code is AI-generated, but the underlying languages remain unchanged.

**Low-code / no-code platforms (Zapier, Retool, n8n, IFTTT)** — visual workflow builders for non-programmers. However: proprietary platforms, not open languages. Cannot be extended, studied, or owned. Corporate tools, not liberation infrastructure.

### §7 — THE FIVE PROPERTIES THAT DON'T EXIST TOGETHER

**Decision: The Inscript Programming Language is defined by the combination of five properties, each of which exists in isolation in the landscape but none of which have been combined in a single language. LOGGED as inception-stage positioning.**

**Property 1: Prose-as-syntax where the prose IS the executable code.** Not prose that generates code (vibe coding), not prose that describes a game world (Inform 7 — though Inform 7 does execute its prose, it is domain-locked). General-purpose computation expressed as readable English sentences that execute directly. `filter the orders where total is above 50` is not a prompt to an AI — it is the program.

**Property 2: Tile composition as the primary authoring surface with a bounded vocabulary.** The language ships with a curated vocabulary. First encounter is arranging tiles, not typing into a blank file. The DSL constraint is the shape of the instrument, not an error message. Scratch does this but produces blocks, not prose, and doesn't graduate.

**Property 3: Graduation from tiles to text editing of the same language.** Both views produce the same underlying structure (AST). A beginner in tiles and an experienced user typing prose are writing the same program. The language meets you where you are. Nobody has built this — Scratch to Python is two languages, not two views of one.

**Property 4: Authorize-don't-author as a language interaction model.** The system observes what you're trying to do, proposes a working program, and you modify rather than create from nothing. The first program you touch is not a blank file — it is a working program the system composed from your stated intent. This is fundamentally different from AI code generation, which requires you to prompt. Here the system proposes without being asked, based on observed patterns.

**Property 5: Designed from liberation pedagogy by a non-programmer.** Every existing programming language was designed by computer scientists or engineers, for people who would learn to think like computer scientists or engineers. The Inscript Programming Language was designed by a community infrastructure architect working from Freire, for people who think in their own language. The design origin produces different design decisions at every layer.

---

## Part IV — The Pipeline in Plain English

### §8 — WHAT A PROGRAMMING LANGUAGE ACTUALLY IS

A programming language is a translation machine. The human writes something readable; the machine turns it into something executable. The translation happens in stages. Each stage has one job.

**Stage 1 — The Lexer (the word-splitter).** Takes raw text and figures out where the words are and what kind of word each one is. Not what they mean — just identification and labeling. `filter the orders where total is above 50` becomes seven labeled pieces: a verb (`filter`), an article (`the`), a name (`orders`), a connective (`where`), a field reference (`total`), a comparison operator (`is above`), and a value (`50`). The output is called tokens.

**Stage 2 — The Parser (the sentence diagrammer).** Takes labeled tokens and figures out the structure — what goes with what, what's inside what, what depends on what. Builds a tree (called an AST — abstract syntax tree) that diagrams the sentence. "This is a filter operation; the target is `orders`; the condition is a comparison; the comparison's field is `total`, operator is `above`, threshold is `50`."

**Stage 3 — The Semantic Analyzer (the meaning checker).** The parser confirmed grammar; the semantic analyzer confirms meaning. Does the collection `orders` exist? Does it have a field called `total`? Is `total` a number (so "above 50" makes sense)? Catches contradictions and references to things that don't exist.

**Stage 4 — The Interpreter or Compiler (the executor).** Walks the validated tree and either does the thing immediately (interpreter) or translates it into machine instructions for later execution (compiler). The first version of the Inscript Programming Language would be an interpreter — simpler to build, fast feedback loop, good enough for the learning stage.

### §9 — HOW INSCRIPT'S PHILOSOPHY CHANGES EACH STAGE

**Decision: Each stage of the pipeline is redesigned when Inscript's principles are applied. The changes are not cosmetic — they are structural. LOGGED as inception-stage architectural direction.**

**The lexer becomes a vocabulary lookup.** In traditional languages, the lexer must handle arbitrary identifiers — any string of characters could be a variable name. In a bounded-vocabulary language, the lexer knows every word in advance. It splits input on spaces and looks up each word in the vocabulary table. If the word is in the table, it gets its category tag (verb, noun, connective, quantifier, value). If it's not, it's either a user-provided name or a literal value. The lexer for a bounded-vocabulary language is simpler and more reliable than a traditional lexer because the vocabulary is closed.

**The parser gains a reorderer.** Traditional parsers fail when tokens are in the wrong order — "unexpected token" errors. The Inscript parser includes a reorderer (locked in v8.11 §283 for Möbius Inscript) that silently maps free-order token arrangements to valid grammar before the parser sees them. The human can type `the orders filter where above 50 total is` and the reorderer maps it to the valid parse: `filter the orders where total is above 50`. The grammar is strict; the surface is forgiving. The error mode changes from "unexpected token at line 3" to "I can't figure out what you mean — here's what's missing."

**The semantic analyzer moves into the interaction.** Traditional semantic analysis runs after the program is written — it tells you what's wrong after the fact. In a tile-composition environment, semantic validity is enforced during composition. The instrument only offers tiles that can validly combine. Wrong arrangements feel unnatural before you finish, not after. When editing as prose, the semantic analyzer runs continuously and shows validity as a live indicator (green/amber per v8.11 §283), not as a post-hoc error list.

**The interpreter starts from working programs, not blank files.** The authorize-don't-author principle means the interpreter ships with example programs that work. The user's first experience is modifying a working program, not constructing one from nothing. The interpreter includes a proposal engine that observes the user's stated intent and composes a valid program from vocabulary tiles, presenting it for modification.

---

## Part V — The Vocabulary Design

### §10 — CONCEPT-LAYER, NOT MECHANISM-LAYER

**Decision: The Inscript Programming Language operates at the concept layer of computation, not the mechanism layer. Its vocabulary names what people are trying to do, not how the machine does it. LOGGED as inception-stage design direction.**

Traditional languages operate at the mechanism layer. `for i in range(len(orders)): if orders[i].total > 50: result.append(orders[i])` describes the mechanism — loop through an index, check a condition, append to a result list. The concept — "find orders above $50" — is buried inside mechanism.

The Inscript vocabulary names concepts directly:

- `filter` instead of writing a conditional inside a loop
- `gather` instead of building a list
- `count` instead of a variable you increment
- `combine` instead of concatenating or merging
- `remember` instead of storing a value
- `transform` instead of a function that modifies data
- `compare` instead of writing comparison operators
- `choose` instead of an if/else branch
- `each` instead of a for loop
- `show` instead of print/console.log/stdout

These are not friendlier names for the same operations. They are a higher level of abstraction. `filter` in traditional programming means "write a function that returns true or false, pass it to a higher-order function that applies it to each element." In the Inscript Programming Language, `filter the orders where total is above 50` is the complete program. The concept IS the code.

### §11 — THE STARTING VOCABULARY

**Decision: Version one of the Inscript Programming Language uses a bounded vocabulary — seven verbs, nine connectives, five operators, two articles, and one delimiter. Three additional verbs (`transform`, `choose`, `compare`) and two temporal connectives (`when`, `unless`) are designed but deferred to v2. The vocabulary expands incrementally through domain packs as the language proves itself. LOGGED as inception-stage scope constraint, UPDATED with pipeline component resolution.**

Provisional starting vocabulary (subject to refinement during build):

**v1 vocabulary (sequential execution):**

| Category | Words |
|---|---|
| **Verbs** | `remember`, `show`, `filter`, `count`, `gather`, `combine`, `each` |
| **Connectives** | `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as` |
| **Operators** | `is`, `above`, `below`, `equal to`, `not` |
| **Articles** | `the`, `a` |
| **Delimiters** | `:` (colon — separates named composition name from body) |

Notes on specific tokens:
- `equal to` is a multi-word operator. The lexer combines `equal` + `to` into a single token via one-word lookahead.
- `to` serves two roles: range endpoint in `gather the numbers from 1 to 10`, and part of the `equal to` operator. The parser disambiguates by context (after `from` + number = range; after `equal` = operator).
- `how` signals named composition definitions: `remember how to [name]: [body]`.
- `as` enables structured records: `remember an order with total as 75 and status as active`. Added to support field-based filtering (§23).
- `is` has dual roles resolved in §23: comparison introducer (`is above`) vs. equality operator (`is active`).
- `not` is a genuine operator modifier with its own comparison semantics, resolved in §23.

**v2 vocabulary (deferred — designed but not executable in the v1 interpreter):**

| Category | Words | Reason for deferral |
|---|---|---|
| **Temporal connectives** | `when`, `unless` | Require event-driven execution model (listener/reactor); v1 is sequential (§13) |
| **Deferred verbs** | `transform`, `choose`, `compare` | Under-specified semantics that cannot execute without additional grammar design (§21) |

`when` and `unless` introduce event-driven execution: "when X happens, do Y" means the program listens and waits rather than running top-to-bottom. The v1 interpreter (§16) is sequential. These words exist in the language design because the use cases that need them (healthcare monitoring, smart home automation, reactive game logic) are core to the language's purpose. They are deferred from the v1 interpreter, not from the language.

`transform` is deferred because its operation is ambiguous — "transform the prices with a discount" doesn't specify how (subtract? multiply? percentage?). `choose` is deferred because its branching grammar (condition + consequence + alternative) requires resolving additional `or` context-dependency. `compare` is deferred because its return value is undefined and it is most useful paired with `choose`. All three will be reintroduced in v2 with fully specified grammars.

This vocabulary allows programs like:

```
remember a list called groceries with milk and eggs and bread
show groceries
gather the numbers from 1 to 100
filter the numbers where each is above 50
count the numbers
remember the total called sum from combine the numbers
show sum
```

The vocabulary is the tile tray. Every word in this table is a tile. There are no words outside this table in v1 except user-provided names (like `groceries`) and literal values (like `50`).

---

## Part VI — The Graduation Model

### §12 — THREE VIEWS, ONE STRUCTURE

**Decision: The Inscript Programming Language has three interaction surfaces — tile composition, prose editing, and symbolic text — all producing the same underlying AST. The three surfaces are views, not modes. The language does not change; the interaction modality does. LOGGED as inception-stage design invariant.**

**Surface 1 — Tile composition (on-ramp).** The user picks from a tile tray organized by category (verbs, connectives, operators, articles). They arrange tiles into a sentence. The reorderer maps the arrangement to valid grammar. A live preview shows the resulting prose. A validity indicator shows whether the arrangement is complete (green) or structurally incomplete (amber with a description of what's missing). This is the Möbius Inscript tile-composition model (v7.5h §25) applied to general computation.

**Surface 2 — Prose editing (intermediate).** The user types directly in the language's prose syntax. Autocomplete offers vocabulary words as they type. The semantic analyzer runs continuously. The experience is writing a sentence with guided completion, not programming. This is the graduation surface (v7.5h §27).

**Surface 3 — Symbolic text (advanced, optional).** For users who eventually want terseness, the language supports an equivalent symbolic syntax: `orders.filter(total > 50)` means exactly the same thing as `filter the orders where total is above 50` and produces the same AST. This surface exists for velocity, not for learning. It is never the default.

The architectural insight: the AST is the source of truth. All three surfaces are editors for the same structure. A program composed in tiles can be opened in the prose editor. A program written as prose can be viewed as tiles. The underlying representation is identical. Two people — one in tiles, one in prose — could work on the same program simultaneously.

This is the property no existing language has. Scratch to Python is two languages. Mind+ shows Python through blocks. The Inscript Programming Language is one language with three interaction surfaces.

---

## Part VII — Real-World Applications

### §13 — WHERE THE TRANSLATION GAP IS MOST COSTLY

**Decision: The Inscript Programming Language's initial target domains are identified by the cost of the translation gap — domains where the person who understands the problem cannot currently express the solution in code, and the translation through an engineer intermediary is where errors, cost, and delay concentrate. LOGGED as inception-stage domain identification.**

**IMPORTANT: These use cases span two execution models. Not all are achievable in the v1 interpreter.**

**v1 use cases (sequential execution — achievable with the v1 interpreter):**

**Business rules.** Every company has operational rules that a business manager understands and an engineer must implement. The translation chain (manager → product manager → spec → engineer → code → QA) is where intent drifts. Companies like Shopify, Stripe, and every insurance company spend enormous engineering budgets on rules engines that attempt to solve this problem. Most fail because they're built by engineers who think in code, not by the people who think in policy. Business rules are predominantly sequential: take data, check conditions, produce results. They are the natural v1 beachhead.

**Legal and regulatory compliance.** Regulations are written in English. Software must comply with them. The translation chain (lawyer → compliance memo → product manager → spec → engineer → code) is four lossy translations. The compliance officer could write the rule directly. Compliance rules are predominantly sequential: take a transaction, check thresholds, flag or pass.

**Data filtering and reporting.** Any domain where the task is "take a collection of things, apply conditions, produce a subset or summary." Sales reports, inventory queries, student grade filtering, survey analysis. These are the core sequential operations the v1 vocabulary already expresses.

**v2 use cases (event-driven execution — require the `when`/`unless` temporal connectives and a listener model the v1 interpreter does not have):**

**Healthcare protocols.** Clinical decision protocols like "when blood pressure exceeds 180, alert the physician" require event-driven execution — the system listens for a condition and reacts. The clinician should author the protocol directly in prose, but the interpreter must support a listener model to execute it. This is a v2 capability.

**Smart home and IoT automation.** "When I leave the house after sunset, turn off the lights but leave the porch light on until 11." The `when` clause means the program is listening for departure events, checking time conditions, and triggering actions reactively. The bounded vocabulary (devices, people, conditions, actions) maps directly to the tile model, but the execution requires event-driven infrastructure. This is a v2 capability.

**Game design and interactive narrative.** "When the player enters the forest and has the silver key, reveal the hidden path." Writers and game designers think in event triggers, conditions, and branching consequences. The writer's document could BE the program — but executing it requires the interpreter to maintain state and listen for game events. This is a v2 capability.

The common thread across both tiers: the computation isn't hard. Checking thresholds, sending notifications, toggling devices — computers do this trivially. What's hard is the translation from human intent to code. The Inscript Programming Language eliminates the translation step. The v1/v2 distinction is about interpreter capability, not language expressiveness — the prose reads the same in both tiers.

---

## Part VIII — The Build Path

### §14 — HOST LANGUAGE

**Decision: The Inscript Programming Language interpreter will be built in Python. LOGGED as inception-stage implementation decision.**

The bootstrapping problem: a new language doesn't exist yet, so its translator must be written in a language the computer already speaks. Every programming language is born inside another language. C was written in assembly. Python was written in C. C* was written in Python.

Python is the right choice for the Inscript Programming Language for three reasons:

1. **The C* repo is a direct study guide.** The `TheJudge26/C-Asterisk-Alpha` codebase is a complete compiler pipeline in readable Python — lexer, parser, semantic analyzer, and codegen in roughly 2,000 lines. This serves as a structural reference, not as code to copy.
2. **Community depth.** The overwhelming majority of tutorials, books, and courses on building programming languages from scratch use Python. The community of people who have done this and can help is largest in Python.
3. **Readable host for a readable language.** Python is the host language closest to plain English, which has symmetry with building a language whose core invariant is prose readability.

The deployment target is independent of the host language. Where the Inscript Programming Language ultimately runs (browser, desktop, terminal, native app, all of the above) is a deployment decision made after the language works. The interpreter could later be rewritten in JavaScript for browser deployment, or compiled to WebAssembly, or ported to any other runtime. The host language is a build decision, not a platform commitment.

### §15 — ROB'S CURRENT POSITION

Rob completed the Codecademy "Learn How to Code" course (certificate, May 3, 2025) and the "Code Foundations Skill Path" (certificate, May 3, 2025). He is 68% through the "Intro to Programming" path: "Introduction to the Computer Science Career Path" (complete), "Fundamentals of Python" (complete), "Programming in Python on Your Computer" (complete), "Basic Python Data Structures and Objects" (21%).

The gap between Rob's current Python knowledge and building a lexer is narrow. The lexer requires string manipulation, loops, conditionals, and list operations — all covered by the completed fundamentals. The parser requires data structures (trees built from objects containing objects), which is exactly what the in-progress "Data Structures and Objects" module covers. The interpreter requires walking a tree and acting on each node — functions, conditionals, and dictionaries.

The build path is not "finish the Codecademy career path, then start the language." It is "finish data structures, then build the lexer — and let the language project itself become the curriculum." Each pipeline stage teaches a different Python skill, and the motivation of building one's own language is higher than completing abstract exercises.

### §16 — FIRST VERSION SCOPE

**Decision: The first version of the Inscript Programming Language is an interpreter (not a compiler), supporting the v1 vocabulary (seven verbs, nine connectives, five operators, two articles, and one delimiter — see §11), executing programs from text input. The tile-composition interface is a separate layer built after the interpreter works. LOGGED as inception-stage build scope.**

The build sequence:

1. **Define the vocabulary** (design work, no code). Write thirty example sentences. Discover the grammar by writing sentences that feel right, then extracting the rules.
2. **Build the lexer** (Python, ~40 lines). Split input on spaces, look up each word in the vocabulary table, tag with category.
3. **Build the parser** (Python, ~200 lines). Pattern-match tagged token sequences into an AST. Each sentence pattern becomes a parse rule.
4. **Build the interpreter** (Python, ~200 lines). Walk the AST, execute each node. Create lists, filter them, count them, show results.
5. **Build the tile interface** (technology TBD). Present the vocabulary as tappable/draggable tiles, composition strip, prose preview, validity indicator. This is the surface; the interpreter is the engine.

The first four steps produce a working language that runs in a terminal. The fifth step wraps it in the interaction model that makes it accessible to non-programmers. Both are necessary; the interpreter is the prerequisite.

---

## Part IX — The Reorderer Resolution

### §17 — SLOT FILLING, NOT NATURAL LANGUAGE UNDERSTANDING

**Decision: The reorderer uses slot filling — each verb defines a signature of expected slots, and the reorderer matches remaining words to slots by category. The reorderer does not need to understand natural language. It needs to understand a small, curated set of sentence patterns built around known verbs with known signatures. LOCKED as reorderer architecture.**

The reorderer was identified as the primary engineering pressure point by external review. The concern: mapping free-form human word order to strict grammatical structure is a hard problem in general. The resolution: it is not a hard problem for a bounded vocabulary where every word's category is known in advance and every verb's signature is defined in advance.

The algorithm:

**Step 1 — Find the verb.** The lexer has already tagged every word by category. The verb is instantly identifiable. Most sentences have exactly one verb, which anchors the entire parse.

**Step 2 — Look up the verb's signature.** Each verb has a defined set of slots with expected types:
- `filter` → target (name/collection) + condition (field + operator + value)
- `remember` → value + name
- `show` → target
- `count` → target
- `gather` → what + source
- `combine` → targets
- `transform` → target + operation
- `choose` → condition + consequence + alternative
- `each` → collection + action

**Step 3 — Fill slots from remaining words.** The reorderer matches each non-verb word to a slot based on its category tag. `orders` is a name → fills the target slot. `total` is a field → starts the condition. `is above` is a comparison operator. `50` is a value. `where` is a connective introducing the condition.

**Step 4 — Output canonical order.** Once slots are filled, the signature defines the output order. The result is always the canonical prose form, regardless of input arrangement.

**Ambiguity handling for v1:** When a set of words could fill slots in more than one valid way, the reorderer does not guess. The validity indicator goes amber with a natural-language description of the ambiguity: "I'm not sure if you mean X or Y — can you clarify?" This follows the Inscript philosophy: the instrument shapes the interaction rather than silently assuming.

### §18 — PRECEDENT IN NARRATIA AND LOOM

**Decision: The reorderer's component patterns already exist across the Narratia MVP and Loom by Narratia MVP codebases. The reorderer is a composition of proven patterns, not a novel invention. LOCKED as implementation source identification.**

A code scan of both repositories (May 11, 2026) confirmed:

| Reorderer Component | Existing Implementation | Location |
|---|---|---|
| Bounded vocabulary lookup (lexer) | `hasAny()` — checks text against known phrase sets | Loom `server/rules.js` (sha: 527450e) |
| Structural reordering of unstructured input | `naive_outline()` — splits freewrite into sentences, groups into 3–6 ordered beats | Narratia `utils.py` (sha: 4425e83) |
| Contradiction/ambiguity detection | `runGrantFit()` — detects conflicts between baseline canon and grant requirements, produces scored flags with human-readable reasons | Loom `server/rules.js` (sha: 527450e) |
| Post-reorder semantic validation | `runIntegrity()` — checks AI-generated output against baseline canon for contradictions after drafting | Loom `server/rules.js` (sha: 527450e) |
| Two-tier architecture (deterministic + AI) | Heuristic `naive_*()` fallbacks + `llm_*_safe()` AI wrappers | Narratia `utils.py` (sha: 4425e83) |
| Human-readable error explanations | Scored dimensions (mission, scope, ethics, stretch) + natural-language reasons ("Grant pressures youth engagement; canon is adult-only") | Loom `server/rules.js` (sha: 527450e) |

The patterns compose into the reorderer pipeline as follows: `hasAny()` demonstrates bounded vocabulary lookup (the lexer). `naive_outline()` demonstrates imposing structure on unstructured input (the reorderer core). `runGrantFit()` demonstrates detecting contradictions between two inputs and producing scored, human-readable explanations (ambiguity detection). `runIntegrity()` demonstrates post-generation validation against constraints (the semantic analyzer). The two-tier fallback architecture in both repos demonstrates the deterministic-free-tier / AI-depth-tier split.

---

## Part X — Vocabulary Scaling Resolution

### §19 — THE BASE VOCABULARY IS SACRED

**Decision: The base vocabulary (~20 words) does not scale. It stays small permanently. Expressiveness scales through four mechanisms external to the base vocabulary. LOCKED as vocabulary scaling architecture.**

Vocabulary scaling was identified as the second engineering pressure point. The concern: as the language adds complex operations, prose could become "word salad" — grammatically correct but cognitively opaque. The resolution: the base vocabulary is never the thing that grows.

Natural languages handle 170,000+ words not by presenting them all at once but through contextual activation, composition, and naming. The Inscript Programming Language follows the same pattern.

**Mechanism 1 — Domain packs.** The base vocabulary stays at ~20 words. When a user works in a specific domain, a domain pack activates and adds context-specific vocabulary. Each pack adds 10–15 domain-specific nouns and a few domain verbs. The tile tray shows the core vocabulary plus the active domain pack — still bounded, still scannable, but contextually relevant.

| Domain Pack | Added Vocabulary (illustrative) | Target Audience |
|---|---|---|
| Healthcare | `patient`, `prescribe`, `alert`, `diagnose`, `protocol`, `symptom`, `dosage` | Clinicians, nurses |
| Business | `invoice`, `approve`, `escalate`, `deadline`, `budget`, `assign`, `report` | Operations managers |
| Home automation | `lights`, `thermostat`, `lock`, `motion`, `sunset`, `schedule`, `notify` | Homeowners |
| Game/narrative | `player`, `reveal`, `hide`, `inventory`, `enter`, `speak`, `trigger` | Writers, game designers |
| Legal/compliance | `regulation`, `violation`, `threshold`, `report`, `audit`, `enforce`, `exempt` | Compliance officers |

Domain packs also serve as the language's natural adoption path. Each pack is a product: "An Inscript healthcare pack that lets nurses write clinical protocols in plain English." The base language is infrastructure; the domain packs are surfaces. Same architecture as Möbius — the protocol is invisible, the clients are what people touch.

**Mechanism 2 — Composition over expansion.** Instead of adding a new verb for every concept, compose complex operations from existing words. `gather the orders and arrange by date` rather than adding `sort`. `when the data arrives, filter it where total is above 50` rather than adding `async`. The temporal connective `when` already handles event-driven logic. The vocabulary stays small; expressiveness comes from combination.

**Mechanism 3 — Named compositions (chunking).** When a sentence gets complex, the user names part of it:

```
remember how to find-big-orders: filter the orders where total is above 50
remember how to find-loyal-customers: filter the customers where years is above 2

find-big-orders from find-loyal-customers
```

`find-big-orders` becomes a tile the user created — a named composition of existing words that appears in their personal tile tray. The base vocabulary didn't grow. The user's vocabulary grew through their own authorship. This is the Inscript authorize-don't-author principle applied recursively: the user authors their own vocabulary from the bounded set.

Named compositions are also the answer to open question Q9 (composition and reuse). "remember how to [name]" is the prose expression of a function definition, expressed without programming jargon.

**Mechanism 4 — Sentence complexity cap.** The language enforces a maximum sentence complexity (approximately three clauses or fifteen content words). When a sentence exceeds the threshold, the validity indicator goes amber: "This is getting complex — would you like to name part of it?" The system guides decomposition into named steps. Complex programs read as sequences of short, named sentences — paragraphs, not run-on sentences.

This is how Loom's `rules.js` handles the baseline canon: not as one monolithic check but as individual constraint checks, each bounded, each independently meaningful. The same principle applied to programs.

### §20 — THE WORD SALAD TEST

**Decision: Before any word is added to the base vocabulary or a domain pack, it must pass the word salad test: "Can a non-programmer read a sentence using this word and understand what it does without explanation?" If it fails, it doesn't go in. The vocabulary is curated, not accumulated. LOCKED as vocabulary governance principle.**

---

## Part XI — Pipeline Component Resolution

### §21 — PARSER TIGHTENING

**Decision: The v1 verb set is reduced from ten to seven. `transform`, `choose`, and `compare` are deferred to v2 due to under-specified semantics. The remaining seven verbs (`remember`, `show`, `filter`, `count`, `gather`, `combine`, `each`) all have clear, executable semantics with defined signatures. LOCKED as v1 parser scope.**

**Decision: `and`/`or` context rules are resolved as follows. The parser tracks which clause it is currently inside (parser state) and checks the category of the next word after `and`/`or` (lookahead). Four meanings are deterministically disambiguated:**

| Context | Meaning | Disambiguation rule |
|---|---|---|
| Inside a `with` clause, next word is a value | List construction: `with milk and eggs and bread` | Parser state = `with` clause, next token = value/unknown |
| Inside a `where` clause, next word is a field reference | Compound condition: `where status is active and age is above 18` | Parser state = `where` clause, next token = field reference |
| After a complete verb phrase, next word is a verb | Operation sequencing: `filter the orders and show the count` | Current verb phrase is complete, next token = verb |
| Inside a `with...as` clause, next word is a field name | Record field continuation: `with total as 75 and status as active` | Parser state = `with...as` clause, next token = field name |

**LOCKED as `and`/`or` disambiguation rules.**

**Decision: `is` dual role resolved. If the word following `is` is a known operator (`above`, `below`, `not`, `equal`), then `is` is a comparison introducer and the operator is the next word. If the word following `is` is a value or name, then `is` itself is the equality operator. One-word lookahead resolves this deterministically. LOCKED as `is` disambiguation rule.**

**Decision: `not` is a genuine operator modifier producing its own comparison semantics, not a synonym-swap for another operator. `not above 50` means ≤ 50 (less than or equal to — includes 50), which is distinct from `below 50` (strictly less than — excludes 50). `not below 50` means ≥ 50. `not equal to 50` means ≠ 50. The interpreter implements three dedicated comparison operations for `not above`, `not below`, and `not equal to`. LOCKED as `not` operator semantics.**

**Decision: Compound conditions (Q14) are handled within the `and`/`or` context rules above. `and` inside a `where` clause before a field reference creates a compound condition node in the AST with two sub-condition children. `or` inside a `where` clause works the same way. Compound conditions nest recursively: `where A and B or C` produces a tree with `or` at the root, `C` on one branch, and an `and` node on the other branch with `A` and `B` as children. LOCKED as compound condition parser rule. Q14 RESOLVED.**

### §22 — LEXER RESOLUTION

**Decision: The lexer is specified as follows for v1. LOCKED as lexer specification.**

**Case insensitivity.** The lexer lowercases all input before vocabulary lookup. `Filter The Orders Where Total Is Above 50` produces the same tokens as `filter the orders where total is above 50`. Non-programmers capitalize naturally; the language accepts it.

**Multi-word token handling.** When the lexer encounters `equal`, it checks the next word. If the next word is `to`, it combines them into a single `equal_to` operator token. No other multi-word tokens exist in v1.

**Number recognition.** A token consisting entirely of digits (optionally with one decimal point) is tagged as a number. `30`, `3.14`, `100` are numbers. Negative numbers are deferred to v2. No scientific notation.

**Decorative punctuation stripping.** Commas, periods, question marks, and exclamation marks are stripped before processing. `with milk, eggs, and bread` is processed as `with milk eggs and bread` (the `and` is the structural separator; commas are decorative). This lets people type naturally without syntactic punishment.

**Whitespace normalization.** Multiple spaces and tabs are collapsed to single separators. Each newline boundary is a statement separator — one sentence per line.

**Colon delimiter.** The colon `:` is recognized as a delimiter token, separated from adjacent text. `find-big-orders:` is split into name `find-big-orders` and delimiter `:`.

**Valid name characters.** User-provided names may contain letters, digits, and hyphens. `find-big-orders`, `order1`, `my-list` are valid names. Names must start with a letter.

**Unknown word handling.** Words not in the vocabulary table and not matching number patterns are tagged as `unknown`. The lexer cannot fully classify unknown words — they may be user-provided names, string values, or field references depending on sentence position. The parser completes classification using positional context: after `called` → name. After `with` (without `as`) → value. Inside a `where` clause before an operator → field reference. Inside a `where` clause after an operator → value.

### §23 — SEMANTIC ANALYZER RESOLUTION

**Decision: v1 supports structured records via the `as` connective, enabling field-based filtering. LOCKED as v1 data model.**

The structured data gap: `filter the orders where total is above 50` requires items in `orders` to have named properties (a `total` field). The `remember` verb without `as` can only create flat values and flat lists. Without structured records, the language cannot demonstrate its core value proposition for business rules.

The resolution: `as` enables field assignment within `remember` statements.

`remember an order called order1 with total as 75 and status as active` creates a record: `{total: 75, status: "active"}` named `order1`.

`remember a list called orders with order1 and order2` creates a list of structured records.

`filter the orders where total is above 50` now works: the semantic analyzer verifies that `total` is a field on items in `orders` by checking the schema recorded in the symbol table.

The parser extension is a sub-pattern of the existing `with` clause: `with [field] as [value] and [field] as [value]` is handled by the `and`/`or` context rule for `with...as` clauses (§21).

**Decision: The symbol table tracks types, not just names. LOCKED as semantic analyzer data model.**

When `remember a number called age with 30` is processed, the symbol table records: name = `age`, type = `number`, value = `30`. When `remember a list called numbers with 1 and 2 and 3` is processed: name = `numbers`, type = `list of numbers`. When a structured record is created: name = `order1`, type = `record`, schema = `{total: number, status: string}`.

Type checking during semantic analysis: `filter the numbers where each is above hello` → error: "`above` requires numbers, but `hello` is text." `filter the orders where total is above 50` → valid: `total` is a number field, `50` is a number, `above` accepts numbers.

Types for v1: number (integer or decimal), string (text), list (of numbers, of strings, or of records), record (named fields with typed values), named composition (stored verb phrase). Types are inferred from values — `75` is a number, `active` is a string. No explicit type annotations required.

**Decision: Named composition validation is split — grammar at definition time, names at call time. LOCKED as composition validation rule.**

`remember how to find-big-orders: filter the orders where total is above 50` — at definition time, the semantic analyzer validates that the body is a well-formed sentence (valid verb, valid clause structure). It does NOT validate that `orders` exists or has a `total` field, because the data the composition operates on may not exist yet.

`find-big-orders from the shop` — at call time, the semantic analyzer resolves names against the current symbol table. Does `the shop` have `orders`? Does it have a `total` field? Errors at call time produce messages like "I can't find 'orders' — you might need to 'remember' it first."

### §24 — INTERPRETER RESOLUTION

**Decision: Standalone expressions auto-show their result. LOCKED as v1 interpreter behavior.**

`count the numbers` on its own line computes a value and displays it immediately, like a calculator. The non-programmer expectation: if I ask the computer to count something, it should tell me the answer. Silence would feel broken. If the result needs to be used later, name it explicitly: `remember the total called num-count from count the numbers`. If you just want to see it, type the expression.

This applies to all verbs that produce values: `count`, `combine`, `gather` (when not creating a named collection). `remember` produces no output (side effect only). `show` always produces output (explicit display). `filter` modifies in place (side effect). `each` produces output if its sub-operation produces output.

**Decision: `filter` modifies in place. LOCKED as v1 data model behavior.**

After `filter the numbers where each is above 3`, `the numbers` now refers to the filtered subset `[4, 5]`. The original `[1, 2, 3, 4, 5]` is gone. This matches prose intuition — "filter the numbers" means "the numbers are now filtered." Immutable operations (producing a new collection without modifying the original) are a v2 enhancement.

**Decision: `gather` creates named collections inline. LOCKED as v1 `gather` semantics.**

`gather the numbers from 1 to 10` both produces a list `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]` AND stores it under the name `numbers`. The name is parsed from the noun after the article. The interpreter executes the gather operation and adds the result to the symbol table automatically. This makes `gather` an implicit `remember` — it produces and names in one statement.

**Decision: All data operations use copy semantics. No references, no aliasing. LOCKED as v1 data model behavior.**

`gather the big from the numbers` copies the data. Changes to `numbers` after this point do not affect `big`. Every named value is independent. This prevents confusing side effects where modifying one collection silently changes another. Reference semantics are a v2 consideration.

### §25 — v1/v2 DEFERRAL SUMMARY

**v1 scope (resolved and locked):**

| Component | What's in v1 | Key decisions |
|---|---|---|
| **Verbs** | `remember`, `show`, `filter`, `count`, `gather`, `combine`, `each` (7 verbs) | `transform`/`choose`/`compare` deferred due to under-specified semantics |
| **Connectives** | `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as` (9 connectives) | `when`/`unless` deferred (event-driven) |
| **Operators** | `is`, `above`, `below`, `equal to`, `not` (5 operators, `not` as modifier) | `not above` ≠ `below` (includes boundary value) |
| **Lexer** | Case-insensitive, comma-stripping, multi-word tokens, number recognition | Unknown words classified by parser, not lexer |
| **Parser** | Slot filling with verb signatures, `and`/`or` context rules, `is` dual role, recursive descent for `each`, compound conditions | Stateful parser tracking clause context |
| **Semantic analyzer** | Symbol table with types, structured records via `as`, field resolution, composition validation split | External data sources deferred to v2 |
| **Interpreter** | Sequential, auto-show for expressions, in-place `filter`, inline `gather` naming, copy semantics | Event-driven execution deferred to v2 |
| **Data types** | Number, string, list, record (via `as`), named composition | Negative numbers deferred to v2 |

**v2 scope (designed, deferred):**

| Item | Reason for deferral |
|---|---|
| `when`/`unless` temporal connectives | Require event-driven execution model |
| `transform` verb | Operation ambiguous without companion grammar (`by subtracting`, `by multiplying`) |
| `choose` verb | Branching grammar not fully specified; `or` context-dependency unresolved |
| `compare` verb | Return value undefined; most useful paired with `choose` |
| Event-driven interpreter | Listener/reactor model required for healthcare, smart home, game design use cases |
| External data sources | Database, API, CSV import — v1 only handles data defined via `remember` |
| Immutable operations | Alternative to in-place `filter` modification |
| Reference/alias semantics | Alternative to copy-only data model |
| Negative numbers | Requires minus sign handling in lexer |
| Named composition parameters | Compositions that accept arguments at call time |

---

## Part XII — Open Questions

### §26 — OPEN QUESTIONS TABLE

| # | Question | Category |
|---|---|---|
| 1 | **Naming.** Is the programming language also called "Inscript," or does it need its own name to distinguish from Möbius Inscript? The relationship is lineage (Möbius Inscript's principles scaled to general computation), not identity (they are not the same system). A name collision could create confusion. | Identity |
| 2 | **Relationship to Möbius Inscript.** Are these two separate projects that share design principles, or is the programming language Inscript v2 — the graduation of Inscript from DSL to general-purpose language? The answer affects whether this lives in the Möbius monorepo or in its own repository. | Architecture |
| 3 | **Vocabulary curation.** ~~How is the vocabulary refined?~~ **RESOLVED (§19–§20).** Four scaling mechanisms locked: domain packs, composition, named compositions, sentence complexity cap. The word salad test governs all vocabulary additions. Remaining open: specific vocabulary for each domain pack requires domain-expert input. | Design |
| 4 | **Reorderer implementation.** ~~What algorithm does the reorderer use?~~ **RESOLVED (§17–§18).** Slot filling: each verb defines a signature of expected slots, reorderer matches words to slots by category. Ambiguity produces amber indicator with clarification prompt. Component patterns confirmed in Narratia and Loom codebases. | Engineering |
| 5 | **Symbolic syntax.** Surface 3 (symbolic text, e.g., `orders.filter(total > 50)`) is identified as a graduation target. Is it in scope for v1? Does its existence compromise the prose-first commitment? | Design |
| 6 | **Error model.** What does "I can't figure out what you mean" look like in practice? How does the language describe what's missing without using programming jargon? The error experience is a design surface, not just an engineering afterthought. | Design |
| 7 | **Deployment target.** Where does the language run? Terminal only for v1? Browser (via JS rewrite or WASM)? Native app? The tile interface needs a rendering environment; the choice affects the technology stack for step 5 of the build sequence. | Engineering |
| 8 | **Type system.** ~~How are types expressed in prose?~~ **PARTIALLY RESOLVED (§23).** Types are inferred from values for v1 — `75` is a number, `active` is a string. No explicit type annotations required. Symbol table tracks types. Remaining open: how types behave as the language grows beyond v1 primitives (custom types, collections of mixed types, type constraints in named compositions). | Language design |
| 9 | **Composition and reuse.** ~~How are reuse mechanisms expressed in prose?~~ **PARTIALLY RESOLVED (§19, Mechanism 3).** Named compositions ("remember how to [name]") serve as the prose expression of function definitions. Remaining open: scope and lifetime of named compositions, whether compositions can accept parameters, and how compositions interact with domain packs. | Language design |
| 10 | **Community and contribution.** If this is liberation infrastructure, it should be open source from day one. License choice (MIT, GPL, something else)? Contribution model? How does the project invite non-programmer contributors to vocabulary design and sentence testing? | Governance |
| 11 | **Vault and repository.** Does this project get its own vault folder? Its own GitHub repository? Its own domain? None of these decisions are urgent but all affect the project's public legibility. | Infrastructure |
| 12 | **Narratia Core integration.** In Möbius, Narratia Core powers the authorize-don't-author proposal engine (v8.9 §245–§246). Does the Inscript Programming Language's proposal engine also use Narratia Core, or is it a simpler pattern-matching system for v1? | Architecture |
| 13 | **Event-driven execution model.** The v2 use cases (healthcare monitoring, smart home automation, reactive game logic) require `when`/`unless` temporal connectives and a listener model. What does this look like architecturally? How does the interpreter transition from "run and finish" to "listen and react"? What event sources does it connect to? This is the primary v2 engineering question. | Engineering |
| 14 | **Compound conditions.** ~~Parser handling for chained conditions.~~ **RESOLVED (§21).** `and`/`or` inside a `where` clause before a field reference creates compound condition nodes. Recursive nesting supported. Disambiguation is deterministic via parser state + lookahead. | Language design |

### §27 — BRANCHES FOR FUTURE SESSIONS

**Branch A — Vocabulary Design.** Write the thirty example sentences using only v1 vocabulary (§11). Discover the grammar. Test readability with non-programmers.

**Branch B — Python Build.** Complete the Codecademy data structures module. Build the lexer. Build the parser. Build the interpreter. First working program.

**Branch C — Tile Interface.** Choose rendering technology. Design the tile tray layout, composition strip, preview, and validity indicator. Connect to the interpreter.

**Branch D — Identity and Positioning.** Name decision. Relationship to Möbius Inscript. Repository setup. README as manifesto. License choice.

**Branch E — Narratia Integration.** How the authorize-don't-author proposal engine works. What "observing intent" means for a general-purpose language. The role of Narratia Core.

**Branch F — Event-Driven Execution (v2).** Design the listener model for `when`/`unless`. Define event sources. Architect the transition from sequential to reactive interpreter. Required before healthcare, smart home, and game design use cases are executable.

---

## WHAT IS LOCKED

This inception checkpoint locks:

- **Project concept:** A general-purpose programming language designed from Inscript's principles — prose-as-syntax, bounded vocabulary, tile composition, graduation from tiles to prose, authorize-don't-author — for people who have never coded (§1, §2)
- **Design lineage:** Narratia (Freirean pedagogy-first) → Möbius Inscript (behavioral DSL) → Inscript Programming Language (general computation) (§3, §4, §5)
- **Five novel properties:** The combination of prose-as-syntax, tile composition, graduation within one language, authorize-don't-author, and non-programmer design origin occupies genuinely unoccupied territory in the programming language landscape (§7)
- **Pipeline architecture:** Lexer (vocabulary lookup), parser (with reorderer), semantic analyzer (live, during composition), interpreter (starting from working programs) (§8, §9)
- **Concept-layer vocabulary:** The language names what people are trying to do, not how the machine does it (§10)
- **Three-surface graduation model:** Tiles, prose, and symbolic text as three views of the same AST (§12)
- **Host language:** Python (§14)
- **Build scope for v1:** Interpreter, seven verbs, text input, tile interface as separate layer (§16, §25)
- **v1/v2 execution model distinction:** v1 is sequential (run and finish). `when`/`unless` temporal connectives and `transform`/`choose`/`compare` verbs are designed but deferred to v2. Use cases split accordingly. (§11, §13, §21, §25)
- **Reorderer architecture:** Slot filling — each verb defines a signature of expected slots, reorderer matches words to slots by category tag. Ambiguity produces clarification prompt, not silent assumption. Component patterns confirmed in Narratia and Loom codebases. (§17, §18)
- **Vocabulary scaling architecture:** Base vocabulary stays permanently small. Expressiveness scales through four mechanisms: domain packs, composition, named compositions (chunking), and sentence complexity cap. (§19)
- **Vocabulary governance:** The word salad test — any new word must be understandable by a non-programmer in context without explanation. (§20)
- **Domain packs as adoption path:** Each domain pack is a product. The base language is infrastructure; domain packs are surfaces. (§19)
- **Parser rules:** `and`/`or` context-dependency resolved via parser state + lookahead (four meanings, deterministic disambiguation). `is` dual role resolved via lookahead. `not` as genuine operator modifier with own comparison semantics (`not above` ≠ `below`). Compound conditions via recursive nesting. v1 verb set: seven verbs with fully specified semantics. (§21)
- **Lexer specification:** Case-insensitive, comma/punctuation stripping, multi-word token handling for `equal to`, number recognition, colon delimiter, hyphen-valid names, unknown word partial classification deferred to parser. (§22)
- **Structured records via `as`:** `remember an order with total as 75 and status as active` creates typed records with named fields, enabling field-based filtering — the core business rules use case. (§23)
- **Type inference:** Types inferred from values, stored in symbol table. No explicit annotations required for v1. (§23)
- **Named composition validation split:** Grammar checked at definition time, name resolution at call time. (§23)
- **Interpreter behaviors:** Auto-show for standalone expressions. In-place modification for `filter`. Inline naming for `gather`. Copy semantics for all data operations. (§24)

This inception checkpoint does NOT lock:

- The project name (Inscript is the working label; naming is Q1)
- The relationship to Möbius Inscript (Q2)
- Specific domain pack vocabularies (require domain-expert input)
- The event-driven execution model for v2 (Q13)
- `transform`/`choose`/`compare` grammar (deferred to v2 with full specification)
- Any deployment target (Q7)
- Any visual identity decisions
- Any repository or infrastructure decisions

---

## RESUME PROMPT (Inscript Programming Language v1)

*We are resuming from the Inscript Programming Language Inception Checkpoint v1 (May 11, 2026). This is a standalone project — a general-purpose programming language designed from the principles of Möbius Inscript (prose-as-syntax, tile composition, authorize-don't-author, bounded vocabulary, graduation from tiles to prose) and rooted in Narratia's Freirean pedagogy-first philosophy. The lineage is Narratia → Möbius Inscript → this. Designed by a non-programmer for non-programmers as liberation infrastructure. Five novel properties occupy unoccupied territory: prose-as-syntax for general computation, tile composition, graduation within one language (three views, one AST), authorize-don't-author, and non-programmer design origin. The interpreter will be built in Python. Rob has completed Codecademy's Python fundamentals and is 21% through data structures. CRITICAL SCOPE: v1 is sequential execution. v1 verb set: `remember`, `show`, `filter`, `count`, `gather`, `combine`, `each` (7 verbs). v1 connectives: `where`, `and`, `or`, `from`, `with`, `called`, `to`, `how`, `as` (9). v1 operators: `is`, `above`, `below`, `equal to`, `not` (5). Deferred to v2: `when`/`unless` (event-driven), `transform`/`choose`/`compare` (under-specified semantics). PIPELINE FULLY SPECIFIED: Lexer — case-insensitive, comma-stripping, multi-word `equal to`, number recognition, colon delimiter, unknown words refined by parser. Parser — slot filling with verb signatures, `and`/`or` disambiguated by parser state + lookahead (four meanings), `is` dual role via lookahead, `not` as genuine operator modifier (`not above` ≠ `below`), compound conditions via recursive nesting, `each` wraps sub-operations via recursive descent. Semantic analyzer — symbol table with types (inferred from values), structured records via `as` connective (enabling field-based filtering for business rules), named composition validation split (grammar at definition, names at call). Interpreter — sequential, auto-show for standalone expressions, in-place `filter` modification, inline `gather` naming, copy semantics. Reorderer uses slot filling; component patterns confirmed in Narratia and Loom codebases. Vocabulary scaling: domain packs, composition, named compositions, sentence complexity cap; base vocabulary stays small; word salad test governs additions. v1 use cases: business rules, legal compliance, data filtering. v2 use cases: healthcare monitoring, smart home, game design (require event-driven execution). Build sequence: vocabulary design → lexer → parser → interpreter → tile interface. Six branches: Vocabulary Design, Python Build, Tile Interface, Identity/Positioning, Narratia Integration, Event-Driven Execution (v2).*

---

## PROVENANCE NOTE

This document was verified against:

- **v7.5g Inscript Resolution** (April 17, 2026): Inscript as DSL confirmed at §11 (line 136–140). Core syntactic shape "When X, then Y" confirmed at §12 (line 146). Prose-as-syntax design invariant confirmed at §13 (line 165–169): "valid inscriptions are readable as English prose. Syntactic constructs that break this invariant are rejected." Authorize-don't-author on-ramp confirmed at §19 (line 260). Bounded, enumerable runnable primitives confirmed at §7 (line 94). "LOCKED in principle" confirmed. DSL boundary — "verbs are Möbius verbs" — confirmed at §11 (line 136).
- **v7.5h Tile Composition Addendum** (April 17, 2026): Tile composition as first-encounter interaction model confirmed at §25 (line 34–36): "tile composition from a pre-given vocabulary set — not freeform text entry, not a form wizard, not a code editor." Bounded vocabulary made tactile confirmed at §26 (line 50). Graduation from tiles to prose confirmed at §27 (line 56–58): "As inscriptions grow complex, the interaction surface graduates from tile arrangement to prose editing of the same syntax." Graduation as design invariant confirmed (line 58).
- **v8.11 Inscript Grammar** (May 2, 2026): Grammar scope and constraints confirmed at §274: "no variables, no loops, no user-defined functions, and no side effects." Four clause types (trigger, condition, action, scope) confirmed at §275. CompositionStrip reorderer confirmed at §283: "The person can arrange tiles in whatever order feels natural — the CompositionStrip does not enforce BNF clause order. A reorderer silently maps the arrangement to a valid BNF derivation before the parser sees it." Validity indicator (green check / amber with description) confirmed at §283.
- **v8.9 Narrative Core Integration** (April 29, 2026): Narratia Core as meaning-formation engine powering Inscript tile composition confirmed at §245. Narratia Core operates upstream of tile surface confirmed at §246. Narratia Core properties (accepts raw input, orders meaning before output, preserves voice, constraint-aware, co-generation mode) confirmed at §245.
- **"One Thesis, Four Depths" insight capture** (April 19, 2026): Narratia-to-Inscript chain as connective tissue confirmed (line 40, 50, 54, 56). Freire reference confirmed (line 56): "Education as liberation, not consumption. Learners author their own narratives rather than absorb dominant ones." Four expressions of one thesis confirmed. Authorship as through-line confirmed (line 50): "The person affected must remain the author."
- **C* (C-Asterisk) project** (`TheJudge26/C-Asterisk-Alpha`): Verified via web fetch (May 11, 2026). College compiler construction project confirmed. Python frontend with LLVM backend confirmed. Hand-written lexer, parser, semantic analyzer, codegen confirmed. Mojo inspiration acknowledged. MIT license confirmed. 11 stars, 24 commits at time of fetch.
- **Inform 7**: Verified via web search (May 11, 2026). Natural language programming for interactive fiction confirmed. Created by Graham Nelson, April 2006. Open-sourced April 2022. TIOBE top 100 ranking confirmed. "Easy to read, hard to write" characterization confirmed via Inform 7 Programmer's Manual.
- **Block-based language landscape**: Verified via web search (May 11, 2026). Scratch → C (Harvard CS50), Snap! → Python (Berkeley CS10) graduation pattern confirmed. Mind+ block-to-Python dual view confirmed. No existing tool providing graduation within a single prose-based language was found.
- **Codecademy progress**: Verified from uploaded documents (May 11, 2026). "Learn How to Code" certificate (May 3, 2025, verification code 9B18CC5C-5) confirmed. "Code Foundations Skill Path" certificate (May 3, 2025, verification code B40AA5E0-8) confirmed. "Intro to Programming" at 68%: Fundamentals of Python (complete), Programming in Python on Your Computer (complete), Basic Python Data Structures and Objects (21%) confirmed from screenshot.
- **Filename:** `inscript_inception_checkpoint_v1.md` — domain `inscript` (provisional, pre-vault), class `inception_checkpoint` (per skill table), version `v1`, no subtitle. Verified against naming grammar in rmt-working-documents skill.
- **Narratia MVP codebase** (`rmichaelthomas/narratia-mvp`): Scanned via GitHub MCP (May 11, 2026). `utils.py` (sha: 4425e83): `naive_outline()` confirmed — splits freewrite into sentences, groups into 3–6 ordered beats (structural reordering of unstructured input). `llm_outline_safe()` confirmed — AI-enhanced outline with voice preservation prompt: "Use the user's language and phrasing where natural to preserve their voice." `ethics_pass()` confirmed — deterministic pattern matching against known risky terms with reflection prompts (bounded constraint checker). Two-tier heuristic-fallback + AI architecture confirmed across all `llm_*_safe()` functions. `app.py` (sha: be61a0f): Flask app, full pipeline flow (freewrite → outline → draft → ethics) confirmed.
- **Loom by Narratia MVP codebase** (`rmichaelthomas/loom-by-narratia-mvp`): Scanned via GitHub MCP (May 11, 2026). `server/rules.js` (sha: 527450e): `hasAny()` confirmed — bounded vocabulary lookup checking text against known phrase sets. `runGrantFit()` confirmed — takes baseline canon + grant text, pattern-matches known phrases, detects contradictions between inputs, produces scored dimensions (mission, scope, ethics, stretch) with human-readable reasons (e.g., "Grant pressures youth engagement; canon is adult-only"). Flags confirmed: `YOUTH_PRESSURE`, `GUARANTEE_PRESSURE`, `SCALE_PRESSURE`, `FRAMING_PRESSURE`. `runIntegrity()` confirmed — post-draft validation checking AI output against baseline canon for contradictions. `server/server.js` (sha: 5071f62): Full Loom pipeline confirmed (session create → fit check → draft → commit → integrity report → export).
- **Internal consistency correction** (May 11, 2026): The initial draft of this checkpoint listed healthcare protocols ("when blood pressure exceeds 180, alert the physician") and smart home automation ("when I leave the house after sunset, turn off the lights") as use cases in §13 without distinguishing that both require event-driven execution (`when` clauses), while §16 locked the v1 interpreter as sequential. This contradiction was identified by external review (Gemini's thirty example sentences surfaced the v1/v2 execution model gap). The correction: §11 now splits the vocabulary into v1 (sequential) and v2 (event-driven) tiers. §13 now explicitly categorizes each use case as v1 or v2. Q13 and Q14 added to the open questions table. Branch F added. This failure mode — claiming a use case is achievable without verifying the architecture in the same document supports it — is now logged as a process requirement: every checkpoint gets an internal consistency pass before shipping.
- **Pipeline component review** (May 11, 2026): Every verb, connective, and operator was traced through the lexer, parser, semantic analyzer, and interpreter to identify execution failures — not pattern-matched against expected behavior. Findings: (1) Parser — `and`/`or` have four context-dependent meanings requiring parser state + lookahead; `is` has dual role requiring lookahead; `not` as operator modifier produces distinct semantics from operator swapping (`not above 50` = ≤ 50, not `below 50` = < 50); `transform`/`choose`/`compare` have under-specified semantics and are deferred to v2. (2) Lexer — `equal to` is a multi-word token requiring lookahead; `to`, `how`, and `as` were missing from vocabulary table; `:` is a delimiter not recognized by the lexer; unknown words cannot be fully classified by the lexer alone (parser completes classification by position). (3) Semantic analyzer — structured data gap: `filter the orders where total is above 50` requires structured records, but `remember` without `as` can only create flat values/lists; resolved by adding `as` connective for field assignment; type tracking required in symbol table. (4) Interpreter — standalone expressions need a destination (resolved: auto-show); `filter` in-place vs immutable (resolved: in-place for v1); `gather` implicitly names collections; copy semantics for all data. All resolutions captured in §21–§25.

---

*END OF THE INSCRIPT PROGRAMMING LANGUAGE INCEPTION CHECKPOINT v1*

*May 11, 2026*

*Freire said the oppressed must name their own world.*
*A programming language is a tool for naming.*
*The question was never whether non-programmers could think computationally.*
*The question was why we kept handing them someone else's language to do it in.*

*Begin anywhere.*
