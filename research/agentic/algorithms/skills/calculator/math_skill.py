import logging
import re

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _try_sympy(expression: str) -> str | None:
    """Attempt symbolic evaluation with sympy. Returns None on failure."""
    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import (
            parse_expr,
            standard_transformations,
            implicit_multiplication_application,
        )

        transformations = standard_transformations + (implicit_multiplication_application,)

        solve_match = re.match(
            r"^(?:solve\s+)?(.+?)\s*=\s*(.+)$", expression, re.IGNORECASE
        )
        if solve_match:
            lhs_str = solve_match.group(1).strip()
            rhs_str = solve_match.group(2).strip()
            lhs = parse_expr(lhs_str, transformations=transformations)
            rhs = parse_expr(rhs_str, transformations=transformations)
            symbols = list((lhs - rhs).free_symbols)
            if symbols:
                solutions = sp.solve(lhs - rhs, symbols[0])
                return f"Solutions for {symbols[0]}: {solutions}"
            else:
                return str(sp.simplify(lhs - rhs) == 0)

        result = parse_expr(expression, transformations=transformations)
        simplified = sp.simplify(result)
        if simplified.is_number:
            evaluated = float(simplified)
            if evaluated == int(evaluated):
                return str(int(evaluated))
            return str(round(evaluated, 10))
        return str(simplified)

    except Exception:
        return None


def _try_statistics(expression: str) -> str | None:
    """Handle mean/median/std/sum/min/max of a list."""
    stat_match = re.match(
        r"^(mean|median|std|sum|min|max)\s+(?:of\s+)?\[?([0-9.,\s]+)\]?$",
        expression.strip(),
        re.IGNORECASE,
    )
    if not stat_match:
        return None

    func_name = stat_match.group(1).lower()
    raw_numbers = stat_match.group(2)
    numbers = [float(n.strip()) for n in re.split(r"[,\s]+", raw_numbers) if n.strip()]

    if not numbers:
        return None

    import statistics

    ops = {
        "mean": lambda ns: statistics.mean(ns),
        "median": lambda ns: statistics.median(ns),
        "std": lambda ns: statistics.stdev(ns) if len(ns) > 1 else 0.0,
        "sum": lambda ns: sum(ns),
        "min": lambda ns: min(ns),
        "max": lambda ns: max(ns),
    }
    result = ops[func_name](numbers)
    return f"{func_name}({numbers}) = {result}"


def _try_percentage(expression: str) -> str | None:
    """Handle 'X% of Y' patterns."""
    pct_match = re.match(
        r"^([0-9.]+)\s*%\s+of\s+([0-9.]+)$", expression.strip(), re.IGNORECASE
    )
    if pct_match:
        pct = float(pct_match.group(1))
        value = float(pct_match.group(2))
        result = (pct / 100) * value
        return f"{pct}% of {value} = {result}"
    return None


@tool
def math_calculator(expression: str) -> str:
    """Evaluate a mathematical expression or solve a math problem.

    Use this for ANY math operation — arithmetic, algebra, equation solving,
    statistics, or percentages. Do NOT attempt to compute math yourself;
    always delegate to this tool.

    Args:
        expression: The math expression or problem. Examples:
            - "2 + 2"
            - "15% of 340"
            - "sqrt(144)"
            - "x^2 - 4 = 0"
            - "mean of [1, 2, 3, 4, 5]"
            - "(3 + 5) * 12 / 4"
    """
    cleaned = expression.strip()
    logger.info("[TOOL] math_calculator called | input: %r", cleaned)

    result = (
        _try_percentage(cleaned)
        or _try_statistics(cleaned)
        or _try_sympy(cleaned)
    )

    if result is not None:
        logger.info("[TOOL] math_calculator result: %r", result)
        return result

    logger.warning("[TOOL] math_calculator failed to evaluate: %r", cleaned)
    return f"Could not evaluate '{expression}'. Please rephrase as a valid math expression."
