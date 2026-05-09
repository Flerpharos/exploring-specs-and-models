import sys
import re
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set, Any

class Error(Exception): pass
class ParseError(Error): pass
class EvalError(Error): pass

UnitExpr = Dict[str, float]

def normalize_unit(u: UnitExpr) -> UnitExpr:
    return {k: v for k, v in sorted(u.items()) if v != 0}

def multiply_unit(u: UnitExpr, v: UnitExpr) -> UnitExpr:
    res = defaultdict(float, u)
    for k, val in v.items():
        res[k] += val
    return normalize_unit(res)

def divide_unit(u: UnitExpr, v: UnitExpr) -> UnitExpr:
    res = defaultdict(float, u)
    for k, val in v.items():
        res[k] -= val
    return normalize_unit(res)

def power_unit(u: UnitExpr, n: float) -> UnitExpr:
    res = {k: v * n for k, v in u.items()}
    return normalize_unit(res)

def format_magnitude(mag: float) -> str:
    return str(float(mag))

def serialize_unit(u: UnitExpr) -> str:
    u = normalize_unit(u)
    if not u:
        return "1"
        
    pos = {k: v for k, v in u.items() if v > 0}
    neg = {k: -v for k, v in u.items() if v < 0}
    
    def format_term(k, v):
        if v == 1:
            return k
        if float(v).is_integer():
            return f"{k}^{int(v)}"
        else:
            return f"{k}^{format_magnitude(v)}"

    num_parts = [format_term(k, v) for k, v in sorted(pos.items())]
    den_parts = [format_term(k, v) for k, v in sorted(neg.items())]
    
    num_str = "*".join(num_parts) if num_parts else "1"
    
    if den_parts:
        den_str = "/".join(den_parts)
        if num_parts:
            return f"{num_str}/{den_str}"
        else:
            return f"1/{den_str}"
    else:
        return num_str

@dataclass
class Value:
    magnitude: float
    unit: UnitExpr

@dataclass
class UnitRelationship:
    target: str
    factor: float
    basis: UnitExpr

class Token:
    def __init__(self, type: str, value: str):
        self.type = type
        self.value = value

class LexerError(Exception): pass

tokens_re = re.compile(r"""
    (?P<NUMBER>(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?) |
    (?P<ID>[A-Za-z][A-Za-z0-9_]*) |
    (?P<OP>[+\-*/^()[\]]) |
    (?P<WS>\s+) |
    (?P<MISC>.)
""", re.VERBOSE)

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.tokens = []
        for match in tokens_re.finditer(text):
            kind = match.lastgroup
            val = match.group()
            if kind == 'WS': continue
            if kind == 'ID':
                if re.fullmatch(r"[a-z][a-z_]*", val):
                    kind = 'UNIT_ID'
                elif re.fullmatch(r"[A-Z][A-Z_]*", val):
                    kind = 'VAR_ID'
                else:
                    raise LexerError(f"Invalid identifier {val}")
            elif kind == 'MISC':
                raise LexerError(f"Invalid token {val}")
            elif kind == 'OP':
                kind = val
            self.tokens.append(Token(kind, val))
        self.tokens.append(Token('EOF', ''))

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def next(self) -> Token:
        t = self.tokens[self.pos]
        if t.type != 'EOF':
            self.pos += 1
        return t

    def expect(self, type: str) -> Token:
        t = self.next()
        if t.type != type:
            raise ParseError(f"Expected {type}, got {t.type}")
        return t

# AST Nodes
class ASTNode: pass
@dataclass
class ValueLiteral(ASTNode):
    magnitude: float
    unit: UnitExpr
@dataclass
class Identifier(ASTNode):
    name: str
@dataclass
class UnaryOp(ASTNode):
    op: str
    operand: ASTNode
@dataclass
class BinaryOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode

def parse_integer(tokens: Lexer) -> int:
    sign = 1
    if tokens.peek().type in ['+', '-']:
        tok = tokens.next()
        if tok.type == '-': sign = -1
        
    tok = tokens.next()
    if tok.type != 'NUMBER' or not re.fullmatch(r"[0-9]+", tok.value):
        raise ParseError("invalid integer")
    return sign * int(tok.value)

def parse_unit_factor(tokens: Lexer) -> UnitExpr:
    if tokens.peek().type == 'UNIT_ID':
        uid = tokens.next().value
        base = {uid: 1.0}
    elif tokens.peek().type == '(':
        tokens.next()
        base = parse_unit_section(tokens)
        tokens.expect(')')
    else:
        raise ParseError("invalid unit factor")
        
    if tokens.peek().type == '^':
        tokens.next()
        exp = parse_integer(tokens)
        base = power_unit(base, exp)
    return base

def parse_unit_section(tokens: Lexer) -> UnitExpr:
    unit = parse_unit_factor(tokens)
    while tokens.peek().type in ['*', '/']:
        op = tokens.next().type
        right = parse_unit_factor(tokens)
        if op == '*': unit = multiply_unit(unit, right)
        else: unit = divide_unit(unit, right)
    return unit

def parse_expr(tokens: Lexer, min_bp: int, mode: str) -> ASTNode:
    tok = tokens.next()
    if tok.type == 'NUMBER':
        val = float(tok.value)
        if not math.isfinite(val):
            raise ParseError("invalid formula.")
            
        peek_type = tokens.peek().type
        if peek_type in ['UNIT_ID', '(']:
            try:
                # We can't really restore state elegantly in python without saving pos
                # but if we fail, we throw ParseError which gets caught outside anyway.
                unit = parse_unit_section(tokens)
                lhs = ValueLiteral(val, unit)
                if tokens.peek().type == '^':
                    raise ParseError("invalid formula.")
            except ParseError:
                raise ParseError("invalid formula.")
        else:
            lhs = ValueLiteral(val, {})
    elif tok.type in ['UNIT_ID', 'VAR_ID']:
        lhs = Identifier(tok.value)
    elif tok.type == '(':
        lhs = parse_expr(tokens, 0, mode)
        tokens.expect(')')
    elif tok.type in ['+', '-', '[', ']']:
        if mode == 'relationship' and tok.type in ['[', ']']:
            raise ParseError("invalid formula.")
        rhs = parse_expr(tokens, 4, mode)
        lhs = UnaryOp(tok.type, rhs)
    else:
        raise ParseError("invalid formula.")
        
    while True:
        peek = tokens.peek()
        if peek.type == 'EOF': break
        op = peek.type
        if op not in ['+', '-', '*', '/', '^']: break
        
        if mode == 'relationship' and op in ['+', '-']:
            raise ParseError("invalid formula.")
            
        if op == '^':
            l_bp, r_bp = 3, 3
        elif op in ['*', '/']:
            l_bp, r_bp = 2, 3
        elif op in ['+', '-']:
            l_bp, r_bp = 1, 2
        else:
            break
            
        if l_bp < min_bp:
            break
            
        tokens.next()
        rhs = parse_expr(tokens, r_bp, mode)
        lhs = BinaryOp(op, lhs, rhs)
        
    return lhs

def parse_value_formula(text: str) -> ASTNode:
    try:
        lexer = Lexer(text)
        expr = parse_expr(lexer, 0, mode='value')
        if lexer.peek().type != 'EOF':
            raise ParseError("invalid formula.")
        return expr
    except LexerError:
        raise ParseError("invalid formula.")

def parse_relationship_formula(text: str) -> ASTNode:
    try:
        lexer = Lexer(text)
        expr = parse_expr(lexer, 0, mode='relationship')
        if lexer.peek().type != 'EOF':
            raise ParseError("invalid formula.")
        return expr
    except LexerError:
        raise ParseError("invalid formula.")

def parse_unit_primary(tokens: Lexer) -> UnitExpr:
    tok = tokens.next()
    if tok.type == 'UNIT_ID':
        return {tok.value: 1.0}
    elif tok.type == 'NUMBER' and tok.value == '1':
        return {}
    elif tok.type == '(':
        res = parse_unit_expression(tokens)
        tokens.expect(')')
        return res
    else:
        raise ParseError("invalid output unit.")

def parse_unit_power(tokens: Lexer) -> UnitExpr:
    res = parse_unit_primary(tokens)
    if tokens.peek().type == '^':
        tokens.next()
        exp = parse_integer(tokens)
        res = power_unit(res, exp)
    return res

def parse_unit_expression(tokens: Lexer) -> UnitExpr:
    res = parse_unit_power(tokens)
    while tokens.peek().type in ['*', '/']:
        op = tokens.next().type
        rhs = parse_unit_power(tokens)
        if op == '*': res = multiply_unit(res, rhs)
        else: res = divide_unit(res, rhs)
    return res

def parse_output_unit_formula(text: str) -> UnitExpr:
    try:
        lexer = Lexer(text)
        unit = parse_unit_expression(lexer)
        if lexer.peek().type != 'EOF':
            raise ParseError("invalid output unit.")
        return unit
    except (LexerError, ParseError):
        raise ParseError("invalid output unit.")

def get_transitions(U: UnitExpr, relationships: Dict[str, UnitRelationship]) -> List[Tuple[str, UnitExpr, float]]:
    transitions = []
    for rel in relationships.values():
        target = rel.target
        factor = rel.factor
        basis = rel.basis
        
        # Forward
        e = U.get(target, 0.0)
        if e != 0:
            next_U = dict(U)
            del next_U[target]
            for k, v in basis.items():
                next_U[k] = next_U.get(k, 0.0) + v * e
            next_U = normalize_unit(next_U)
            try:
                scale = factor ** e
                if not math.isfinite(scale) or isinstance(scale, complex):
                    raise EvalError("invalid relationship.")
                transitions.append((next_U, scale, target, 0))
            except EvalError:
                raise
            except Exception:
                raise EvalError("invalid relationship.")
                
        # Reverse
        r_values = {}
        for x, bx in basis.items():
            if bx != 0:
                r_values[x] = U.get(x, 0.0) / bx
                
        nonzero_r = {x: r for x, r in r_values.items() if r != 0}
        if nonzero_r:
            signs = set(math.copysign(1, r) for r in nonzero_r.values())
            if len(signs) == 1:
                sign = signs.pop()
                min_abs = min(abs(r) for r in nonzero_r.values())
                e = sign * min_abs
                
                next_U = dict(U)
                for x, bx in basis.items():
                    next_U[x] = next_U.get(x, 0.0) - bx * e
                next_U[target] = next_U.get(target, 0.0) + e
                next_U = normalize_unit(next_U)
                
                try:
                    scale = factor ** (-e)
                    if not math.isfinite(scale) or isinstance(scale, complex):
                        raise EvalError("invalid relationship.")
                    transitions.append((next_U, scale, target, 1))
                except EvalError:
                    raise
                except Exception:
                    raise EvalError("invalid relationship.")

    # Sort to satisfy rule 3 and tie-breaking rules
    transitions.sort(key=lambda t: (serialize_unit(t[0]), t[2], t[3]))
    unique_next = []
    seen_next = set()
    for t in transitions:
        ser = serialize_unit(t[0])
        if ser not in seen_next:
            seen_next.add(ser)
            unique_next.append((ser, t[0], t[1]))
    return unique_next

def search_conversion(source: UnitExpr, target: UnitExpr, relationships: Dict[str, UnitRelationship]) -> Optional[float]:
    source_ser = serialize_unit(source)
    target_ser = serialize_unit(target)
    
    if source_ser == target_ser:
        return 1.0
        
    visited = {source_ser}
    # (path_key, current_ser, current_U, scale)
    queue = [([source_ser], source_ser, source, 1.0)]
    
    while queue:
        for item in queue:
            if item[1] == target_ser:
                return item[3]
                
        next_level = []
        for path_key, q_ser, q_U, q_scale in queue:
            transitions = get_transitions(q_U, relationships)
            for n_ser, n_U, step_scale in transitions:
                if n_ser not in visited:
                    visited.add(n_ser)
                    next_level.append((path_key + [n_ser], n_ser, n_U, q_scale * step_scale))
                    
        next_level.sort(key=lambda x: x[0])
        queue = next_level
        
    return None

class Context:
    def __init__(self, units: Set[str], variables: Dict[str, Value], relationships: Dict[str, UnitRelationship], mode: str = "value", source_units: Optional[List[str]] = None):
        self.units = units
        self.variables = variables
        self.relationships = relationships
        self.mode = mode
        self.source_units = source_units or []

    def has_unit(self, name: str) -> bool:
        if self.mode == "relationship":
            return name in self.source_units
        return name in self.units

    def resolve_identifier(self, name: str) -> Value:
        if re.fullmatch(r"[A-Z][A-Z_]*", name):
            if self.mode == "relationship":
                raise EvalError(f"unknown unit {name}.")
            else:
                if name in self.variables:
                    return self.variables[name]
                else:
                    raise EvalError(f"unknown variable {name}.")
        elif re.fullmatch(r"[a-z][a-z_]*", name):
            if self.mode == "relationship":
                if name in self.source_units:
                    return Value(1.0, {name: 1.0})
                else:
                    raise EvalError(f"unknown unit {name}.")
            else:
                if name in self.units:
                    return Value(1.0, {name: 1.0})
                else:
                    raise EvalError(f"unknown unit {name}.")
        else:
            raise EvalError("invalid formula.")

    def convert(self, value: Value, target_unit: UnitExpr) -> Value:
        if value.unit == target_unit:
            return Value(value.magnitude, value.unit)
        scale = search_conversion(value.unit, target_unit, self.relationships)
        if scale is None:
            raise EvalError(f"cannot convert {serialize_unit(value.unit)} to {serialize_unit(target_unit)}.")
        return Value(value.magnitude * scale, target_unit)

def safe_power(a: float, b: float) -> float:
    try:
        res = a ** b
    except ZeroDivisionError:
        raise EvalError("division by zero.")
    except Exception:
        raise EvalError("numeric result is not real.")
    if isinstance(res, complex):
        raise EvalError("numeric result is not real.")
    if not math.isfinite(res):
        raise EvalError("numeric result is not finite.")
    return res

def evaluate_ast(node: ASTNode, ctx: Context) -> Value:
    if isinstance(node, ValueLiteral):
        for u in node.unit.keys():
            if not ctx.has_unit(u):
                raise EvalError(f"unknown unit {u}.")
        return Value(node.magnitude, normalize_unit(node.unit))
        
    elif isinstance(node, Identifier):
        return ctx.resolve_identifier(node.name)
        
    elif isinstance(node, UnaryOp):
        operand = evaluate_ast(node.operand, ctx)
        if node.op == '+':
            res_mag = operand.magnitude
        elif node.op == '-':
            res_mag = -operand.magnitude
        elif node.op == '[':
            if operand.unit: raise EvalError("log argument must be scalar.")
            if operand.magnitude <= 0: raise EvalError("log argument must be positive.")
            res_mag = math.log(operand.magnitude)
        elif node.op == ']':
            if operand.unit: raise EvalError("exp argument must be scalar.")
            try:
                res_mag = math.exp(operand.magnitude)
            except OverflowError:
                raise EvalError("numeric result is not finite.")
        else:
            raise EvalError("invalid formula.")
            
        if not math.isfinite(res_mag):
            raise EvalError("numeric result is not finite.")
        if isinstance(res_mag, complex):
            raise EvalError("numeric result is not real.")
            
        return Value(res_mag, operand.unit if node.op in ['+', '-'] else {})
        
    elif isinstance(node, BinaryOp):
        left = evaluate_ast(node.left, ctx)
        right = evaluate_ast(node.right, ctx)
        
        if node.op == '*':
            res_mag = left.magnitude * right.magnitude
            res_unit = multiply_unit(left.unit, right.unit)
        elif node.op == '/':
            if right.magnitude == 0: raise EvalError("division by zero.")
            res_mag = left.magnitude / right.magnitude
            res_unit = divide_unit(left.unit, right.unit)
        elif node.op == '^':
            if right.unit: raise EvalError("exponent must be scalar.")
            res_mag = safe_power(left.magnitude, right.magnitude)
            res_unit = power_unit(left.unit, right.magnitude) if left.unit else {}
        elif node.op in ['+', '-']:
            try:
                right_conv = ctx.ctx.convert(right, left.unit)
                mag_left = left.magnitude
                mag_right = right_conv.magnitude
                res_unit = left.unit
            except EvalError:
                try:
                    left_conv = ctx.convert(left, right.unit)
                    mag_left = left_conv.magnitude
                    mag_right = right.magnitude
                    res_unit = right.unit
                except EvalError:
                    raise EvalError(f"cannot convert {serialize_unit(right.unit)} to {serialize_unit(left.unit)}.")
            
            if node.op == '+':
                res_mag = mag_left + mag_right
            else:
                res_mag = mag_left - mag_right
        else:
            raise EvalError("invalid formula.")
            
        if not math.isfinite(res_mag):
            raise EvalError("numeric result is not finite.")
        if isinstance(res_mag, complex):
            raise EvalError("numeric result is not real.")
            
        return Value(res_mag, res_unit)
    
    raise EvalError("invalid formula.")

class CLI:
    def __init__(self):
        self.units = set()
        self.variables = {}
        self.relationships = {}

    def execute(self, line: str) -> List[str]:
        line = line.strip()
        if not line:
            return []
            
        try:
            if line.startswith("unit:"):
                payload = line[5:].strip()
                if not payload:
                    raise Error("invalid command syntax.")
                if not re.fullmatch(r"[a-z][a-z_]*", payload):
                    raise Error("invalid unit name.")
                self.units.add(payload)
                return []
                
            elif line.startswith("set:"):
                payload = line[4:].strip()
                if ":" not in payload:
                    raise Error("invalid command syntax.")
                var_id, formula = payload.split(":", 1)
                var_id = var_id.strip()
                formula = formula.strip()
                
                if not var_id or not formula:
                    raise Error("invalid command syntax.")
                if not re.fullmatch(r"[A-Z][A-Z_]*", var_id):
                    raise Error("invalid variable name.")
                    
                ast = parse_value_formula(formula)
                ctx = Context(self.units, self.variables, self.relationships, mode="value")
                val = evaluate_ast(ast, ctx)
                
                self.variables[var_id] = val
                return []
                
            elif line.startswith("relate:"):
                payload = line[7:].strip()
                parts = payload.split(":", 2)
                if len(parts) != 3:
                    raise Error("invalid command syntax.")
                
                target, sources_str, formula = [p.strip() for p in parts]
                if not target or not sources_str or not formula:
                    raise Error("invalid command syntax.")
                    
                if not re.fullmatch(r"[a-z][a-z_]*", target):
                    raise Error("invalid unit name.")
                    
                sources = [s.strip() for s in sources_str.split(",")]
                if not all(sources):
                    raise Error("invalid unit list.")
                if len(sources) != len(set(sources)):
                    raise Error("invalid unit list.")
                    
                for s in sources:
                    if not re.fullmatch(r"[a-z][a-z_]*", s):
                        raise Error("invalid unit list.")
                    if s not in self.units:
                        raise Error("invalid unit list.")
                        
                if target in sources:
                    raise Error("invalid unit list.")
                    
                ast = parse_relationship_formula(formula)
                ctx = Context(self.units, self.variables, self.relationships, mode="relationship", source_units=sources)
                val = evaluate_ast(ast, ctx)
                
                if not math.isfinite(val.magnitude) or val.magnitude == 0:
                    raise Error("invalid relationship.")
                    
                for u in val.unit.keys():
                    if u not in sources:
                        raise Error("invalid relationship.")
                        
                self.units.add(target)
                self.relationships[target] = UnitRelationship(target, val.magnitude, val.unit)
                return []
                
            elif line.startswith("evaluate:"):
                payload = line[9:].strip()
                
                if ":" in payload:
                    formula, out_formula = payload.rsplit(":", 1)
                    formula = formula.strip()
                    out_formula = out_formula.strip()
                    
                    if not formula or not out_formula:
                        raise Error("invalid command syntax.")
                        
                    out_ast = parse_output_unit_formula(out_formula)
                    ast = parse_value_formula(formula)
                    
                    target_unit = out_ast
                    for u in target_unit.keys():
                        if u not in self.units:
                            raise Error(f"unknown unit {u}.")
                            
                    ctx = Context(self.units, self.variables, self.relationships, mode="value")
                    val = evaluate_ast(ast, ctx)
                    val_conv = ctx.convert(val, target_unit)
                    
                    mag_str = format_magnitude(val_conv.magnitude)
                    unit_str = serialize_unit(val_conv.unit)
                    return [f"{mag_str} {unit_str}"]
                    
                else:
                    formula = payload
                    if not formula:
                        raise Error("invalid command syntax.")
                        
                    ast = parse_value_formula(formula)
                    ctx = Context(self.units, self.variables, self.relationships, mode="value")
                    val = evaluate_ast(ast, ctx)
                    
                    mag_str = format_magnitude(val.magnitude)
                    unit_str = serialize_unit(val.unit)
                    return [f"{mag_str} {unit_str}"]
                    
            else:
                raise Error("unknown command.")
                
        except Error as e:
            return [f"Error: {e}"]
        except ParseError as e:
            return [f"Error: {e}"]
        except EvalError as e:
            return [f"Error: {e}"]

def run_transcript(commands: List[str]) -> List[str]:
    cli = CLI()
    output = []
    for cmd in commands:
        output.extend(cli.execute(cmd))
    return output

if __name__ == '__main__':
    cli = CLI()
    for line in sys.stdin:
        line = line.strip()
        if line:
            for out in cli.execute(line):
                print(out)
