# Phase 3 Interpreter Benchmark — existing pack verbs

Regression baseline for cite/verify/measure/validate. Each case records the final pack-verb result's status, failure_type, and message.

## B1 — cite pass
- status: `SUCCESS`
- failure_type: `—`
- message: `—`

## B2 — cite fail
- status: `PACK_VERB_FAILURE`
- failure_type: `substring_not_found`
- message: `The text 'deficit' was not found in 'the-source'. The source begins: 'revenue was 100'`

## B3 — verify structural mismatch
- status: `PACK_VERB_FAILURE`
- failure_type: `comparison_mismatch`
- message: `'the-claim' does not match 'the-source'. Status: mismatch.`

## B4 — measure outside tolerance
- status: `PACK_VERB_FAILURE`
- failure_type: `outside_tolerance`
- message: `Claimed 100 but closest value in 'the-source' is 150 (delta: 50, tolerance: 1).`

## B5 — validate range mismatch
- status: `PACK_VERB_FAILURE`
- failure_type: `range_mismatch`
- message: `Claimed range 10 to 25 does not match 'the-window' (10 to 20) — divergence: upper.`
