"""Unit-Aware Formula CLI — spec-compliant implementation.

Modules within this single file:
  1. Tokens & Lexer
  2. AST & Parser  (value-formula, relationship-formula, unit-expression)
  3. Environment   (units, variables, relationships)
  4. Evaluator     (value context, relationship context)
  5. Unit Conversion (BFS shortest-path)
  6. Serialization
  7. Command dispatch
  8. CLI entry point
"""

from __future__ import annotations

import math
import re
import sys
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


# ── Error helpers ──────────────────────────────────────────────────────────

class FormulaError(Exception):
    """All recoverable errors raised during command processing."""


def error(msg: str) -> FormulaError:
    return FormulaError(f"Error: {msg}")


# ── 1. Tokens & Lexer ─────────────────────────────────────────────────────

class TokenKind:
    NUMBER = "NUMBER"
    UNIT_ID = "UNIT_ID"
    VAR_ID = "VAR_ID"
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    CARET = "^"
    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    EOF = "EOF"


@dataclass
class Token:
    kind: str
    value: str
    pos: int


# Patterns for lexing (order matters).
_TOKEN_PATTERNS: list[tuple[str, str | None]] = [
    (r"[ \t]+", None),  # skip whitespace
    (r"[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", TokenKind.NUMBER),
    (r"\.[0-9]+(?:[eE][+-]?[0-9]+)?", TokenKind.NUMBER),
    (r"[a-z][a-z_]*", TokenKind.UNIT_ID),
    (r"[A-Z][A-Z_]*", TokenKind.VAR_ID),
    (r"\+", TokenKind.PLUS),
    (r"-", TokenKind.MINUS),
    (r"\*", TokenKind.STAR),
    (r"/", TokenKind.SLASH),
    (r"\^", TokenKind.CARET),
    (r"\(", TokenKind.LPAREN),
    (r"\)", TokenKind.RPAREN),
    (r"\[", TokenKind.LBRACKET),
    (r"\]", TokenKind.RBRACKET),
]

_MASTER_RE = re.compile(
    "|".join(f"(?P<T{i}>{pat})" for i, (pat, _) in enumerate(_TOKEN_PATTERNS))
)


def tokenize(text: str) -> list[Token]:
    """Tokenize a formula string into a list of Token objects."""
    tokens: list[Token] = []
    pos = 0
    for m in _MASTER_RE.finditer(text):
        if m.start() != pos:
            # Characters between last match end and this match start — invalid.
            raise error("invalid formula.")
        pos = m.end()
        for i, (_, kind) in enumerate(_TOKEN_PATTERNS):
            if m.group(f"T{i}") is not None:
                if kind is not None:
                    tokens.append(Token(kind=kind, value=m.group(f"T{i}"), pos=m.start()))
                break
    if pos != len(text):
        raise error("invalid formula.")
    tokens.append(Token(kind=TokenKind.EOF, value="", pos=len(text)))
    return tokens


# ── 2. AST & Parser ───────────────────────────────────────────────────────

@dataclass
class ValueLiteral:
    magnitude: float
    unit: dict[str, float]  # UnitExpr


@dataclass
class Identifier:
    name: str


@dataclass
class UnaryOp:
    op: str  # "+", "-", "[", "]"
    operand: object  # Expr


@dataclass
class BinaryOp:
    op: str  # "+", "-", "*", "/", "^"
    left: object   # Expr
    right: object  # Expr


Expr = ValueLiteral | Identifier | UnaryOp | BinaryOp


class Parser:
    """Recursive-descent parser for formula expressions.

    Supports two modes:
      - value formula  (allow_additive=True,  allow_log_exp=True)
      - relationship formula (allow_additive=False, allow_log_exp=False)
    """

    def __init__(
        self,
        tokens: list[Token],
        known_units: set[str],
        *,
        allow_additive: bool = True,
        allow_log_exp: bool = True,
    ):
        self.tokens = tokens
        self.pos = 0
        self.known_units = known_units
        self.allow_additive = allow_additive
        self.allow_log_exp = allow_log_exp

    # ── helpers ──

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, kind: str) -> Token:
        tok = self.peek()
        if tok.kind != kind:
            raise error("invalid formula.")
        return self.advance()

    def at(self, kind: str) -> bool:
        return self.peek().kind == kind

    # ── entry points ──

    def parse_formula(self) -> Expr:
        expr = self._parse_additive()
        self.expect(TokenKind.EOF)
        return expr

    # ── precedence 1: additive (+, -) ──

    def _parse_additive(self) -> Expr:
        left = self._parse_multiplicative()
        while self.at(TokenKind.PLUS) or self.at(TokenKind.MINUS):
            if not self.allow_additive:
                raise error("invalid formula.")
            op = self.advance().kind
            right = self._parse_multiplicative()
            left = BinaryOp(op=op, left=left, right=right)
        return left

    # ── precedence 2: multiplicative (*, /) ──

    def _parse_multiplicative(self) -> Expr:
        left = self._parse_power()
        while self.at(TokenKind.STAR) or self.at(TokenKind.SLASH):
            op = self.advance().kind
            right = self._parse_power()
            left = BinaryOp(op=op, left=left, right=right)
        return left

    # ── precedence 3: power (^), right-associative ──

    def _parse_power(self) -> Expr:
        base = self._parse_unary()
        if self.at(TokenKind.CARET):
            self.advance()
            exp = self._parse_power()  # right-associative: recurse at same level
            return BinaryOp(op="^", left=base, right=exp)
        return base

    # ── precedence 4: unary (+, -, [, ]) ──

    def _parse_unary(self) -> Expr:
        if self.at(TokenKind.PLUS) or self.at(TokenKind.MINUS):
            op = self.advance().kind
            operand = self._parse_unary()
            return UnaryOp(op=op, operand=operand)
        if self.at(TokenKind.LBRACKET):
            if not self.allow_log_exp:
                raise error("invalid formula.")
            self.advance()
            operand = self._parse_unary()
            return UnaryOp(op="[", operand=operand)
        if self.at(TokenKind.RBRACKET):
            if not self.allow_log_exp:
                raise error("invalid formula.")
            self.advance()
            operand = self._parse_unary()
            return UnaryOp(op="]", operand=operand)
        return self._parse_primary()

    # ── precedence 5/6: value literals with unit attachment, and parens ──

    def _parse_primary(self) -> Expr:
        if self.at(TokenKind.NUMBER):
            return self._parse_number_with_unit()
        if self.at(TokenKind.UNIT_ID):
            name = self.advance().value
            return Identifier(name=name)
        if self.at(TokenKind.VAR_ID):
            name = self.advance().value
            return Identifier(name=name)
        if self.at(TokenKind.LPAREN):
            self.advance()
            expr = self._parse_additive()
            self.expect(TokenKind.RPAREN)
            return expr
        raise error("invalid formula.")

    def _parse_number_with_unit(self) -> Expr:
        """Parse a number and attempt to attach a unit section."""
        num_tok = self.expect(TokenKind.NUMBER)
        magnitude = float(num_tok.value)
        if not math.isfinite(magnitude):
            raise error("invalid formula.")

        # Try to parse a unit section after the number.
        unit_expr = self._try_parse_unit_section()

        # Reject ambiguous caret after a value literal with units (e.g. 2 m^2^3).
        if unit_expr and self.at(TokenKind.CARET):
            raise error("invalid formula.")

        return ValueLiteral(magnitude=magnitude, unit=unit_expr)

    def _try_parse_unit_section(self) -> dict[str, float]:
        """Attempt to parse a unit section (greedy).

        A unit section starts with a unit-id or '(' and extends through
        subsequent '*' and '/' operators followed by unit factors.
        """
        # A unit section can start with a unit-id or '('.
        if not (self.at(TokenKind.UNIT_ID) or self.at(TokenKind.LPAREN)):
            return {}

        # Check that a leading UNIT_ID is actually a known unit.
        if self.at(TokenKind.UNIT_ID) and self.peek().value not in self.known_units:
            raise error(f"unknown unit {self.peek().value}.")

        unit = self._parse_unit_factor()

        # Continue consuming '*' and '/' as part of the unit section.
        while self.at(TokenKind.STAR) or self.at(TokenKind.SLASH):
            op = self.advance().kind
            right = self._parse_unit_factor()
            if op == "*":
                unit = _unit_multiply(unit, right)
            else:
                unit = _unit_divide(unit, right)

        return _normalize_unit(unit)

    def _parse_unit_factor(self) -> dict[str, float]:
        """Parse a single unit factor: unit-id[^integer] or (unit-section)[^integer]."""
        if self.at(TokenKind.LPAREN):
            self.advance()
            inner = self._parse_unit_section_inner()
            self.expect(TokenKind.RPAREN)
            if self.at(TokenKind.CARET):
                self.advance()
                exp = self._parse_integer_exponent()
                return _unit_power(inner, exp)
            return inner
        if self.at(TokenKind.UNIT_ID):
            name = self.advance().value
            if name not in self.known_units:
                raise error(f"unknown unit {name}.")
            exp = 1
            if self.at(TokenKind.CARET):
                self.advance()
                exp = self._parse_integer_exponent()
            return {name: float(exp)}
        raise error("invalid formula.")

    def _parse_unit_section_inner(self) -> dict[str, float]:
        """Parse a unit-section inside parentheses.

        The grammar for parenthesized unit sections is the same unit-factor
        grammar (no "1" literal allowed — that is only in output-unit context).
        """
        unit = self._parse_unit_factor()
        while self.at(TokenKind.STAR) or self.at(TokenKind.SLASH):
            op = self.advance().kind
            right = self._parse_unit_factor()
            if op == "*":
                unit = _unit_multiply(unit, right)
            else:
                unit = _unit_divide(unit, right)
        return _normalize_unit(unit)

    def _parse_integer_exponent(self) -> int:
        """Parse an integer exponent (possibly signed)."""
        sign = 1
        if self.at(TokenKind.PLUS):
            self.advance()
        elif self.at(TokenKind.MINUS):
            self.advance()
            sign = -1
        tok = self.peek()
        if tok.kind != TokenKind.NUMBER:
            raise error("invalid formula.")
        # Must be a plain integer (no dot, no exponent part).
        if not re.fullmatch(r"[0-9]+", tok.value):
            raise error("invalid formula.")
        self.advance()
        return sign * int(tok.value)


# ── Unit-expression parser (for output-unit formulas) ──────────────────────

class UnitExprParser:
    """Parse a unit-expression for output-unit context."""

    def __init__(self, tokens: list[Token], known_units: set[str]):
        self.tokens = tokens
        self.pos = 0
        self.known_units = known_units

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, kind: str) -> Token:
        tok = self.peek()
        if tok.kind != kind:
            raise error("invalid output unit.")
        return self.advance()

    def at(self, kind: str) -> bool:
        return self.peek().kind == kind

    def parse(self) -> dict[str, float]:
        unit = self._parse_product()
        self.expect(TokenKind.EOF)
        return _normalize_unit(unit)

    def _parse_product(self) -> dict[str, float]:
        unit = self._parse_power()
        while self.at(TokenKind.STAR) or self.at(TokenKind.SLASH):
            op = self.advance().kind
            right = self._parse_power()
            if op == "*":
                unit = _unit_multiply(unit, right)
            else:
                unit = _unit_divide(unit, right)
        return unit

    def _parse_power(self) -> dict[str, float]:
        primary = self._parse_primary()
        if self.at(TokenKind.CARET):
            self.advance()
            exp = self._parse_integer_exponent()
            return _unit_power(primary, exp)
        return primary

    def _parse_primary(self) -> dict[str, float]:
        if self.at(TokenKind.UNIT_ID):
            name = self.advance().value
            if name not in self.known_units:
                raise error(f"unknown unit {name}.")
            return {name: 1.0}
        if self.at(TokenKind.NUMBER) and self.peek().value == "1":
            self.advance()
            return {}
        if self.at(TokenKind.LPAREN):
            self.advance()
            inner = self._parse_product()
            self.expect(TokenKind.RPAREN)
            return inner
        raise error("invalid output unit.")

    def _parse_integer_exponent(self) -> int:
        sign = 1
        if self.at(TokenKind.PLUS):
            self.advance()
        elif self.at(TokenKind.MINUS):
            self.advance()
            sign = -1
        tok = self.peek()
        if tok.kind != TokenKind.NUMBER:
            raise error("invalid output unit.")
        if not re.fullmatch(r"[0-9]+", tok.value):
            raise error("invalid output unit.")
        self.advance()
        return sign * int(tok.value)


# ── Unit algebra helpers ───────────────────────────────────────────────────

def _unit_multiply(u: dict[str, float], v: dict[str, float]) -> dict[str, float]:
    result = dict(u)
    for k, exp in v.items():
        result[k] = result.get(k, 0.0) + exp
    return result


def _unit_divide(u: dict[str, float], v: dict[str, float]) -> dict[str, float]:
    result = dict(u)
    for k, exp in v.items():
        result[k] = result.get(k, 0.0) - exp
    return result


def _unit_power(u: dict[str, float], n: float) -> dict[str, float]:
    return {k: exp * n for k, exp in u.items()}


def _normalize_unit(u: dict[str, float]) -> dict[str, float]:
    return {k: v for k, v in u.items() if v != 0.0}


# ── 3. Environment ────────────────────────────────────────────────────────

@dataclass
class UnitRelationship:
    target: str
    factor: float
    basis: dict[str, float]


@dataclass
class Environment:
    units: set[str] = field(default_factory=set)
    variables: dict[str, tuple[float, dict[str, float]]] = field(default_factory=dict)
    relationships: dict[str, UnitRelationship] = field(default_factory=dict)


# ── 4. Evaluator ──────────────────────────────────────────────────────────

def evaluate_value(expr: Expr, env: Environment) -> tuple[float, dict[str, float]]:
    """Evaluate an expression in value context. Returns (magnitude, unit_expr)."""
    return _eval(expr, env, context="value")


def evaluate_relationship(
    expr: Expr,
    source_units: set[str],
) -> tuple[float, dict[str, float]]:
    """Evaluate an expression in relationship context. Returns (factor, basis)."""
    # Build a minimal environment with only source units.
    rel_env = Environment(units=source_units)
    return _eval(expr, rel_env, context="relationship")


def _eval(
    expr: Expr,
    env: Environment,
    context: str,
) -> tuple[float, dict[str, float]]:
    """Core recursive evaluator."""

    if isinstance(expr, ValueLiteral):
        return (expr.magnitude, dict(expr.unit))

    if isinstance(expr, Identifier):
        return _resolve_identifier(expr.name, env, context)

    if isinstance(expr, UnaryOp):
        val = _eval(expr.operand, env, context)
        mag, unit = val
        if expr.op == "+":
            return (mag, unit)
        if expr.op == "-":
            return (-mag, unit)
        if expr.op == "[":
            # log: requires scalar and positive
            if unit:
                raise error("log argument must be scalar.")
            if mag <= 0:
                raise error("log argument must be positive.")
            result = math.log(mag)
            _check_finite_real(result)
            return (result, {})
        if expr.op == "]":
            # exp: requires scalar
            if unit:
                raise error("exp argument must be scalar.")
            result = math.exp(mag)
            _check_finite_real(result)
            return (result, {})

    if isinstance(expr, BinaryOp):
        if expr.op == "+":
            return _eval_add_sub("+", expr.left, expr.right, env, context)
        if expr.op == "-":
            return _eval_add_sub("-", expr.left, expr.right, env, context)
        if expr.op == "*":
            lm, lu = _eval(expr.left, env, context)
            rm, ru = _eval(expr.right, env, context)
            result = lm * rm
            _check_finite_real(result)
            return (result, _normalize_unit(_unit_multiply(lu, ru)))
        if expr.op == "/":
            lm, lu = _eval(expr.left, env, context)
            rm, ru = _eval(expr.right, env, context)
            if rm == 0:
                raise error("division by zero.")
            result = lm / rm
            _check_finite_real(result)
            return (result, _normalize_unit(_unit_divide(lu, ru)))
        if expr.op == "^":
            lm, lu = _eval(expr.left, env, context)
            rm, ru = _eval(expr.right, env, context)
            if ru:
                raise error("exponent must be scalar.")
            try:
                result = lm ** rm
            except (ValueError, OverflowError, ZeroDivisionError):
                raise error("numeric result is not finite.")
            if isinstance(result, complex):
                raise error("numeric result is not real.")
            _check_finite_real(result)
            return (result, _normalize_unit(_unit_power(lu, rm)))

    raise error("invalid formula.")


def _resolve_identifier(
    name: str,
    env: Environment,
    context: str,
) -> tuple[float, dict[str, float]]:
    """Resolve an identifier in the appropriate context."""
    if context == "value":
        # Check variable namespace first (uppercase).
        if re.fullmatch(r"[A-Z][A-Z_]*", name):
            if name in env.variables:
                return env.variables[name]
            raise error(f"unknown variable {name}.")
        # Unit namespace (lowercase).
        if re.fullmatch(r"[a-z][a-z_]*", name):
            if name in env.units:
                return (1.0, {name: 1.0})
            raise error(f"unknown unit {name}.")
        raise error("invalid formula.")

    if context == "relationship":
        # Only source-list units are visible.
        if re.fullmatch(r"[a-z][a-z_]*", name):
            if name in env.units:
                return (1.0, {name: 1.0})
            raise error(f"unknown unit {name}.")
        # Variables are not available in relationship context.
        if re.fullmatch(r"[A-Z][A-Z_]*", name):
            raise error(f"unknown unit {name}.")
        raise error("invalid formula.")

    raise error("invalid formula.")


def _eval_add_sub(
    op: str,
    left_expr: Expr,
    right_expr: Expr,
    env: Environment,
    context: str,
) -> tuple[float, dict[str, float]]:
    """Evaluate addition/subtraction with unit unification."""
    lm, lu = _eval(left_expr, env, context)
    rm, ru = _eval(right_expr, env, context)

    # Unify units.
    lm, rm, result_unit = _unify_units(lm, lu, rm, ru, env)

    if op == "+":
        result = lm + rm
    else:
        result = lm - rm
    _check_finite_real(result)
    return (result, result_unit)


def _unify_units(
    lm: float,
    lu: dict[str, float],
    rm: float,
    ru: dict[str, float],
    env: Environment,
) -> tuple[float, float, dict[str, float]]:
    """Unify two values' units for additive operations."""
    if lu == ru:
        return (lm, rm, lu)

    # Try converting right to left.
    try:
        converted_rm = convert_magnitude(rm, ru, lu, env)
        return (lm, converted_rm, lu)
    except FormulaError:
        pass

    # Try converting left to right.
    try:
        converted_lm = convert_magnitude(lm, lu, ru, env)
        return (converted_lm, rm, ru)
    except FormulaError:
        pass

    raise error(f"cannot convert {serialize_unit(ru)} to {serialize_unit(lu)}.")


def _check_finite_real(value: float) -> None:
    if isinstance(value, complex):
        raise error("numeric result is not real.")
    if not math.isfinite(value):
        raise error("numeric result is not finite.")


# ── 5. Unit Conversion (BFS) ──────────────────────────────────────────────

def convert_magnitude(
    magnitude: float,
    source: dict[str, float],
    target: dict[str, float],
    env: Environment,
) -> float:
    """Convert a magnitude from source unit to target unit using BFS."""
    if source == target:
        return magnitude

    # BFS state: (unit_expr_key, magnitude_scale)
    source_key = _unit_key(source)
    target_key = _unit_key(target)

    visited: set[str] = {source_key}
    # Queue entries: (current_unit_expr, current_scale)
    queue: deque[tuple[dict[str, float], float]] = deque()
    queue.append((source, 1.0))

    while queue:
        current_unit, current_scale = queue.popleft()

        # Generate all next states by applying each relationship in both directions.
        next_states = _generate_next_states(current_unit, current_scale, env)

        # Sort by serialized UnitExpr for deterministic alphabetical ordering.
        next_states.sort(key=lambda x: _unit_key(x[0]))

        # Deduplicate: for same UnitExpr, keep the one with the alphabetically-first
        # relationship target, preferring forward over reverse.
        seen_keys: dict[str, tuple[dict[str, float], float]] = {}
        for unit_expr, scale in next_states:
            key = _unit_key(unit_expr)
            if key not in seen_keys:
                seen_keys[key] = (unit_expr, scale)

        for key, (unit_expr, scale) in sorted(seen_keys.items()):
            if key == target_key:
                result = magnitude * scale
                _check_finite_real(result)
                return result
            if key not in visited:
                visited.add(key)
                queue.append((unit_expr, scale))

    raise error(f"cannot convert {serialize_unit(source)} to {serialize_unit(target)}.")


def _generate_next_states(
    current: dict[str, float],
    current_scale: float,
    env: Environment,
) -> list[tuple[dict[str, float], float]]:
    """Generate all possible next UnitExpr states from the current state."""
    results: list[tuple[dict[str, float], float]] = []

    # Iterate relationships in alphabetical order of target for tie-breaking.
    for target_id in sorted(env.relationships):
        rel = env.relationships[target_id]

        # Validate relationship.
        if not math.isfinite(rel.factor) or rel.factor == 0:
            continue

        # Forward: target -> basis (if current contains target).
        exponent = current.get(rel.target, 0.0)
        if exponent != 0.0:
            try:
                scale_factor = rel.factor ** exponent
            except (ValueError, OverflowError):
                continue
            if isinstance(scale_factor, complex) or not math.isfinite(scale_factor):
                continue

            new_unit = dict(current)
            # Remove target.
            del new_unit[rel.target]
            # Add basis * exponent.
            for basis_unit, basis_exp in rel.basis.items():
                new_unit[basis_unit] = new_unit.get(basis_unit, 0.0) + basis_exp * exponent
            new_unit = _normalize_unit(new_unit)

            new_scale = current_scale * scale_factor
            if math.isfinite(new_scale):
                results.append((new_unit, new_scale))

        # Reverse: basis -> target.
        rev = _try_reverse_application(current, rel)
        if rev is not None:
            rev_unit, rev_exponent = rev
            try:
                scale_factor = rel.factor ** (-rev_exponent)
            except (ValueError, OverflowError):
                continue
            if isinstance(scale_factor, complex) or not math.isfinite(scale_factor):
                continue

            new_scale = current_scale * scale_factor
            if math.isfinite(new_scale):
                results.append((rev_unit, new_scale))

    return results


def _try_reverse_application(
    current: dict[str, float],
    rel: UnitRelationship,
) -> Optional[tuple[dict[str, float], float]]:
    """Try to apply a relationship in reverse direction.

    Returns (new_unit_expr, exponent_e) or None.
    """
    if not rel.basis:
        return None

    ratios = []
    for basis_unit, basis_exp in rel.basis.items():
        if basis_exp == 0.0:
            continue
        current_exp = current.get(basis_unit, 0.0)
        r = current_exp / basis_exp
        ratios.append(r)

    if not ratios:
        return None

    # All nonzero ratios must have the same sign.
    nonzero_ratios = [r for r in ratios if r != 0.0]
    if not nonzero_ratios:
        return None

    signs = {(1 if r > 0 else -1) for r in nonzero_ratios}
    if len(signs) > 1:
        return None

    # e = the nonzero ratio with smallest absolute value.
    e = min(nonzero_ratios, key=abs)

    # Build the new unit.
    new_unit = dict(current)
    for basis_unit, basis_exp in rel.basis.items():
        new_unit[basis_unit] = new_unit.get(basis_unit, 0.0) - basis_exp * e
    new_unit[rel.target] = new_unit.get(rel.target, 0.0) + e
    new_unit = _normalize_unit(new_unit)

    return (new_unit, e)


def _unit_key(unit: dict[str, float]) -> str:
    """Produce a deterministic string key for a UnitExpr (its serialization)."""
    return serialize_unit(unit)


# ── 6. Serialization ──────────────────────────────────────────────────────

def serialize_unit(unit: dict[str, float]) -> str:
    """Serialize a UnitExpr to its canonical string form."""
    if not unit:
        return "1"

    positive = sorted((k, v) for k, v in unit.items() if v > 0)
    negative = sorted((k, v) for k, v in unit.items() if v < 0)

    def format_factor(name: str, exp: float) -> str:
        if exp == 1.0:
            return name
        # Format exponent: use integer form if it is one, else float.
        if exp == int(exp):
            return f"{name}^{int(exp)}"
        return f"{name}^{exp}"

    if positive:
        numerator = "*".join(format_factor(k, v) for k, v in positive)
    else:
        numerator = "1"

    if negative:
        denominator_parts = []
        for k, v in negative:
            abs_v = -v
            denominator_parts.append(format_factor(k, abs_v))
        denominator = "*".join(denominator_parts)
        if len(negative) > 1:
            # Multiple denominator terms: separate with *.
            # But the spec examples show kg*m/s^2, not kg*m/(s^2).
            # Each denominator term is separated by /.
            return numerator + "/" + "/".join(denominator_parts)
        return numerator + "/" + denominator
    return numerator


def serialize_magnitude(mag: float) -> str:
    """Serialize a magnitude deterministically."""
    if mag == int(mag) and abs(mag) < 1e15:
        # Use integer representation for clean values.
        return str(int(mag))
    # Use repr for full precision; Python's repr is finite and parseable.
    result = repr(mag)
    # Ensure it matches the number grammar (no leading '+').
    return result


# ── 7. Command Dispatch ───────────────────────────────────────────────────

def process_command(line: str, env: Environment) -> Optional[str]:
    """Process a single command line. Returns output string or None."""
    line = line.strip()
    if not line:
        return None

    if line.startswith("unit:"):
        return _cmd_unit(line[5:], env)
    if line.startswith("set:"):
        return _cmd_set(line[4:], env)
    if line.startswith("relate:"):
        return _cmd_relate(line[7:], env)
    if line.startswith("evaluate:"):
        return _cmd_evaluate(line[9:], env)

    raise error("unknown command.")


def _cmd_unit(payload: str, env: Environment) -> Optional[str]:
    unit_id = payload.strip()
    if not re.fullmatch(r"[a-z][a-z_]*", unit_id):
        raise error("invalid unit name.")
    env.units.add(unit_id)
    return None


def _cmd_set(payload: str, env: Environment) -> Optional[str]:
    parts = payload.split(":", 1)
    if len(parts) != 2:
        raise error("invalid command syntax.")
    var_id = parts[0].strip()
    formula_str = parts[1].strip()
    if not var_id or not formula_str:
        raise error("invalid command syntax.")
    if not re.fullmatch(r"[A-Z][A-Z_]*", var_id):
        raise error("invalid variable name.")

    tokens = tokenize(formula_str)
    parser = Parser(tokens, env.units, allow_additive=True, allow_log_exp=True)
    ast = parser.parse_formula()
    mag, unit = evaluate_value(ast, env)
    _check_finite_real(mag)
    env.variables[var_id] = (mag, unit)
    return None


def _cmd_relate(payload: str, env: Environment) -> Optional[str]:
    parts = payload.split(":", 2)
    if len(parts) != 3:
        raise error("invalid command syntax.")

    target_id = parts[0].strip()
    source_list_str = parts[1].strip()
    formula_str = parts[2].strip()

    if not target_id or not source_list_str or not formula_str:
        raise error("invalid command syntax.")

    if not re.fullmatch(r"[a-z][a-z_]*", target_id):
        raise error("invalid unit name.")

    # Parse source unit list.
    source_items = [s.strip() for s in source_list_str.split(",")]
    source_units: set[str] = set()
    for item in source_items:
        if not item:
            raise error("invalid unit list.")
        if not re.fullmatch(r"[a-z][a-z_]*", item):
            raise error("invalid unit list.")
        if item not in env.units:
            raise error("invalid unit list.")
        if item in source_units:
            raise error("invalid unit list.")
        source_units.add(item)

    if target_id in source_units:
        raise error("invalid unit list.")

    # Parse and evaluate relationship formula.
    tokens = tokenize(formula_str)
    parser = Parser(
        tokens, source_units,
        allow_additive=False, allow_log_exp=False,
    )
    ast = parser.parse_formula()
    factor, basis = evaluate_relationship(ast, source_units)

    # Validate relationship.
    if not math.isfinite(factor) or factor == 0:
        raise error("invalid relationship.")
    for unit_id in basis:
        if unit_id not in source_units:
            raise error("invalid relationship.")

    env.units.add(target_id)
    env.relationships[target_id] = UnitRelationship(
        target=target_id,
        factor=factor,
        basis=_normalize_unit(basis),
    )
    return None


def _cmd_evaluate(payload: str, env: Environment) -> Optional[str]:
    # Split at the LAST ':' to separate value-formula from output-unit-formula.
    last_colon = payload.rfind(":")
    if last_colon == -1:
        # No colon: entire payload is the value formula.
        value_str = payload.strip()
        output_unit_str = None
    else:
        value_str = payload[:last_colon].strip()
        output_unit_str = payload[last_colon + 1:].strip()

    if not value_str:
        raise error("invalid command syntax.")
    if output_unit_str is not None and not output_unit_str:
        raise error("invalid command syntax.")

    # Parse output unit first (errors take precedence).
    target_unit: Optional[dict[str, float]] = None
    if output_unit_str is not None:
        try:
            out_tokens = tokenize(output_unit_str)
        except FormulaError:
            raise error("invalid output unit.")
        try:
            out_parser = UnitExprParser(out_tokens, env.units)
            target_unit = out_parser.parse()
        except FormulaError as e:
            # Re-raise with appropriate message if not already "invalid output unit."
            msg = str(e)
            if "unknown unit" in msg:
                raise error(f"unknown unit {msg.split('unknown unit ')[1]}")
            raise error("invalid output unit.")

    # Parse and evaluate value formula.
    tokens = tokenize(value_str)
    parser = Parser(tokens, env.units, allow_additive=True, allow_log_exp=True)
    ast = parser.parse_formula()
    mag, unit = evaluate_value(ast, env)
    _check_finite_real(mag)

    if target_unit is not None:
        mag = convert_magnitude(mag, unit, target_unit, env)
        unit = target_unit

    return f"{serialize_magnitude(mag)} {serialize_unit(unit)}"


# ── 8. CLI Entry Point & Transcript Runner ─────────────────────────────────

def run_session(lines: list[str]) -> list[str]:
    """Run a sequence of command lines in a fresh session.

    Returns the list of output lines (one per command that produces output).
    This is the adapter interface expected by the test harness.
    """
    env = Environment()
    output: list[str] = []
    for line in lines:
        try:
            result = process_command(line, env)
            if result is not None:
                output.append(result)
        except FormulaError as e:
            output.append(str(e))
    return output


def main() -> None:
    """Read commands from stdin, one per line."""
    env = Environment()
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line.strip():
            continue
        try:
            result = process_command(line, env)
            if result is not None:
                print(result)
        except FormulaError as e:
            print(e)


if __name__ == "__main__":
    main()
