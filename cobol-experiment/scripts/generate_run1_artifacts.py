#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "translations"


def source(repo: str, rel: str, start: int, end: int) -> dict:
    urls = {
        "learn_cobol": "https://github.com/kalsmic/learn_cobol",
        "cobol-samples": "https://github.com/neopragma/cobol-samples",
        "mortgagesample": "https://github.com/rradclif/mortgagesample",
    }
    return {
        "repo": repo,
        "url": urls[repo],
        "rel": rel,
        "path": ROOT / "corpus" / "_fetched" / rel,
        "start": start,
        "end": end,
    }


RULES: list[dict] = [
    {
        "slug": "learn_cobol__AGE-CHECK",
        "source_repo": "learn_cobol",
        "program": "AGE-CHECK",
        "summary": "classifies whether a person is over 21",
        "source": source("learn_cobol", "learn_cobol/AGE-CHECK.cobol", 13, 20),
        "expressibility": "base",
        "verbs": ["permit"],
        "limn": """about "age check"

remember a value called age with 22

permit age is above 21 because "COBOL branch says age > 21"
permit age is below 22 because "else branch is age <= 21 for integer ages"

show "Age threshold evaluated."
""",
        "events": [
            {"kind": "boundary", "cobol": "age <= 21", "limn": "age is below 22", "risk": "else branch made explicit; faithful for integer PIC 999 ages", "recorded_in_because": True}
        ],
        "prose": "This rule separates people over 21 from people 21 or younger. The COBOL only writes the greater-than branch; the else branch was made explicit and is faithful for integer ages.",
    },
    {
        "slug": "learn_cobol__RETIREMENT-AGE",
        "source_repo": "learn_cobol",
        "program": "RETIREMENT-AGE",
        "summary": "women retire at 60, men at 65",
        "source": source("learn_cobol", "learn_cobol/RETIREMENT-AGE.cobol", 5, 32),
        "expressibility": "base",
        "verbs": ["permit"],
        "limn": """about "retirement eligibility"

remember a value called gender with "F"
remember a value called age with 62

permit gender is "F" and age is above 59 because "female condition name means gender F and COBOL age >= 60 is inclusive"
permit gender is "M" and age is above 64 because "male condition name means gender M and COBOL age >= 65 is inclusive"

show "Retirement thresholds evaluated."
""",
        "events": [
            {"kind": "boundary", "cobol": "age >= 60", "limn": "age is above 59", "risk": "inclusive-vs-exclusive; faithful for integer ages only", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "age >= 65", "limn": "age is above 64", "risk": "inclusive-vs-exclusive; faithful for integer ages only", "recorded_in_because": True},
            {"kind": "precedence", "cobol": "female AND age >= 60 OR male AND age >= 65", "limn": "two permit lines", "risk": "COBOL AND/OR grouping made explicit", "recorded_in_because": True},
        ],
        "prose": "The COBOL hides gender meanings behind 88-level condition names and relies on operator precedence. The Liminate version expands both branches so the thresholds and grouping are visible.",
    },
    {
        "slug": "learn_cobol__PAY-CALCULATION",
        "source_repo": "learn_cobol",
        "program": "PAY-CALCULATION",
        "summary": "overtime pay applies above 37.5 hours at 1.5 times rate",
        "source": source("learn_cobol", "learn_cobol/PAY-CALCULATION.cobol", 5, 23),
        "expressibility": "base",
        "verbs": ["remember", "permit"],
        "limn": """about "overtime pay calculation"

remember a value called hours-worked with 42.5
remember a value called rate-of-pay with 12.00
remember a value called standard-hours with 37.5
remember a value called overtime-hours with hours-worked minus standard-hours because "COBOL computes overtime only when hours-worked > std-hours"
remember a value called standard-pay with standard-hours multiplied by rate-of-pay because "standard pay portion is standard-hours times rate"
remember a value called overtime-pay with 1.5 multiplied by rate-of-pay multiplied by overtime-hours because "overtime premium is 1.5 times rate for hours above 37.5"
remember a value called total-pay with standard-pay plus overtime-pay because "COBOL COMPUTE pay ROUNDED adds standard and overtime portions"

permit hours-worked is above standard-hours because "COBOL overtime branch uses strict > 37.5"

show total-pay
""",
        "events": [
            {"kind": "rounding", "cobol": "COMPUTE pay ROUNDED", "limn": "remember total-pay with standard-pay plus overtime-pay", "risk": "base Liminate arithmetic does not declare COBOL rounding mode", "recorded_in_because": True}
        ],
        "prose": "The overtime formula itself fits base Liminate. The audit risk is rounding: COBOL says ROUNDED, while this base translation can show the formula but not the exact target-picture rounding behavior.",
    },
    {
        "slug": "learn_cobol__PAY-MODULAR-VERSION",
        "source_repo": "learn_cobol",
        "program": "PAY-MODULAR-VERSION",
        "summary": "modular version of overtime pay above 37.5 hours",
        "source": source("learn_cobol", "learn_cobol/PAY-MODULAR-VERSION.cobol", 28, 37),
        "expressibility": "base",
        "verbs": ["remember", "permit"],
        "limn": """about "modular overtime pay calculation"

remember a value called hours-worked with 36.5
remember a value called rate-of-pay with 12.00
remember a value called standard-hours with 37.5
remember a value called regular-pay with hours-worked multiplied by rate-of-pay because "COBOL else branch computes hours-worked times rate when hours are not above standard"

permit hours-worked is below 37.51 because "COBOL else branch means hours-worked <= 37.5; PIC 99V99 makes 37.51 the next centesimal boundary"

show regular-pay
""",
        "events": [
            {"kind": "boundary", "cobol": "hours-worked <= 37.5", "limn": "hours-worked is below 37.51", "risk": "inclusive decimal boundary assumes PIC 99V99 centesimal precision", "recorded_in_because": True},
            {"kind": "rounding", "cobol": "COMPUTE pay ROUNDED", "limn": "remember regular-pay with hours-worked multiplied by rate-of-pay", "risk": "target-picture rounding not represented in base vocabulary", "recorded_in_because": True},
        ],
        "prose": "This is the same pay rule written in paragraphs. The non-overtime branch is expressible, but the decimal boundary and COBOL rounding are explicit audit events.",
    },
    {
        "slug": "learn_cobol__ELECTRICITY-BILL",
        "source_repo": "learn_cobol",
        "program": "ELECTRICITY-BILL",
        "summary": "reject negative usage and calculate tiered electricity charge",
        "source": source("learn_cobol", "learn_cobol/ELECTRICITY-BILL.cobol", 6, 47),
        "expressibility": "base",
        "verbs": ["remember", "forbid", "permit"],
        "limn": """about "electricity bill"

remember a value called present-reading with 250
remember a value called previous-reading with 100
remember a value called basic-units with 72
remember a value called basic-rate with 0.035
remember a value called cheap-rate with 0.009
remember a value called standing-charge with 2.50
remember a value called vat with 0.08
remember a value called units with present-reading minus previous-reading because "COBOL computes units as present reading minus previous reading"
remember a value called basic-charge with basic-units multiplied by basic-rate because "first 72 units use the basic rate"
remember a value called extra-units with units minus basic-units because "units above 72 use the cheap rate"
remember a value called extra-charge with extra-units multiplied by cheap-rate because "COBOL charges excess units at cheap rate"
remember a value called charge with basic-charge plus extra-charge because "COBOL tiered branch adds basic and excess charges before VAT"
remember a value called charge-before-vat with charge plus standing-charge because "COBOL adds the standing charge before VAT"
remember a value called vat-multiplier with 1 plus vat because "COBOL computes charge-out using 1 plus VAT"
remember a value called charge-out with charge-before-vat multiplied by vat-multiplier because "COBOL applies VAT to charge plus standing charge"

forbid units is below 0 because "COBOL units NEGATIVE branch is an error"
permit units is above basic-units because "COBOL tiered branch uses strict units > basic-units"

show charge-out
""",
        "events": [
            {"kind": "sign", "cobol": "IF units NEGATIVE", "limn": "forbid units is below 0", "risk": "negative usage is treated as rejection", "recorded_in_because": True},
            {"kind": "rounding", "cobol": "COMPUTE charge ROUNDED", "limn": "remember charge with basic-charge plus extra-charge", "risk": "COBOL target rounding is not represented", "recorded_in_because": True},
        ],
        "prose": "The core billing rule fits: negative consumption is forbidden and units above 72 move into a second rate. The base translation does not model target-field rounding or display formatting.",
    },
    {
        "slug": "learn_cobol__PROCESS-MARKS",
        "source_repo": "learn_cobol",
        "program": "PROCESS-MARKS",
        "summary": "classifies average marks into four bands",
        "source": source("learn_cobol", "learn_cobol/PROCESS-MARKS.cobol", 24, 33),
        "expressibility": "base",
        "verbs": ["remember", "permit"],
        "limn": """about "student mark classification"

remember a value called english-marks with 68
remember a value called math-marks with 72
remember a value called total-marks with english-marks plus math-marks because "COBOL adds English and math marks before dividing"
remember a value called average-mark with total-marks divided by 2 because "COBOL EVALUATE classifies the average of English and math marks"

permit average-mark is above 39.9 and average-mark is below 50 because "COBOL WHEN 40 THRU 49.9 is inclusive at both endpoints"
permit average-mark is above 49.9 and average-mark is below 60 because "COBOL WHEN 50 THRU 59.9 is inclusive at both endpoints"
permit average-mark is above 59.9 and average-mark is below 70 because "COBOL WHEN 60 THRU 69.9 is inclusive at both endpoints"
permit average-mark is above 69.9 and average-mark is below 100.1 because "COBOL WHEN 70 THRU 100 is inclusive; 100.1 records the decimal boundary assumption"

show average-mark
""",
        "events": [
            {"kind": "boundary", "cobol": "40 THRU 49.9", "limn": "average-mark is above 39.9 and average-mark is below 50", "risk": "inclusive range rewritten through strict operators", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "50 THRU 59.9", "limn": "average-mark is above 49.9 and average-mark is below 60", "risk": "inclusive range rewritten through strict operators", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "60 THRU 69.9", "limn": "average-mark is above 59.9 and average-mark is below 70", "risk": "inclusive range rewritten through strict operators", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "70 THRU 100", "limn": "average-mark is above 69.9 and average-mark is below 100.1", "risk": "upper boundary assumes one decimal place for the average", "recorded_in_because": True},
            {"kind": "precedence", "cobol": "(english-marks + math-marks) /2", "limn": "total-marks with english-marks plus math-marks; average-mark with total-marks divided by 2", "risk": "COBOL parentheses made explicit through an intermediate value", "recorded_in_because": True},
        ],
        "prose": "The classification bands can be expressed, but every `THRU` range becomes an audit boundary. The average calculation also exposes a precedence concern because the COBOL uses parentheses.",
    },
    {
        "slug": "learn_cobol__MORTGAGE",
        "source_repo": "learn_cobol",
        "program": "MORTGAGE",
        "summary": "computes yearly mortgage interest and ending balance",
        "source": source("learn_cobol", "learn_cobol/MORTGAGE.cobol", 33, 45),
        "expressibility": "base",
        "verbs": ["remember"],
        "limn": """about "simple mortgage year calculation"

remember a value called balance-start with 100000
remember a value called interest-rate with 5
remember a value called repayment with 500
remember a value called interest with balance-start multiplied by interest-rate divided by 100 because "COBOL computes interest as balance times rate divided by 100"
remember a value called annual-repayment with 12 multiplied by repayment because "COBOL subtracts twelve monthly repayments"
remember a value called balance-end with balance-start plus interest minus annual-repayment because "COBOL ending balance adds interest and subtracts annual repayments"

show balance-end
""",
        "events": [
            {"kind": "truncation", "cobol": "PIC 9(6)V99 targets", "limn": "unbounded base values", "risk": "base Liminate does not enforce COBOL target picture size or decimal scale", "recorded_in_because": True}
        ],
        "prose": "The annual mortgage arithmetic is readable in base Liminate. The missing fidelity is COBOL picture enforcement: the base language does not constrain the value to the original field size or scale.",
    },
    {
        "slug": "learn_cobol__TIME-AND-DATE",
        "source_repo": "learn_cobol",
        "program": "TIME-AND-DATE",
        "summary": "uses a 96 pivot to choose century for two-digit years",
        "source": source("learn_cobol", "learn_cobol/TIME-AND-DATE.cobol", 28, 39),
        "expressibility": "base",
        "verbs": ["remember", "permit"],
        "limn": """about "two digit year pivot"

remember a value called date-year with 25

permit date-year is below 96 because "COBOL maps YY < 96 to century 20"
permit date-year is above 95 because "COBOL else branch maps YY >= 96 to century 19"

show "Century pivot evaluated."
""",
        "events": [
            {"kind": "boundary", "cobol": "date-in-yy < 96", "limn": "date-year is below 96", "risk": "strict less-than is direct", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "date-in-yy >= 96", "limn": "date-year is above 95", "risk": "else branch inclusive boundary made explicit for integer YY", "recorded_in_because": True},
        ],
        "prose": "This is a classic two-digit-year pivot rule. It fits base Liminate, but the century cutoff is exactly the kind of boundary an auditor would want surfaced.",
    },
    {
        "slug": "learn_cobol__DISCOUNT",
        "source_repo": "learn_cobol",
        "program": "DISCOUNT",
        "summary": "subtracts discount from charge",
        "source": source("learn_cobol", "learn_cobol/DISCOUNT.cobol", 10, 17),
        "expressibility": "base",
        "verbs": ["remember"],
        "limn": """about "discount calculation"

remember a value called charge with 199.99
remember a value called discount with 20.00
remember a value called discounted-charge with charge minus discount because "COBOL subtracts discount from charge and rounds into display field"

show discounted-charge
""",
        "events": [
            {"kind": "rounding", "cobol": "GIVING discounted-charge ROUNDED", "limn": "discounted-charge with charge minus discount", "risk": "base Liminate does not declare COBOL rounded target-picture behavior", "recorded_in_because": True}
        ],
        "prose": "The arithmetic is simple and expressible. The fidelity risk is not the subtraction; it is the COBOL rounded display target.",
    },
    {
        "slug": "learn_cobol__BALANCE",
        "source_repo": "learn_cobol",
        "program": "BALANCE",
        "summary": "adds transaction amount to old balance",
        "source": source("learn_cobol", "learn_cobol/BALANCE.cobol", 12, 18),
        "expressibility": "base",
        "verbs": ["remember"],
        "limn": """about "balance update"

remember a value called amount with 125.50
remember a value called old-balance with 1000.00
remember a value called new-balance with amount plus old-balance because "COBOL ADD amount, old-balance GIVING new-balance"

show new-balance
""",
        "events": [{"kind": "none", "cobol": "ADD amount, old-balance", "limn": "amount plus old-balance", "risk": "no special boundary or rounding decision in the isolated rule", "recorded_in_because": True}],
        "prose": "This balance update fits cleanly in the base vocabulary. No special boundary or precedence decision is needed for the isolated addition.",
    },
    {
        "slug": "learn_cobol__COST",
        "source_repo": "learn_cobol",
        "program": "COST",
        "summary": "adds VAT and price to produce cost",
        "source": source("learn_cobol", "learn_cobol/COST.cobol", 14, 21),
        "expressibility": "base",
        "verbs": ["remember"],
        "limn": """about "cost calculation"

remember a value called price with 100.00
remember a value called vat with 8.00
remember a value called cost-out with vat plus price because "COBOL ADD vat, price GIVING cost-out"

show cost-out
""",
        "events": [{"kind": "none", "cobol": "ADD vat, price GIVING cost-out", "limn": "vat plus price", "risk": "no special fidelity event in the isolated arithmetic", "recorded_in_because": True}],
        "prose": "The VAT addition is directly expressible in base Liminate. This rule has no boundary, sign, or rounding event in the excerpt.",
    },
    {
        "slug": "learn_cobol__ADDAMT",
        "source_repo": "learn_cobol",
        "program": "ADDAMT",
        "summary": "sums three input amounts",
        "source": source("learn_cobol", "learn_cobol/ADDAMT.cobol", 26, 33),
        "expressibility": "base",
        "verbs": ["remember"],
        "limn": """about "amount sum"

remember a value called amount-one with 10.00
remember a value called amount-two with 20.00
remember a value called amount-three with 30.00
remember a value called amount-total with amount-one plus amount-two plus amount-three because "COBOL ADD AMT1-IN AMT2-IN AMT3-IN computes their sum"

show amount-total
""",
        "events": [{"kind": "none", "cobol": "ADD AMT1-IN AMT2-IN AMT3-IN", "limn": "amount-one plus amount-two plus amount-three", "risk": "no special fidelity event in the isolated arithmetic", "recorded_in_because": True}],
        "prose": "The rule is a straight three-amount sum. It fits the base vocabulary without needing a domain pack.",
    },
    {
        "slug": "learn_cobol__SHOPPING-BILL",
        "source_repo": "learn_cobol",
        "program": "SHOPPING-BILL",
        "summary": "adds item cost to running shopping bill",
        "source": source("learn_cobol", "learn_cobol/SHOPPING-BILL.cobol", 12, 18),
        "expressibility": "base",
        "verbs": ["remember"],
        "limn": """about "shopping bill accumulation"

remember a value called total-bill with 25.50
remember a value called item-cost with 9.99
remember a value called updated-bill with total-bill plus item-cost because "COBOL ADD item-cost TO total-bill ROUNDED updates the running bill"

show updated-bill
""",
        "events": [
            {"kind": "rounding", "cobol": "ADD item-cost TO total-bill ROUNDED", "limn": "total-bill plus item-cost", "risk": "base Liminate does not model rounded accumulation into the target field", "recorded_in_because": True}
        ],
        "prose": "The running-total operation fits base Liminate. The risk is that COBOL rounds into the bill field after the add.",
    },
    {
        "slug": "learn_cobol__WORD-ORDER",
        "source_repo": "learn_cobol",
        "program": "WORD-ORDER",
        "summary": "chooses alphabetical order from a lexical comparison",
        "source": source("learn_cobol", "learn_cobol/WORD-ORDER.cobol", 11, 20),
        "expressibility": "pack-needed",
        "pack_needed": "collation and string-order comparison pack",
        "verbs": [],
        "events": [
            {"kind": "type-coercion", "cobol": "IF word-1 < word-2", "limn": "not expressed", "risk": "COBOL alphanumeric comparison depends on collating sequence", "recorded_in_because": False}
        ],
        "prose": "The rule depends on COBOL's alphanumeric ordering. Base Liminate has no explicit collation semantics, so a faithful translation needs a string-collation pack.",
    },
    {
        "slug": "learn_cobol__NET-PAY",
        "source_repo": "learn_cobol",
        "program": "NET-PAY",
        "summary": "subtracts tax and deductions from gross pay",
        "source": source("learn_cobol", "learn_cobol/NET-PAY.cobol", 18, 28),
        "expressibility": "pack-needed",
        "pack_needed": "packed-decimal currency rounding and signed display-size pack",
        "verbs": [],
        "events": [
            {"kind": "rounding", "cobol": "GIVING net-pay ROUNDED", "limn": "not expressed", "risk": "rounded signed display target must be preserved", "recorded_in_because": False},
            {"kind": "sign", "cobol": "PIC +999.99", "limn": "not expressed", "risk": "display sign behavior is part of the financial result", "recorded_in_because": False},
        ],
        "prose": "The subtraction formula is understandable, but the rule is about a signed packed-decimal result with size-error behavior. That needs a currency/display pack rather than a word-salad base translation.",
    },
    {
        "slug": "learn_cobol__COMPOUND-INTEREST",
        "source_repo": "learn_cobol",
        "program": "COMPOUND-INTEREST",
        "summary": "computes compound interest with exponentiation and size-error handling",
        "source": source("learn_cobol", "learn_cobol/COMPOUND-INTEREST.cobol", 23, 31),
        "expressibility": "pack-needed",
        "pack_needed": "financial exponentiation plus rounded currency overflow pack",
        "verbs": [],
        "events": [
            {"kind": "rounding", "cobol": "COMPUTE amount-at-end ROUNDED", "limn": "not expressed", "risk": "target rounding and overflow are material", "recorded_in_because": False},
            {"kind": "type-coercion", "cobol": "** years", "limn": "not expressed", "risk": "base arithmetic contract does not include exponentiation", "recorded_in_because": False},
        ],
        "prose": "This is a real financial rule, but base Liminate lacks exponentiation and COBOL size-error semantics. It should be counted as pack demand, not forced into invalid syntax.",
    },
    {
        "slug": "learn_cobol__INVESTIMENT",
        "source_repo": "learn_cobol",
        "program": "INVESTIMENT",
        "summary": "calculates investment interest and final amount with rounded packed fields",
        "source": source("learn_cobol", "learn_cobol/INVESTIMENT.cobol", 24, 46),
        "expressibility": "pack-needed",
        "pack_needed": "packed-decimal rounded currency and size-error pack",
        "verbs": [],
        "events": [
            {"kind": "rounding", "cobol": "GIVING temp ROUNDED / interest ROUNDED / amount-end-out ROUNDED", "limn": "not expressed", "risk": "multiple rounded targets affect the final amount", "recorded_in_because": False},
            {"kind": "truncation", "cobol": "ON SIZE ERROR", "limn": "not expressed", "risk": "overflow path cannot be expressed in base vocabulary", "recorded_in_because": False},
        ],
        "prose": "The interest formula is ordinary, but COBOL rounds at several intermediate fields and branches on size errors. Faithful translation needs a packed-decimal financial pack.",
    },
    {
        "slug": "learn_cobol__DIVIDE-NUMBER",
        "source_repo": "learn_cobol",
        "program": "DIVIDE-NUMBER",
        "summary": "divides a dividend by divisor and handles size errors",
        "source": source("learn_cobol", "learn_cobol/DIVIDE-NUMBER.cobol", 15, 25),
        "expressibility": "pack-needed",
        "pack_needed": "decimal division with divide-by-zero and size-error pack",
        "verbs": [],
        "events": [
            {"kind": "type-coercion", "cobol": "ON SIZE ERROR", "limn": "not expressed", "risk": "COBOL arithmetic exception path is not a base Liminate concept", "recorded_in_because": False}
        ],
        "prose": "A quotient can be written in base arithmetic, but this COBOL rule includes arithmetic exception handling. That exception contract is the missing domain behavior.",
    },
    {
        "slug": "learn_cobol__ADD-WITH-SIZE-ERROR",
        "source_repo": "learn_cobol",
        "program": "ADD-WITH-SIZE-ERROR",
        "summary": "adds values with rounded result and size-error branch",
        "source": source("learn_cobol", "learn_cobol/ADD-WITH-SIZE-ERROR.cobol", 18, 29),
        "expressibility": "pack-needed",
        "pack_needed": "rounded numeric target and size-error pack",
        "verbs": [],
        "events": [
            {"kind": "rounding", "cobol": "ADD in-1 TO in-2 GIVING result-1 ROUNDED", "limn": "not expressed", "risk": "rounded target behavior must be explicit", "recorded_in_because": False},
            {"kind": "truncation", "cobol": "ON SIZE ERROR", "limn": "not expressed", "risk": "target overflow path cannot be modeled by base vocabulary", "recorded_in_because": False},
        ],
        "prose": "The addition is simple, but the isolable rule includes both rounding and an overflow branch. That belongs in a numeric target/size-error pack.",
    },
    {
        "slug": "cobol-samples__COND88-CATEGORY",
        "source_repo": "cobol-samples",
        "program": "COND88-CATEGORY",
        "summary": "88-level category names map multiple literal values",
        "source": source("cobol-samples", "cobol-samples/src/main/cobol/COND88.CBL", 20, 75),
        "expressibility": "base",
        "verbs": ["remember", "permit"],
        "limn": """about "88 level category membership"

remember a value called category-code with "A"
remember a list called category-a-values with "A" and "3" and "7"
remember a list called category-b-values with "B" and "9" and "X"

permit category-a-values includes category-code because "COBOL 88 CATEGORY-A is true for A, 3, or 7"
permit category-b-values includes category-code because "COBOL 88 CATEGORY-B is true for B, 9, or X"

show "Category membership evaluated."
""",
        "events": [{"kind": "none", "cobol": "88 CATEGORY-A VALUE 'A', '3', '7'", "limn": "category-a-values includes category-code", "risk": "membership mapping is direct", "recorded_in_because": True}],
        "prose": "This 88-level pattern maps cleanly to list membership. The Liminate reader does not need to chase the condition-name declaration.",
    },
    {
        "slug": "cobol-samples__COND88-AGE-RANGES",
        "source_repo": "cobol-samples",
        "program": "COND88-AGE-RANGES",
        "summary": "88-level age names classify child through elderly ranges",
        "source": source("cobol-samples", "cobol-samples/src/main/cobol/COND88.CBL", 27, 97),
        "expressibility": "base",
        "verbs": ["remember", "permit"],
        "limn": """about "88 level age classification"

remember a value called person-age with 37

permit person-age is above -1 and person-age is below 13 because "COBOL PERSON-IS-A-CHILD is VALUE 0 THRU 12 inclusive"
permit person-age is above 12 and person-age is below 20 because "COBOL PERSON-IS-A-TEEN is VALUE 13 THRU 19 inclusive"
permit person-age is above 19 and person-age is below 36 because "COBOL PERSON-IS-YOUNG-ADULT is VALUE 20 THRU 35 inclusive"
permit person-age is above 35 and person-age is below 50 because "COBOL PERSON-IS-AN-ADULT is VALUE 36 THRU 49 inclusive"
permit person-age is above 49 and person-age is below 60 because "COBOL PERSON-IS-MIDDLE-AGED is VALUE 50 THRU 59 inclusive"
permit person-age is above 59 and person-age is below 75 because "COBOL PERSON-IS-A-SENIOR is VALUE 60 THRU 74 inclusive"
permit person-age is above 74 and person-age is below 201 because "COBOL PERSON-IS-ELDERLY is VALUE 75 THRU 200 inclusive"

show "Age range membership evaluated."
""",
        "events": [
            {"kind": "boundary", "cobol": "0 THRU 12", "limn": "person-age is above -1 and person-age is below 13", "risk": "inclusive integer range rewritten through strict operators", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "13 THRU 19", "limn": "person-age is above 12 and person-age is below 20", "risk": "inclusive integer range rewritten through strict operators", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "20 THRU 35", "limn": "person-age is above 19 and person-age is below 36", "risk": "inclusive integer range rewritten through strict operators", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "36 THRU 49", "limn": "person-age is above 35 and person-age is below 50", "risk": "inclusive integer range rewritten through strict operators", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "50 THRU 59", "limn": "person-age is above 49 and person-age is below 60", "risk": "inclusive integer range rewritten through strict operators", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "60 THRU 74", "limn": "person-age is above 59 and person-age is below 75", "risk": "inclusive integer range rewritten through strict operators", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "75 THRU 200", "limn": "person-age is above 74 and person-age is below 201", "risk": "inclusive integer range rewritten through strict operators", "recorded_in_because": True},
        ],
        "prose": "The 88-level age bands are expressible, but every range boundary becomes visible. That is useful: the translation exposes exactly where an off-by-one error would occur.",
    },
    {
        "slug": "cobol-samples__NOTBOOL-FLAGS",
        "source_repo": "cobol-samples",
        "program": "NOTBOOL-FLAGS",
        "summary": "pseudo-boolean conventions encode true values as T, Y, 1, or 88-level names",
        "source": source("cobol-samples", "cobol-samples/src/main/cobol/NOTBOOL.CBL", 65, 168),
        "expressibility": "base",
        "verbs": ["remember", "permit", "forbid"],
        "limn": """about "pseudo boolean flag conventions"

remember a value called ex-two-flag with "T"
remember a value called ex-three-flag with "Y"
remember a value called ex-four-flag with "1"
remember a value called ex-five-field with "T"
remember a value called ex-six-field with "T"

permit ex-two-flag is "T" because "COBOL convention treats T as true"
permit ex-three-flag is "Y" because "COBOL convention treats Y as yes"
permit ex-four-flag is "1" because "COBOL convention treats 1 as true"
permit ex-five-field is "T" because "COBOL 88 EX5-FLAG is true when the field is T"
permit ex-six-field is "T" because "COBOL 88 EX6-FLAG is true when the field is T and false when F"
forbid ex-six-field is "F" because "COBOL 88 FALSE value for EX6-FLAG is F"

show "Pseudo boolean conventions evaluated."
""",
        "events": [{"kind": "none", "cobol": "PIC X where T/Y/1/88-level values mean true", "limn": "literal equality permits", "risk": "literal conventions are direct once expanded", "recorded_in_because": True}],
        "prose": "The base vocabulary can hold legacy pseudo-boolean conventions once the magic values are named. The important translation step is to expose the convention, not to invent a boolean type.",
    },
    {
        "slug": "cobol-samples__IFEVAL-DIVIDE-GUARD",
        "source_repo": "cobol-samples",
        "program": "IFEVAL-DIVIDE-GUARD",
        "summary": "avoids divide-by-zero by requiring a divisor greater than zero",
        "source": source("cobol-samples", "cobol-samples/src/main/cobol/IFEVAL.CBL", 77, 93),
        "expressibility": "base",
        "verbs": ["remember", "require"],
        "limn": """about "divide by zero guard"

remember a value called divisor with 1
remember a value called dividend with 100

require divisor is above 0 because "COBOL divides only when NUMERIC-1 IS GREATER THAN ZERO"
remember a value called quotient with dividend divided by divisor because "division is permitted only after the positive-divisor guard"

show quotient
""",
        "events": [{"kind": "boundary", "cobol": "NUMERIC-1 IS GREATER THAN ZERO", "limn": "divisor is above 0", "risk": "strict positive boundary is direct", "recorded_in_because": True}],
        "prose": "This is a validation rule to avoid divide-by-zero. It maps cleanly to `require divisor is above 0` before the division.",
    },
    {
        "slug": "cobol-samples__IFEVAL-NUMERIC-CONFORMANCE",
        "source_repo": "cobol-samples",
        "program": "IFEVAL-NUMERIC-CONFORMANCE",
        "summary": "checks whether a field is numeric before arithmetic",
        "source": source("cobol-samples", "cobol-samples/src/main/cobol/IFEVAL.CBL", 65, 75),
        "expressibility": "pack-needed",
        "pack_needed": "numeric conformance predicate pack",
        "verbs": [],
        "events": [
            {"kind": "type-coercion", "cobol": "IF NUMERIC-2 IS NUMERIC", "limn": "not expressed", "risk": "base vocabulary has no numeric-conformance predicate for storage fields", "recorded_in_because": False}
        ],
        "prose": "The business intent is clear: check numeric shape before arithmetic. Base Liminate has values, but not COBOL's `IS NUMERIC` storage-conformance test.",
    },
    {
        "slug": "cobol-samples__IFEVAL-DUAL-EVALUATE",
        "source_repo": "cobol-samples",
        "program": "IFEVAL-DUAL-EVALUATE",
        "summary": "EVALUATE TRUE ALSO TRUE combines numeric comparison and string prefix checks",
        "source": source("cobol-samples", "cobol-samples/src/main/cobol/IFEVAL.CBL", 119, 144),
        "expressibility": "pack-needed",
        "pack_needed": "substring/prefix predicate and multi-axis evaluate pack",
        "verbs": [],
        "events": [
            {"kind": "precedence", "cobol": "EVALUATE TRUE ALSO TRUE", "limn": "not expressed", "risk": "multi-axis EVALUATE branch priority must be preserved", "recorded_in_because": False},
            {"kind": "type-coercion", "cobol": "ALPHA-1(1:3) EQUAL 'THX'", "limn": "not expressed", "risk": "base vocabulary lacks substring slicing", "recorded_in_because": False},
        ],
        "prose": "The branch logic combines two axes and substring predicates. A faithful readable translation needs a prefix/substring pack and explicit branch priority.",
    },
    {
        "slug": "cobol-samples__INVCALC",
        "source_repo": "cobol-samples",
        "program": "INVCALC",
        "summary": "calculates invoice line totals, taxable line tax, and cumulative invoice totals",
        "source": source("cobol-samples", "cobol-samples/src/main/cobol/INVCALC.CBL", 84, 125),
        "expressibility": "pack-needed",
        "pack_needed": "invoice line aggregation with currency scale and numeric conformance pack",
        "verbs": [],
        "events": [
            {"kind": "type-coercion", "cobol": "INV-LINE-QUANTITY IS NUMERIC", "limn": "not expressed", "risk": "numeric conformance guard is missing", "recorded_in_because": False},
            {"kind": "rounding", "cobol": "packed decimal line totals and tax fields", "limn": "not expressed", "risk": "currency scale and tax precision affect totals", "recorded_in_because": False},
        ],
        "prose": "This is business logic, but it is table-driven aggregation over invoice lines with numeric validation and tax precision. That is exactly the sort of domain pack the experiment is meant to reveal.",
    },
    {
        "slug": "mortgagesample__EPSMPMT-VALIDATION",
        "source_repo": "mortgagesample",
        "program": "EPSMPMT-VALIDATION",
        "summary": "validates mortgage principal and interest before calculating monthly payment",
        "source": source("mortgagesample", "mortgagesample/MortgageApplication/cobol/epsmpmt.cbl", 26, 117),
        "expressibility": "base",
        "verbs": ["remember", "require", "forbid"],
        "limn": """about "mortgage payment input validation"

remember a value called principal-amount with 250000
remember a value called maximum-principal with 100000000.01
remember a value called quoted-interest-rate with 5.75
remember a value called year-month-indicator with "Y"
remember a value called number-of-years with 30
remember a value called number-of-months with number-of-years multiplied by 12 because "COBOL converts years to months when the year-month indicator is Y"

require principal-amount is above 0 because "COBOL error 1 is principal amount not greater than zero"
forbid principal-amount is above maximum-principal because "COBOL error 2 is principal exceeding static maximum"
require quoted-interest-rate is above 0 because "COBOL error 3 is quoted interest rate <= 0"

show number-of-months
""",
        "events": [
            {"kind": "boundary", "cobol": "EPSPDATA-PRINCIPLE-DATA > 0", "limn": "principal-amount is above 0", "risk": "strict positive boundary is direct", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "EPSPDATA-PRINCIPLE-DATA > STATIC-MAXIMUM-PRINCIPLE", "limn": "forbid principal-amount is above maximum-principal", "risk": "strict maximum boundary is direct", "recorded_in_because": True},
            {"kind": "boundary", "cobol": "EPSPDATA-QUOTED-INTEREST-RATE <= 0", "limn": "require quoted-interest-rate is above 0", "risk": "negative/zero interest rejection restated as positive requirement", "recorded_in_because": True},
        ],
        "prose": "The mortgage validation thresholds fit base Liminate very well. The translation states each rejection condition as a readable requirement or prohibition.",
    },
    {
        "slug": "mortgagesample__EPSMPMT-PAYMENT-FORMULA",
        "source_repo": "mortgagesample",
        "program": "EPSMPMT-PAYMENT-FORMULA",
        "summary": "calculates amortized monthly payment using exponentiation",
        "source": source("mortgagesample", "mortgagesample/MortgageApplication/cobol/epsmpmt.cbl", 120, 141),
        "expressibility": "pack-needed",
        "pack_needed": "mortgage amortization formula pack with exponentiation and decimal precision",
        "verbs": [],
        "events": [
            {"kind": "rounding", "cobol": "EPSPDATA-RETURN-MONTH-PAYMENT target", "limn": "not expressed", "risk": "payment precision is financially material", "recorded_in_because": False},
            {"kind": "type-coercion", "cobol": "** WS-NUMBER-OF-MONTHS", "limn": "not expressed", "risk": "base vocabulary lacks exponentiation and amortization primitive", "recorded_in_because": False},
        ],
        "prose": "The payment formula is central banking logic, but base Liminate cannot express exponentiation or the payment target's numeric precision. This is a strong pack-demand signal.",
    },
    {
        "slug": "mortgagesample__EPSNBRVL-NUMBER-PARSER",
        "source_repo": "mortgagesample",
        "program": "EPSNBRVL-NUMBER-PARSER",
        "summary": "validates numeric text by trimming spaces, allowing commas, and detecting decimal errors",
        "source": source("mortgagesample", "mortgagesample/MortgageApplication/cobol/epsnbrvl.cbl", 83, 185),
        "expressibility": "pack-needed",
        "pack_needed": "numeric text parsing and decimal-point validation pack",
        "verbs": [],
        "events": [
            {"kind": "type-coercion", "cobol": "EPSPARM-VALIDATE-DATA(WS-IDX:1) IS NOT NUMERIC", "limn": "not expressed", "risk": "character-by-character numeric validation is outside base vocabulary", "recorded_in_because": False},
            {"kind": "boundary", "cobol": "UNTIL WS-IDX > WS-END-SPACE / < WS-LEADING-SPACES", "limn": "not expressed", "risk": "loop boundaries govern which characters are accepted", "recorded_in_because": False},
        ],
        "prose": "This routine is a validation rule over numeric text, not just plumbing. Faithful expression needs a parser-like pack for spaces, commas, decimals, and digit predicates.",
    },
    {
        "slug": "mortgagesample__EPSMLIST-CICS-NAVIGATION",
        "source_repo": "mortgagesample",
        "program": "EPSMLIST-CICS-NAVIGATION",
        "summary": "routes CICS screen behavior by AID key and communication state",
        "source": source("mortgagesample", "mortgagesample/MortgageApplication/cobol/epsmlist.cbl", 95, 115),
        "expressibility": "pack-needed",
        "pack_needed": "CICS screen-event routing pack",
        "verbs": [],
        "events": [
            {"kind": "precedence", "cobol": "EIBAID = DFHPF3 OR DFHPF12", "limn": "not expressed", "risk": "event-key routing semantics must preserve CICS constants", "recorded_in_because": False}
        ],
        "prose": "This is a UI routing rule rather than financial calculation. It is isolable, but it needs a CICS event/screen pack to be readable and faithful.",
    },
    {
        "slug": "mortgagesample__EPSCMORT-SCREEN-FLOW",
        "source_repo": "mortgagesample",
        "program": "EPSCMORT-SCREEN-FLOW",
        "summary": "routes mortgage CICS screen flow by aid key and process indicator",
        "source": source("mortgagesample", "mortgagesample/MortgageApplication/cobol_cics_db2/epscmort.cbl", 80, 141),
        "expressibility": "pack-needed",
        "pack_needed": "CICS mortgage screen-flow and DB2 state pack",
        "verbs": [],
        "events": [
            {"kind": "precedence", "cobol": "EVALUATE TRUE with nested PROCESS-INDICATOR checks", "limn": "not expressed", "risk": "screen flow depends on CICS AID constants and process state", "recorded_in_because": False}
        ],
        "prose": "The rule is a screen-flow decision, but base Liminate has no CICS AID-key vocabulary or DB2-backed state model. A domain pack would make it expressible.",
    },
    {
        "slug": "mortgagesample__EPSCSMRD-XML-CONTENT",
        "source_repo": "mortgagesample",
        "program": "EPSCSMRD-XML-CONTENT",
        "summary": "builds XML/content buffers through low-level generated COBOL routines",
        "source": source("mortgagesample", "mortgagesample/MortgageApplication/cobol_cics/epscsmrd.cbl", 3877, 3904),
        "expressibility": "untranslatable",
        "pack_needed": None,
        "verbs": [],
        "events": [
            {"kind": "type-coercion", "cobol": "generated buffer index and pointer arithmetic", "limn": "not expressed", "risk": "not an isolable business rule in human policy terms", "recorded_in_because": False}
        ],
        "prose": "This excerpt is generated-style buffer manipulation, not a human business rule. Even with a pack, translating it would test COBOL mechanics rather than Liminate's business-rule expressibility.",
    },
]


SCANNED_PROGRAMS = 61


def read_excerpt(src: dict) -> str:
    lines = src["path"].read_text(errors="replace").splitlines()
    body = lines[src["start"] - 1 : src["end"]]
    header = [
        f"* Attribution: {src['url']}",
        f"* Upstream file: {src['rel']}",
        f"* Excerpt lines: {src['start']}-{src['end']} (rule-bearing excerpt only; not whole file)",
        "",
    ]
    return "\n".join(header + body) + "\n"


def note_json(rule: dict, accepted: bool) -> dict:
    return {
        "source_repo": rule["source_repo"],
        "program": rule["program"],
        "rule_summary": rule["summary"],
        "expressibility": rule["expressibility"],
        "pack_needed": rule.get("pack_needed"),
        "verbs_used": rule.get("verbs", []),
        "fidelity_events": rule["events"],
        "interpreter_accepted": accepted,
    }


def write_rule(rule: dict) -> dict:
    out = TRANSLATIONS / rule["slug"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "source.cobol").write_text(read_excerpt(rule["source"]))
    accepted = False
    if rule["expressibility"] == "base":
        (out / "rule.limn").write_text(rule["limn"])
        proc = subprocess.run(
            ["liminate", str(out / "rule.limn")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        (out / "actual.txt").write_text(proc.stdout + proc.stderr)
        accepted = proc.returncode == 0
        if not accepted:
            raise RuntimeError(f"{rule['slug']} failed: {proc.stdout}{proc.stderr}")
    else:
        stale = out / "rule.limn"
        if stale.exists():
            stale.unlink()
        stale_actual = out / "actual.txt"
        if stale_actual.exists():
            stale_actual.unlink()

    payload = note_json(rule, accepted)
    (out / "notes.md").write_text("```json\n" + json.dumps(payload, indent=2) + "\n```\n\n" + rule["prose"] + "\n")
    return payload


def percent(count: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{count * 100 / total:.1f}%"


def repo_sha(path: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT / "corpus" / "_fetched" / path), "rev-parse", "HEAD"], text=True).strip()


def write_results(rules: list[dict]) -> None:
    counts = Counter(rule["expressibility"] for rule in rules)
    attempted = len(rules)
    pack_counts = Counter(rule["pack_needed"] for rule in rules if rule.get("pack_needed"))
    event_counts = Counter(event["kind"] for rule in rules for event in rule["fidelity_events"])
    verb_counts = Counter(verb for rule in rules for verb in rule["verbs_used"])
    liminate_version = subprocess.check_output(["liminate", "--version"], text=True).strip()
    shas = {
        "learn_cobol": repo_sha("learn_cobol"),
        "cobol-samples": repo_sha("cobol-samples"),
        "mortgagesample": repo_sha("mortgagesample"),
    }
    boundary_rows = [
        (rule["program"], event["kind"], event["cobol"], event["limn"], event["risk"])
        for rule in rules
        for event in rule["fidelity_events"]
        if event["kind"] in {"boundary", "rounding", "sign"}
    ]
    data = {
        "run_header": {
            "date": date.today().isoformat(),
            "interpreter_version": liminate_version,
            "corpus_commit_shas": shas,
            "total_programs_scanned": SCANNED_PROGRAMS,
            "total_with_isolable_rules": attempted,
            "total_attempted": attempted,
        },
        "expressibility": {
            "base": counts["base"],
            "pack-needed": counts["pack-needed"],
            "untranslatable": counts["untranslatable"],
        },
        "pack_demand": dict(pack_counts),
        "fidelity_events": dict(event_counts),
        "verb_frequency": dict(verb_counts),
        "rules": rules,
        "findings": [
            "Base Liminate carried the small threshold, membership, guard, and arithmetic rules, but COBOL's financial target semantics pushed many realistic calculations into pack-needed territory.",
            "The strongest pack-demand signal is not COBOL syntax itself; it is domain fidelity around rounded packed decimals, size-error paths, numeric conformance, string slicing, and amortization.",
            "The fidelity surface is concentrated in boundaries and rounding: the translations that pass are readable precisely because every inclusive range, else-branch boundary, and rounded target is called out instead of hidden.",
        ],
        "honesty_boundary": "This run uses a small learning/sample corpus, not production mainframe portfolios; it uses one interpreter version, Liminate 0.14.1; and no human COBOL auditor or bank compliance reviewer certified the translations.",
    }
    (ROOT / "corpus" / "RESULTS.json").write_text(json.dumps(data, indent=2) + "\n")

    lines: list[str] = []
    lines.append("# COBOL -> Liminate Expressibility & Fidelity Experiment - Run 1\n")
    lines.append("## Run header\n")
    lines.append(f"- Date: {data['run_header']['date']}")
    lines.append(f"- Interpreter version: {liminate_version}")
    lines.append(f"- learn_cobol SHA: `{shas['learn_cobol']}`")
    lines.append(f"- cobol-samples SHA: `{shas['cobol-samples']}`")
    lines.append(f"- mortgagesample SHA: `{shas['mortgagesample']}`")
    lines.append(f"- Total programs scanned: {SCANNED_PROGRAMS}")
    lines.append(f"- Total with isolable rules: {attempted}")
    lines.append(f"- Total attempted: {attempted}\n")
    lines.append("## Expressibility table\n")
    lines.append("|Outcome|Count|% of attempted|")
    lines.append("|---|---:|---:|")
    lines.append(f"|base vocabulary|{counts['base']}|{percent(counts['base'], attempted)}|")
    lines.append(f"|pack-needed|{counts['pack-needed']}|{percent(counts['pack-needed'], attempted)}|")
    lines.append(f"|untranslatable|{counts['untranslatable']}|{percent(counts['untranslatable'], attempted)}|\n")
    lines.append("## Pack-demand summary\n")
    if pack_counts:
        lines.append("|Pack needed|Count|")
        lines.append("|---|---:|")
        for name, count in pack_counts.most_common():
            lines.append(f"|{name}|{count}|")
        lines.append("")
    else:
        lines.append("No pack-needed rules were found.\n")
    lines.append("## Fidelity-risk summary\n")
    lines.append("|Event kind|Count|")
    lines.append("|---|---:|")
    for kind, count in sorted(event_counts.items()):
        lines.append(f"|{kind}|{count}|")
    lines.append("")
    lines.append("|Program|Kind|COBOL|Liminate|Risk|")
    lines.append("|---|---|---|---|---|")
    for program, kind, cobol, limn, risk in boundary_rows:
        lines.append(f"|{program}|{kind}|`{cobol}`|`{limn}`|{risk}|")
    lines.append("")
    lines.append("## Verb-frequency table\n")
    lines.append("|Verb|Count|")
    lines.append("|---|---:|")
    for verb, count in verb_counts.most_common():
        lines.append(f"|{verb}|{count}|")
    lines.append("")
    lines.append("## Three findings\n")
    for finding in data["findings"]:
        lines.append(f"- {finding}")
    lines.append("")
    lines.append("## Honesty boundary\n")
    lines.append(data["honesty_boundary"])
    lines.append("")
    (ROOT / "corpus" / "RESULTS.md").write_text("\n".join(lines))


def main() -> None:
    if TRANSLATIONS.exists():
        for child in TRANSLATIONS.iterdir():
            if child.name != ".gitkeep":
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
    written = [write_rule(rule) for rule in RULES]
    write_results(written)


if __name__ == "__main__":
    main()
