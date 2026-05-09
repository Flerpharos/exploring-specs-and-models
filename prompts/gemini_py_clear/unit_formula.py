import sys
import re
import math
from collections import deque

class Error(Exception):
    pass

class UnitExpr:
    def __init__(self, powers=None):
        self.powers = {}
        if powers:
            for k, v in powers.items():
                if v != 0:
                    self.powers[k] = v

    def __eq__(self, other):
        if not isinstance(other, UnitExpr):
            return False
        return self.powers == other.powers

    def __hash__(self):
        return hash(frozenset(self.powers.items()))

    def __repr__(self):
        return f"UnitExpr({self.powers})"

    def copy(self):
        return UnitExpr(self.powers)

def multiply_units(u1, u2):
    res = dict(u1.powers)
    for k, v in u2.powers.items():
        res[k] = res.get(k, 0) + v
    return UnitExpr(res)

def divide_units(u1, u2):
    res = dict(u1.powers)
    for k, v in u2.powers.items():
        res[k] = res.get(k, 0) - v
    return UnitExpr(res)

def power_unit(u1, n):
    return UnitExpr({k: v * n for k, v in u1.powers.items()})

def serialize_unit(u):
    if not u.powers:
        return "1"
    
    num = []
    den = []
    for k in sorted(u.powers.keys()):
        v = u.powers[k]
        if v > 0:
            num.append((k, v))
        else:
            den.append((k, -v))
    
    def format_part(parts):
        res = []
        for k, v in parts:
            if v == 1:
                res.append(k)
            else:
                if isinstance(v, int) or (isinstance(v, float) and v.is_integer()):
                    res.append(f"{k}^{int(v)}")
                else:
                    res.append(f"{k}^{v}")
        return "*".join(res)
    
    num_str = format_part(num)
    den_str = format_part(den)
    
    if not num_str and den_str:
        return f"1/{den_str}"
    elif num_str and not den_str:
        return num_str
    else:
        return f"{num_str}/{den_str}"

class Value:
    def __init__(self, magnitude, unit_expr):
        self.magnitude = magnitude
        self.unit_expr = unit_expr
        if not math.isfinite(magnitude):
            raise Error("Error: numeric result is not finite.")

class UnitRelationship:
    def __init__(self, target, factor, basis):
        self.target = target
        self.factor = factor
        self.basis = basis

class Env:
    def __init__(self):
        self.units = set()
        self.variables = {}
        self.relationships = {}

def is_valid_unit_id(s):
    return bool(re.match(r'^[a-z][a-z_]*$', s))

def is_valid_var_id(s):
    return bool(re.match(r'^[A-Z][A-Z_]*$', s))

def parse_number(s):
    try:
        f = float(s)
        if not math.isfinite(f):
            raise ValueError
        return f
    except ValueError:
        raise Error("Error: numeric result is not finite.")

TOKEN_PATTERNS = [
    ('NUMBER', r'(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?'),
    ('ID', r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('OP', r'[+\-*/^()\[\]]'),
    ('WS', r'\s+'),
    ('MISC', r'.')
]
TOKEN_REGEX = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_PATTERNS))

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value
    def __repr__(self):
        return f"Token({self.type}, {self.value})"

def tokenize(s):
    tokens = []
    for match in TOKEN_REGEX.finditer(s):
        kind = match.lastgroup
        value = match.group(kind)
        if kind == 'WS':
            continue
        elif kind == 'MISC':
            tokens.append(Token('INVALID', value))
        elif kind == 'ID':
            if is_valid_unit_id(value):
                tokens.append(Token('UNIT_ID', value))
            elif is_valid_var_id(value):
                tokens.append(Token('VAR_ID', value))
            else:
                tokens.append(Token('INVALID_ID', value))
        else:
            tokens.append(Token(kind, value))
    return tokens

class Parser:
    def __init__(self, tokens, env, context, source_units=None):
        self.tokens = tokens
        self.pos = 0
        self.env = env
        self.context = context
        self.source_units = source_units or []

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self):
        if self.pos < len(self.tokens):
            t = self.tokens[self.pos]
            self.pos += 1
            return t
        return None

    def match(self, *types):
        t = self.peek()
        if t and t.type in types:
            return self.advance()
        return None

    def match_val(self, *vals):
        t = self.peek()
        if t and t.value in vals:
            return self.advance()
        return None

    def parse_value_formula(self):
        expr = self.parse_expr(1)
        if self.peek() is not None:
            raise Error("Error: invalid formula.")
        return expr

    def parse_expr(self, min_prec):
        t = self.peek()
        if t is None:
            raise Error("Error: invalid formula.")
        
        if self.match_val('('):
            left = self.parse_expr(1)
            if not self.match_val(')'):
                raise Error("Error: invalid formula.")
        elif self.match_val('['):
            if self.context == 'relationship':
                raise Error("Error: invalid formula.")
            operand = self.parse_expr(4)
            left = ('LOG', operand)
        elif self.match_val(']'):
            if self.context == 'relationship':
                raise Error("Error: invalid formula.")
            operand = self.parse_expr(4)
            left = ('EXP', operand)
        elif self.match_val('+'):
            operand = self.parse_expr(4)
            left = ('UPLUS', operand)
        elif self.match_val('-'):
            operand = self.parse_expr(4)
            left = ('UMINUS', operand)
        elif t.type == 'NUMBER':
            left = self.parse_value_literal()
        elif t.type in ('UNIT_ID', 'VAR_ID', 'INVALID_ID'):
            left = self.parse_ident()
        else:
            raise Error("Error: invalid formula.")

        while True:
            t = self.peek()
            if not t or t.type != 'OP':
                break
            
            op = t.value
            if op == '^':
                prec, assoc = 3, 'R'
            elif op in ('*', '/'):
                prec, assoc = 2, 'L'
            elif op in ('+', '-'):
                prec, assoc = 1, 'L'
            else:
                break
                
            if prec < min_prec:
                break
                
            self.advance()
            next_min_prec = prec + 1 if assoc == 'L' else prec
            right = self.parse_expr(next_min_prec)
            
            left = ('BINOP', op, left, right)
            
        return left

    def parse_value_literal(self):
        t = self.advance()
        mag = parse_number(t.value)
        has_unit = False
        unit_expr = UnitExpr()
        
        saved_pos = self.pos
        try:
            pt = self.peek()
            if pt and (pt.type == 'UNIT_ID' or pt.value == '('):
                unit_expr = self.parse_unit_section()
                has_unit = True
        except Error:
            self.pos = saved_pos
            
        if has_unit:
            pt = self.peek()
            if pt and pt.value == '^':
                raise Error("Error: invalid formula.")
        
        return ('LITERAL', mag, unit_expr)

    def parse_ident(self):
        t = self.advance()
        if t.type == 'INVALID_ID':
            raise Error("Error: invalid formula.")
        return ('IDENT', t.value, t.type)

    def parse_unit_section(self):
        u = self.parse_unit_factor()
        while True:
            t = self.peek()
            if t and t.value in ('*', '/'):
                op = t.value
                self.advance()
                try:
                    right = self.parse_unit_factor()
                except Error:
                    raise Error("Error: invalid formula.")
                if op == '*':
                    u = multiply_units(u, right)
                else:
                    u = divide_units(u, right)
            else:
                break
        return u

    def parse_unit_factor(self):
        t = self.peek()
        if not t:
            raise Error("Error: invalid formula.")
        if t.type == 'UNIT_ID':
            self.advance()
            u = UnitExpr({t.value: 1})
            exp = self.parse_optional_integer_exponent()
            if exp != 1:
                u = power_unit(u, exp)
            return u
        elif t.value == '(':
            self.advance()
            u = self.parse_unit_section()
            if not self.match_val(')'):
                raise Error("Error: invalid formula.")
            exp = self.parse_optional_integer_exponent()
            if exp != 1:
                u = power_unit(u, exp)
            return u
        else:
            raise Error("Error: invalid formula.")

    def parse_optional_integer_exponent(self):
        if self.match_val('^'):
            sign = 1
            if self.match_val('+'):
                sign = 1
            elif self.match_val('-'):
                sign = -1
            t = self.peek()
            if t and t.type == 'NUMBER' and '.' not in t.value and 'e' not in t.value.lower():
                self.advance()
                return sign * int(t.value)
            raise Error("Error: invalid formula.")
        return 1

    def parse_output_unit_formula(self):
        u = self.parse_unit_expression()
        if self.peek() is not None:
            raise Error("Error: invalid output unit.")
        return u

    def parse_unit_expression(self):
        u = self.parse_unit_power()
        while True:
            t = self.peek()
            if t and t.value in ('*', '/'):
                op = t.value
                self.advance()
                right = self.parse_unit_power()
                if op == '*':
                    u = multiply_units(u, right)
                else:
                    u = divide_units(u, right)
            else:
                break
        return u

    def parse_unit_power(self):
        u = self.parse_unit_primary()
        exp = self.parse_optional_integer_exponent_out()
        if exp != 1:
            u = power_unit(u, exp)
        return u

    def parse_optional_integer_exponent_out(self):
        if self.match_val('^'):
            sign = 1
            if self.match_val('+'):
                sign = 1
            elif self.match_val('-'):
                sign = -1
            t = self.peek()
            if t and t.type == 'NUMBER' and '.' not in t.value and 'e' not in t.value.lower():
                self.advance()
                return sign * int(t.value)
            raise Error("Error: invalid output unit.")
        return 1

    def parse_unit_primary(self):
        t = self.peek()
        if not t:
            raise Error("Error: invalid output unit.")
        if t.type == 'UNIT_ID':
            self.advance()
            return UnitExpr({t.value: 1})
        elif t.type == 'NUMBER' and t.value == '1':
            self.advance()
            return UnitExpr()
        elif t.value == '(':
            self.advance()
            u = self.parse_unit_expression()
            if not self.match_val(')'):
                raise Error("Error: invalid output unit.")
            return u
        else:
            raise Error("Error: invalid output unit.")

class Evaluator:
    def __init__(self, env, context, source_units=None):
        self.env = env
        self.context = context
        self.source_units = source_units or []

    def evaluate(self, ast):
        if ast[0] == 'LITERAL':
            _, mag, u = ast
            if self.context == 'relationship':
                for k in u.powers.keys():
                    if k not in self.source_units:
                        raise Error(f"Error: unknown unit {k}.")
            else:
                for k in u.powers.keys():
                    if k not in self.env.units:
                        raise Error(f"Error: unknown unit {k}.")
            return Value(mag, u)
            
        elif ast[0] == 'IDENT':
            _, name, ttype = ast
            if self.context == 'value':
                if ttype == 'VAR_ID':
                    if name in self.env.variables:
                        return self.env.variables[name]
                    else:
                        raise Error(f"Error: unknown variable {name}.")
                elif ttype == 'UNIT_ID':
                    if name in self.env.units:
                        return Value(1.0, UnitExpr({name: 1}))
                    else:
                        raise Error(f"Error: unknown unit {name}.")
            elif self.context == 'relationship':
                if ttype == 'UNIT_ID' and name in self.source_units:
                    return Value(1.0, UnitExpr({name: 1}))
                else:
                    raise Error(f"Error: unknown unit {name}.")
            raise Error("Error: invalid formula.")
            
        elif ast[0] == 'UPLUS':
            val = self.evaluate(ast[1])
            return Value(val.magnitude, val.unit_expr)
            
        elif ast[0] == 'UMINUS':
            val = self.evaluate(ast[1])
            return Value(-val.magnitude, val.unit_expr)
            
        elif ast[0] == 'LOG':
            val = self.evaluate(ast[1])
            if val.unit_expr.powers:
                raise Error("Error: log argument must be scalar.")
            if val.magnitude <= 0:
                raise Error("Error: log argument must be positive.")
            return Value(math.log(val.magnitude), UnitExpr())
            
        elif ast[0] == 'EXP':
            val = self.evaluate(ast[1])
            if val.unit_expr.powers:
                raise Error("Error: exp argument must be scalar.")
            try:
                res = math.exp(val.magnitude)
            except OverflowError:
                raise Error("Error: numeric result is not finite.")
            return Value(res, UnitExpr())
            
        elif ast[0] == 'BINOP':
            _, op, left_ast, right_ast = ast
            
            if self.context == 'relationship' and op in ('+', '-'):
                raise Error("Error: invalid formula.")
                
            left = self.evaluate(left_ast)
            right = self.evaluate(right_ast)
            
            if op == '*':
                return Value(left.magnitude * right.magnitude, multiply_units(left.unit_expr, right.unit_expr))
            elif op == '/':
                if right.magnitude == 0:
                    raise Error("Error: division by zero.")
                return Value(left.magnitude / right.magnitude, divide_units(left.unit_expr, right.unit_expr))
            elif op == '^':
                if right.unit_expr.powers:
                    raise Error("Error: exponent must be scalar.")
                try:
                    if left.magnitude == 0 and right.magnitude < 0:
                        raise Error("Error: numeric result is not finite.")
                    if left.magnitude < 0 and not right.magnitude.is_integer():
                        raise Error("Error: numeric result is not real.")
                    mag = math.pow(left.magnitude, right.magnitude)
                except ValueError:
                    raise Error("Error: numeric result is not real.")
                except OverflowError:
                    raise Error("Error: numeric result is not finite.")
                if isinstance(mag, complex):
                    raise Error("Error: numeric result is not real.")
                return Value(mag, power_unit(left.unit_expr, right.magnitude))
            elif op in ('+', '-'):
                if left.unit_expr == right.unit_expr:
                    if op == '+':
                        return Value(left.magnitude + right.magnitude, left.unit_expr)
                    else:
                        return Value(left.magnitude - right.magnitude, left.unit_expr)
                
                try:
                    right_mag_conv = convert(right.magnitude, right.unit_expr, left.unit_expr, self.env)
                    if op == '+':
                        return Value(left.magnitude + right_mag_conv, left.unit_expr)
                    else:
                        return Value(left.magnitude - right_mag_conv, left.unit_expr)
                except Error:
                    try:
                        left_mag_conv = convert(left.magnitude, left.unit_expr, right.unit_expr, self.env)
                        if op == '+':
                            return Value(left_mag_conv + right.magnitude, right.unit_expr)
                        else:
                            return Value(left_mag_conv - right.magnitude, right.unit_expr)
                    except Error:
                        raise Error(f"Error: cannot convert {serialize_unit(right.unit_expr)} to {serialize_unit(left.unit_expr)}.")

def convert(magnitude, source_unit, target_unit, env):
    if source_unit == target_unit:
        return magnitude
    
    queue = deque([(source_unit, magnitude, [serialize_unit(source_unit)])])
    visited = {source_unit}
    
    target_str = serialize_unit(target_unit)
    
    while queue:
        level_size = len(queue)
        successes = []
        current_level_states = []
        
        for _ in range(level_size):
            curr_unit, curr_mag, path_keys = queue.popleft()
            
            if curr_unit == target_unit:
                successes.append((path_keys, curr_mag))
                continue
            
            next_states = []
            
            for rel in env.relationships.values():
                if not math.isfinite(rel.factor) or rel.factor == 0:
                    raise Error("Error: invalid relationship.")
                
                if rel.target in curr_unit.powers:
                    e = curr_unit.powers[rel.target]
                    next_powers = dict(curr_unit.powers)
                    del next_powers[rel.target]
                    
                    for k, v in rel.basis.powers.items():
                        next_powers[k] = next_powers.get(k, 0) + e * v
                    
                    next_u = UnitExpr(next_powers)
                    try:
                        scale_mult = math.pow(rel.factor, e)
                        if isinstance(scale_mult, complex):
                            raise Error("Error: invalid relationship.")
                        if not math.isfinite(scale_mult):
                            raise Error("Error: invalid relationship.")
                    except (ValueError, OverflowError):
                        raise Error("Error: invalid relationship.")
                    
                    next_mag = curr_mag * scale_mult
                    next_states.append((next_u, next_mag, 'F', rel.target))

                basis_units = rel.basis.powers
                if basis_units:
                    ratios = {}
                    for k, v in basis_units.items():
                        cu = curr_unit.powers.get(k, 0)
                        ratios[k] = cu / v
                    
                    non_zero_ratios = {k: v for k, v in ratios.items() if v != 0}
                    if non_zero_ratios:
                        signs = set(math.copysign(1, v) for v in non_zero_ratios.values())
                        if len(signs) == 1:
                            sign = signs.pop()
                            abs_e = min(abs(v) for v in non_zero_ratios.values())
                            e = abs_e * sign
                            
                            next_powers = dict(curr_unit.powers)
                            for k, v in basis_units.items():
                                next_powers[k] = next_powers.get(k, 0) - v * e
                            next_powers[rel.target] = next_powers.get(rel.target, 0) + e
                            
                            next_u = UnitExpr(next_powers)
                            try:
                                scale_mult = math.pow(rel.factor, -e)
                                if isinstance(scale_mult, complex):
                                    raise Error("Error: invalid relationship.")
                                if not math.isfinite(scale_mult):
                                    raise Error("Error: invalid relationship.")
                            except (ValueError, OverflowError):
                                raise Error("Error: invalid relationship.")
                                
                            next_mag = curr_mag * scale_mult
                            next_states.append((next_u, next_mag, 'R', rel.target))

            for next_u, next_mag, d_dir, d_target in next_states:
                current_level_states.append((next_u, next_mag, d_dir, d_target, path_keys))

        if successes:
            successes.sort()
            return successes[0][1]
            
        if not current_level_states:
            break
            
        grouped = {}
        for next_u, next_mag, d_dir, d_target, path_keys in current_level_states:
            if next_u in visited:
                continue
                
            serialized_next_u = serialize_unit(next_u)
            new_path_keys = path_keys + [serialized_next_u]
            tie_key = (new_path_keys, d_target, 0 if d_dir == 'F' else 1)
            
            if next_u not in grouped:
                grouped[next_u] = (tie_key, next_mag)
            else:
                if tie_key < grouped[next_u][0]:
                    grouped[next_u] = (tie_key, next_mag)
                    
        sorted_next = sorted(grouped.items(), key=lambda x: x[1][0][0])
        
        for next_u, (tie_key, next_mag) in sorted_next:
            visited.add(next_u)
            queue.append((next_u, next_mag, tie_key[0]))
            
    raise Error(f"Error: cannot convert {serialize_unit(source_unit)} to {target_str}.")

def run_command(cmd, env):
    try:
        if cmd.startswith("unit:"):
            payload = cmd[5:].strip()
            if not payload:
                raise Error("Error: invalid command syntax.")
            if not is_valid_unit_id(payload):
                raise Error("Error: invalid unit name.")
            env.units.add(payload)
            
        elif cmd.startswith("set:"):
            payload = cmd[4:].strip()
            if ":" not in payload:
                raise Error("Error: invalid command syntax.")
            var_id, val_formula = map(str.strip, payload.split(":", 1))
            if not var_id or not val_formula:
                raise Error("Error: invalid command syntax.")
            if not is_valid_var_id(var_id):
                raise Error("Error: invalid variable name.")
            
            tokens = tokenize(val_formula)
            parser = Parser(tokens, env, 'value')
            ast = parser.parse_value_formula()
            
            evaluator = Evaluator(env, 'value')
            val = evaluator.evaluate(ast)
            
            env.variables[var_id] = val
            
        elif cmd.startswith("relate:"):
            payload = cmd[7:].strip()
            parts = payload.split(":")
            if len(parts) < 3:
                raise Error("Error: invalid command syntax.")
            target_id = parts[0].strip()
            source_list_str = parts[1].strip()
            rel_formula = ":".join(parts[2:]).strip()
            
            if not target_id or not source_list_str or not rel_formula:
                raise Error("Error: invalid command syntax.")
                
            if not is_valid_unit_id(target_id):
                raise Error("Error: invalid unit name.")
                
            sources = [s.strip() for s in source_list_str.split(",")]
            if any(not s for s in sources):
                raise Error("Error: invalid unit list.")
            if len(set(sources)) != len(sources):
                raise Error("Error: invalid unit list.")
            for s in sources:
                if not is_valid_unit_id(s):
                    raise Error("Error: invalid unit list.")
                if s not in env.units:
                    raise Error("Error: invalid unit list.")
                    
            if target_id in sources:
                raise Error("Error: invalid unit list.")
                
            tokens = tokenize(rel_formula)
            parser = Parser(tokens, env, 'relationship', source_units=sources)
            ast = parser.parse_value_formula()
            
            evaluator = Evaluator(env, 'relationship', source_units=sources)
            val = evaluator.evaluate(ast)
            
            if not math.isfinite(val.magnitude) or val.magnitude == 0:
                raise Error("Error: invalid relationship.")
            
            for k in val.unit_expr.powers:
                if k not in sources:
                    raise Error("Error: invalid relationship.")
                    
            env.units.add(target_id)
            env.relationships[target_id] = UnitRelationship(target_id, val.magnitude, val.unit_expr)
            
        elif cmd.startswith("evaluate:"):
            payload = cmd[9:].strip()
            if not payload:
                raise Error("Error: invalid command syntax.")
                
            if ":" in payload:
                val_formula, out_unit_formula = map(str.strip, payload.rsplit(":", 1))
                if not val_formula or not out_unit_formula:
                    raise Error("Error: invalid command syntax.")
                    
                try:
                    tokens_out = tokenize(out_unit_formula)
                    parser_out = Parser(tokens_out, env, 'output_unit')
                    out_unit_expr = parser_out.parse_output_unit_formula()
                    
                    for k in out_unit_expr.powers:
                        if k not in env.units:
                            raise Error(f"Error: unknown unit {k}.")
                except Error as e:
                    if str(e).startswith("Error: invalid output unit") or str(e).startswith("Error: unknown unit"):
                        raise
                    else:
                        raise Error("Error: invalid output unit.")
                        
                tokens_val = tokenize(val_formula)
                parser_val = Parser(tokens_val, env, 'value')
                ast_val = parser_val.parse_value_formula()
                
                evaluator = Evaluator(env, 'value')
                val = evaluator.evaluate(ast_val)
                
                conv_mag = convert(val.magnitude, val.unit_expr, out_unit_expr, env)
                return f"{conv_mag} {serialize_unit(out_unit_expr)}"
                
            else:
                val_formula = payload
                tokens_val = tokenize(val_formula)
                parser_val = Parser(tokens_val, env, 'value')
                ast_val = parser_val.parse_value_formula()
                
                evaluator = Evaluator(env, 'value')
                val = evaluator.evaluate(ast_val)
                
                return f"{val.magnitude} {serialize_unit(val.unit_expr)}"
                
        else:
            raise Error("Error: unknown command.")
            
    except Error as e:
        return str(e)
        
    return None

def main():
    env = Env()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        res = run_command(line, env)
        if res is not None:
            print(res)

if __name__ == '__main__':
    main()