from formula import parse_value_formula, parse_expr, Lexer
import traceback

try:
    l = Lexer("-2^2")
    res = parse_expr(l, 0, 'value')
    print(res)
    print("Next:", l.peek().type)
except Exception as e:
    traceback.print_exc()
