---
name: math-calculator
description: Use this skill for any mathematical calculation — arithmetic, algebra, equation solving, statistics, or percentages. Do NOT compute math yourself; always delegate to this tool.
---

# math-calculator

## Overview

Evaluates mathematical expressions reliably using Python's `sympy` and `statistics` libraries. This bypasses the model's tendency to make arithmetic errors for non-trivial calculations.

## When to use

- User asks to calculate, compute, or solve anything numeric
- Percentages: "15% of 340", "what is a 20% tip on 85?"
- Algebra: "solve x^2 - 4 = 0", "simplify 3x + 2x"
- Statistics: "mean/median/std of [1,2,3,4,5]"
- Any arithmetic where accuracy matters

**Do NOT use** for questions that are purely conceptual with no actual calculation needed.

## How to invoke

Call the `math_calculator` tool with a single `expression` argument:

```
math_calculator(expression="<math problem in plain text or notation>")
```

### Input examples

| User request | expression to pass |
|---|---|
| "What is 15% of 340?" | `15% of 340` |
| "Solve x² - 9 = 0" | `x^2 - 9 = 0` |
| "Square root of 144" | `sqrt(144)` |
| "Mean of 4, 8, 15, 16, 23" | `mean of [4, 8, 15, 16, 23]` |
| "(3 + 5) × 12 ÷ 4" | `(3 + 5) * 12 / 4` |

## Expected output

A string containing the result, e.g.:
- `"51.0"` for `15% of 340`
- `"Solutions for x: [-3, 3]"` for `x^2 - 9 = 0`
- `"mean([4, 8, 15, 16, 23]) = 13.2"` for the mean example

## Implementation

See `math_skill.py` in this folder.
