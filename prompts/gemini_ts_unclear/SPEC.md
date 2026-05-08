# Technical Specification: Unit-Aware Formula CLI

## 1. Model

The CLI maintains one session environment.

Semantically, the environment consists of:

```text
Units          Set<UnitId>
Variables      Map<VariableId, Value>
Relationships  Map<UnitId, UnitRelationship>
```

A failed command leaves the environment unchanged.

A `Value` is:

```text
Value {
  magnitude: Real
  unit: UnitExpr
}
```

`Real` is a finite real numeric type.

A scalar value has unit `1`, represented semantically as an empty unit expression:

```text
{}
```

A `UnitExpr` is semantically a normalized finite mapping:

```text
UnitExpr = Map<UnitId, RealExponent>
```

Examples:

```text
1        => {}
m        => { m: 1 }
m/s      => { m: 1, s: -1 }
kg*m/s^2 => { kg: 1, m: 1, s: -2 }
m^0.5    => { m: 0.5 }
```

Input unit syntax accepts only integer exponents. Formula evaluation may produce `UnitExpr` values with non-integer real exponents, for example through the formula power operator. Such `UnitExpr` values may be serialized, but they cannot necessarily be written back as input unit syntax unless their exponents are integers.

Unit expression normalization:

```text
combine repeated unit identifiers by adding exponents
remove unit identifiers whose exponent is 0
serialize identifiers in deterministic order
```

Unit algebra:

```text
multiply(U, V): result[x] = U[x] + V[x]
divide(U, V):   result[x] = U[x] - V[x]
power(U, n):    result[x] = U[x] * n
```

A unit relationship is:

```text
UnitRelationship {
  target: UnitId
  factor: Real
  basis: UnitExpr
}
```

Meaning:

```text
1 target = factor basis
```

A relationship is valid when:

```text
factor is finite
factor != 0
basis is normalized
```

For every stored relationship:

```text
Relationships[k].target == k
```

---

## 2. Lexical Rules

Identifiers are namespace-specific.

```ebnf
lowercase-letter = "a"…"z" ;
uppercase-letter = "A"…"Z" ;

unit-id =
    lowercase-letter { lowercase-letter | "_" } ;

variable-id =
    uppercase-letter { uppercase-letter | "_" } ;
```

Definitions:

```text
UnitId      = unit-id
VariableId  = variable-id
```

Unit identifiers must start with a lowercase alphabetic character and may contain only lowercase alphabetic characters and underscores.

Variable identifiers must start with an uppercase alphabetic character and may contain only uppercase alphabetic characters and underscores.

Digits are not allowed in either unit identifiers or variable identifiers.

Examples:

```text
valid UnitId:      m, kg, meter, meters_per_second
invalid UnitId:    _m, m2, Meter, METER

valid VariableId:  X, SPEED, SPEED_AVG
invalid VariableId: _X, X2, Speed, speed
```

Numbers:

```ebnf
number =
    digits [ "." digits ] [ exponent-part ]
  | "." digits [ exponent-part ] ;

digits = digit { digit } ;
digit = "0"…"9" ;
exponent-part = ( "e" | "E" ) [ "+" | "-" ] digits ;
```

A number must parse to a finite real value.

Integers:

```ebnf
integer = [ "+" | "-" ] digit { digit } ;
```

Formula tokens:

```text
NUMBER
UNIT_IDENTIFIER
VARIABLE_IDENTIFIER
+
-
*
/
^
(
)
[
]
EOF
```

Whitespace:

```text
Whitespace is ignored after lexing.

Whitespace is only used to separate tokens where separation is otherwise ambiguous.

Whitespace is not allowed inside identifiers or numbers.
```

Because `UnitId` and `VariableId` are lexically disjoint, a valid identifier token can be classified before name lookup.

Lowercase identifiers are units. Uppercase identifiers are variables. Mixed-case identifiers and identifiers containing digits are invalid formula tokens.

Examples:

```text
1 m
1m
1 m / s
1m/s
```

are tokenized equivalently where possible.

---

## 3. Commands

The CLI reads UTF-8 input, one command per line. Empty lines are ignored. Command prefixes are case-sensitive.

Supported commands:

```text
unit:<unit-id>
set:<variable-id>:<value-formula>
relate:<target-unit-id>:<source-unit-id-list>:<relationship-formula>
evaluate:<value-formula>[:<output-unit-formula>]
```

Parsing:

```text
unit:
  payload after "unit:" is unit-id

set:
  payload after "set:" is split once at the first ":"
  left  = variable-id
  right = value-formula

relate:
  payload after "relate:" is split twice from the left
  field 1 = target-unit-id
  field 2 = source-unit-id-list
  field 3 = relationship-formula

evaluate:
  payload after "evaluate:" is split once at the last ":"

  if no ":" appears in the payload:
    field 1 = value-formula
    field 2 = omitted

  if ":" appears in the payload:
    field 1 = value-formula
    field 2 = output-unit-formula
```

All command fields are trimmed. Required fields must be non-empty.

For `evaluate`, the `value-formula` field is required and must be non-empty. If the `output-unit-formula` field is present, it must be non-empty.

A source unit list is comma-separated:

```ebnf
source-unit-id-list = unit-id { "," unit-id } ;
```

Source unit list rules:

```text
trim each item
reject empty items
reject duplicate items
each item must be a valid UnitId
each item must be a declared UnitId
```

Command effects:

```text
unit:<unit-id>
  require valid UnitId
  otherwise Error: invalid unit name.
  Units = Units ∪ { unit-id }
```

```text
set:<variable-id>:<value-formula>
  require valid VariableId
  otherwise Error: invalid variable name.
  evaluate value-formula in value context
  Variables[variable-id] = evaluated Value
```

```text
relate:<target-unit-id>:<source-unit-id-list>:<relationship-formula>
  require target-unit-id is a valid UnitId
  otherwise Error: invalid unit name.
  target-unit-id does not need to already be declared
  require valid source unit list
  require target not in source unit list
  evaluate relationship-formula in relationship context
  require result Value(factor, basis) to form a valid UnitRelationship
  Units = Units ∪ { target-unit-id }
  Relationships[target-unit-id] = UnitRelationship(target-unit-id, factor, basis)
```

```text
evaluate:<value-formula>[:<output-unit-formula>]
  if output-unit-formula is present:
    evaluate output-unit-formula in output-unit context

  evaluate value-formula in value context

  if output-unit-formula is present:
    convert source magnitude from source unit to target unit
    print "<convertedMagnitude> <serialize(targetUnit)>"

  if output-unit-formula is omitted:
    print "<sourceMagnitude> <serialize(sourceUnit)>"
```

A successful `relate` command replaces any existing relationship for the target unit.

A successful `relate` command may create a cyclic relationship graph. Cycles are not rejected at relation-definition time.

Successful `unit`, `set`, and `relate` commands print no output.

A recoverable error does not terminate the CLI.

---

## 4. Formula Syntax

Formula parsing must behave according to the grammar, precedence, and associativity rules in this section.

There are two formula grammars:

```text
value-formula
relationship-formula
```

### 4.1 AST

AST:

```text
Expr =
    ValueLiteral(magnitude, unit)
  | Identifier(name)
  | UnaryOp(op, operand)
  | BinaryOp(op, left, right)
```

---

## 4.2 Value Literals

Value literals:

```ebnf
value-literal = number [ unit-section ] ;
```

If a number has no parsed unit section, it is scalar:

```text
1   => ValueLiteral(1, {})
2.5 => ValueLiteral(2.5, {})
```

If a unit section is present:

```text
3 m      => ValueLiteral(3, { m: 1 })
10 m/s   => ValueLiteral(10, { m: 1, s: -1 })
4 kg*m^2 => ValueLiteral(4, { kg: 1, m: 2 })
```

Whitespace is allowed between a number and its unit section. The unit section attaches to the immediately preceding number.

Unit-section attachment is attempted immediately after a `NUMBER` token.

If the token immediately after a `NUMBER` begins a valid unit section, the parser consumes the longest valid unit section before normal binary formula parsing resumes.

Once unit-section parsing begins, any immediately following `*` or `/` is considered part of the unit section. If such an operator is not followed by a valid unit factor, the formula is invalid.

There is no implicit multiplication between formula expressions.

Examples:

```text
2 m
  parses as ValueLiteral(2, m)

2 m/s
  parses as ValueLiteral(2, m/s)

2 m / s
  parses as ValueLiteral(2, m/s)

2 m * s
  parses as ValueLiteral(2, m*s)

2 m + 3
  parses as ValueLiteral(2, m) + ValueLiteral(3, 1)

2 m / s + 1
  parses as ValueLiteral(2, m/s) + ValueLiteral(1, 1)

2 m^2^3
  is invalid because m^2 is a complete unit factor and the remaining ^3 cannot be parsed as a valid formula continuation

2 m^ -1
  parses as ValueLiteral(2, m^-1)

2 (m)
  parses as ValueLiteral(2, m)

2 (m/s)^2
  parses as ValueLiteral(2, m^2/s^2)

2 m x
  is invalid

2 X
  is invalid

2 (X + 1)
  is invalid

2 * X
  is valid

2 * (X + 1)
  is valid
```

---

## 4.3 Value Formulas

Value formulas are used by:

```text
set:<variable-id>:<value-formula>
evaluate:<value-formula>[:<output-unit-formula>]
```

Value formulas support:

```text
value literals
identifiers
unary +
unary -
binary +
binary -
binary *
binary /
binary ^
parentheses: (expr)
prefix log operator: [expr
prefix exp operator: ]expr
```

`[` and `]` are independent prefix unary operators.

Prefix `[` computes natural logarithm.

Prefix `]` computes exponential.

Precedence, highest to lowest:

| Precedence | Syntax                                       | Associativity |
| ---------: | -------------------------------------------- | ------------- |
|          6 | `(expr)`                                     | n/a           |
|          5 | value-literal unit attachment                | left          |
|          4 | prefix `[`, prefix `]`, unary `+`, unary `-` | right         |
|          3 | `^`                                          | right         |
|          2 | `*`, `/`                                     | left          |
|          1 | `+`, `-`                                     | left          |

Because unary operators have higher precedence than `^`:

```text
-2^2
```

parses as:

```text
(-2)^2
```

To express the negation of a power, use parentheses:

```text
-(2^2)
```

---

## 4.4 Relationship Formulas

Relationship formulas are used by:

```text
relate:<target-unit-id>:<source-unit-id-list>:<relationship-formula>
```

Relationship formulas support:

```text
value literals
identifiers
unary +
unary -
binary *
binary /
binary ^
parentheses: (expr)
```

Relationship formulas do not support:

```text
binary +
binary -
prefix log [
prefix exp ]
```

Any use of those operators in a relationship formula reports:

```text
Error: invalid formula.
```

This means the following is invalid:

```text
relate:m:m:m+m
```

---

## 5. Unit Syntax

Unit syntax is used by:

```text
value-literal unit sections
output-unit formulas
unit structure inside relationship validation
```

Unit expressions use:

```ebnf
unit-expression = unit-product ;

unit-product =
    unit-power { ( "*" | "/" ) unit-power } ;

unit-power =
    unit-primary [ "^" integer ] ;

unit-primary =
    unit-id
  | "1"
  | "(" unit-expression ")" ;
```

Rules:

```text
unit-id must resolve in the active unit context
^ accepts only integer exponents
+ and - are accepted only as signs in integer exponents
```

Unit sections in value literals use:

```ebnf
unit-section = unit-factor { ( "*" | "/" ) unit-factor } ;

unit-factor =
    unit-id [ "^" integer ]
  | "(" unit-section ")" [ "^" integer ] ;
```

Output unit formulas use:

```ebnf
output-unit-formula = unit-expression ;
```

An output-unit formula denotes only a `UnitExpr`.

It does not contain a numeric magnitude.

The result of an output-unit formula is the requested target `UnitExpr`.

Invalid output unit expressions report:

```text
Error: invalid output unit.
```

A token such as `m_s` is a single `UnitId`, not an implicit product.

Compound unit expressions require explicit `*` or `/`.

Examples:

```text
m_s     => unit identifier `m_s`
m/s     => unit `m` divided by unit `s`
m_s/s   => unit `m_s` divided by unit `s`
```

---

## 6. Evaluation Contexts

## 6.1 Value Context

Used by `set` and the first field of `evaluate`.

The variable and unit namespaces are lexically separate.

Identifier resolution:

```text
if identifier matches VariableId:
  if identifier exists in Variables:
    resolve to Variables[identifier]
  else:
    Error: unknown variable <identifier>.

else if identifier matches UnitId:
  if identifier exists in Units:
    resolve to Value(1, { identifier: 1 })
  else:
    Error: unknown unit <identifier>.

else:
  Error: invalid formula.
```

---

## 6.2 Relationship Context

Used by `relate`.

Relationship formulas are restricted formulas. They support:

```text
value literals
identifiers
unary +
unary -
binary *
binary /
binary ^
parentheses
```

They do not support:

```text
binary +
binary -
prefix log [
prefix exp ]
```

Identifier resolution:

```text
if identifier matches UnitId and appears in source-unit-id-list:
  resolve to Value(1, { identifier: 1 })
else:
  Error: unknown unit <identifier>.
```

Existing variables are ignored.

Existing units not present in `source-unit-id-list` are ignored.

Existing relationships are not applied while evaluating the relationship formula.

Unit names inside value-literal unit sections in a relationship formula are resolved only against the `source-unit-id-list`.

The evaluated relationship formula must produce:

```text
Value(factor, basis)
```

with:

```text
factor finite
factor != 0
basis contains only units from source-unit-id-list
```

The target unit may not appear in its own relationship formula because the target unit is forbidden from appearing in the source unit list, and relationship-context identifier resolution only resolves units from the source unit list.

---

## 6.3 Output-Unit Context

Used by the second field of `evaluate`, when present.

Identifier resolution:

```text
if identifier matches UnitId and exists in Units:
  resolve to unit identifier in a UnitExpr
else:
  Error: unknown unit <identifier>.
```

Output-unit formulas are parsed using the unit-expression grammar, not the value-formula grammar.

---

## 7. Evaluation Semantics

## 7.1 Value Literal

```text
ValueLiteral(n, U) => Value(n, U)
```

## 7.2 Unit Identifier

```text
u => Value(1, { u: 1 })
```

## 7.3 Variable Identifier

```text
X => Variables[X]
```

## 7.4 Unary Arithmetic

```text
+Value(a, U) = Value(a, U)
-Value(a, U) = Value(-a, U)
```

---

## 7.5 Value-Mode Operator Categories

In value context, binary operators behave as follows.

Unit-combining operators:

```text
*
/
```

These operators do not require scalar operands and do not require compatible units.

They combine `UnitExpr` values algebraically.

Unit-unifying operators:

```text
+
-
```

These operators do not require scalar operands, but they do require operands to represent the same physical dimension.

Before evaluating the operator, the operands are unified by conversion.

Scalar-required operators:

```text
^
```

The exponent operand must be scalar.

The base operand may have any unit.

---

## 7.6 Unit Unification

Some value-mode operators require their operands to represent the same physical dimension.

To unify two operands:

```text
left  = Value(a, U)
right = Value(b, V)
```

Attempt conversions in this order:

```text
1. If V can be converted to U:
     right' = Value(convert(b, from = V, to = U), U)
     result unit = U

2. Else if U can be converted to V:
     left' = Value(convert(a, from = U, to = V), V)
     result unit = V

3. Else:
     Error: cannot convert <V> to <U>.
```

The operator is then evaluated using the converted operands.

If `U == V`, no conversion is necessary and the result unit is `U`.

---

## 7.7 Multiplication

```text
Value(a, U) * Value(b, V)
  = Value(a * b, multiply(U, V))
```

---

## 7.8 Division

```text
Value(a, U) / Value(b, V)
```

If `b == 0`:

```text
Error: division by zero.
```

Otherwise:

```text
Value(a, U) / Value(b, V)
  = Value(a / b, divide(U, V))
```

---

## 7.9 Power

```text
Value(a, U) ^ Value(b, V)
```

Requires `V == {}`.

If exponent is not scalar:

```text
Error: exponent must be scalar.
```

Otherwise:

```text
Value(a^b, power(U, b))
```

---

## 7.10 Addition

```text
Value(a, U) + Value(b, V)
```

In value context, first unify the operands.

After unification:

```text
Value(a', W) + Value(b', W)
  = Value(a' + b', W)
```

---

## 7.11 Subtraction

```text
Value(a, U) - Value(b, V)
```

In value context, first unify the operands.

After unification:

```text
Value(a', W) - Value(b', W)
  = Value(a' - b', W)
```

---

## 7.12 Log Prefix Operator

```text
[Value(a, U)
```

Requires:

```text
U == {}
a > 0
```

Result:

```text
Value(log(a), {})
```

Errors:

```text
Error: log argument must be scalar.
Error: log argument must be positive.
```

---

## 7.13 Exp Prefix Operator

```text
]Value(a, U)
```

Requires `U == {}`.

Result:

```text
Value(exp(a), {})
```

Error:

```text
Error: exp argument must be scalar.
```

---

## 7.14 Numeric Results

All numeric results must be finite and real.

A non-finite result reports:

```text
Error: numeric result is not finite.
```

A non-real result reports:

```text
Error: numeric result is not real.
```

Power over negative bases, fractional exponents, overflow, underflow, and implementation-specific real numeric edge cases are otherwise intentionally underspecified, except that any produced result must be finite and real.

---

# 8. Unit Conversion

A unit relationship:

```text
UnitRelationship {
  target: UnitId
  factor: Real
  basis: UnitExpr
}
```

means:

```text
1 target = factor basis
```

---

## 8.1 Relationship as a Conversion Rule

Each relationship defines implicit conversion applications.

The forward direction is:

```text
target -> basis
scale factor = factor
```

Meaning:

```text
x target = x * factor basis
```

The reverse direction is:

```text
basis -> target
scale factor = 1 / factor
```

Meaning:

```text
x basis = x / factor target
```

Relationship applications also apply to powers of units and composite unit expressions.

---

## 8.2 Applying a Relationship: Forward Direction

Given relationship:

```text
1 target = factor basis
```

The forward application may be applied to a current `UnitExpr` `U` when `U` contains `target` with nonzero exponent `e`.

The application replaces:

```text
target^e
```

with:

```text
basis^e
```

The resulting unit expression is normalized.

The numeric magnitude is multiplied by:

```text
factor^e
```

Example:

```text
relate:cm:m:0.01 m
```

means:

```text
1 cm = 0.01 m
```

Therefore:

```text
cm   -> m      scale = 0.01
cm^2 -> m^2    scale = 0.01^2
1/cm -> 1/m    scale = 0.01^-1
```

---

## 8.3 Applying a Relationship: Reverse Direction

Given relationship:

```text
1 target = factor basis
```

The reverse application attempts to replace an occurrence of `basis^e` with `target^e`.

The candidate exponent `e` is determined from the current `UnitExpr` `U`.

For every unit `x` in `basis`, let:

```text
r[x] = U[x] / basis[x]
```

using `U[x] = 0` when `x` is absent.

Reverse application is possible only if all nonzero `r[x]` values have the same sign.

If reverse application is possible, the chosen exponent `e` is the nonzero value with that sign and the smallest absolute magnitude among the ratios:

```text
abs(e) = min(abs(r[x])) for x in basis
```

with the shared sign of the nonzero ratios.

Equivalently, reverse application replaces the largest whole proportional occurrence of `basis` that is present in `U`.

The application subtracts:

```text
basis * e
```

from `U`, adds:

```text
target: e
```

and normalizes the resulting `UnitExpr`.

The numeric magnitude is multiplied by:

```text
factor^(-e)
```

Example:

```text
relate:n:kg,m,s:kg*m/s^2
```

means:

```text
1 n = 1 kg*m/s^2
```

Therefore:

```text
kg*m/s^2        -> n        scale = 1
kg^2*m^2/s^4    -> n^2      scale = 1
kg*m^2/s^2      -> m*n      scale = 1
kg*m/s^3        -> n/s      scale = 1
s^2/(kg*m)      -> 1/n      scale = 1
```

Example with a non-1 factor:

```text
relate:cm:m:0.01 m
```

means:

```text
1 cm = 0.01 m
```

Therefore:

```text
m    -> cm      scale = 100
m^2  -> cm^2    scale = 100^2
1/m  -> 1/cm    scale = 100^-1
```

---

## 8.4 Conversion Search

To convert a value from source `UnitExpr` `A` to target `UnitExpr` `B`, the implementation searches for a finite sequence of relationship applications that transforms `A` into `B`.

Each relationship application may be used in either the forward or reverse direction.

The numeric magnitude is multiplied by the scale factor of each applied relationship.

If a conversion sequence is found:

```text
value_B = value_A * product(applied scale factors)
```

If no conversion sequence is found:

```text
Error: cannot convert <A> to <B>.
```

`<A>` and `<B>` use normalized unit serialization.

If `A == B`, conversion succeeds immediately with scale factor `1`.

---

## 8.5 Shortest-Path Conversion Rule

Conversion search must return a shortest path.

A path length is the number of relationship applications in the conversion sequence.

The chosen conversion path must satisfy:

```text
1. It reaches the requested target UnitExpr.
2. It has the minimum possible number of relationship applications.
3. Among all minimum-length paths, it is the first path in alphabetical order.
```

Alphabetical tie-breaking is defined over the sequence of serialized intermediate `UnitExpr` states produced by the path.

For a path:

```text
A -> U1 -> U2 -> ... -> B
```

its alphabetical key is:

```text
serialize(U1), serialize(U2), ..., serialize(B)
```

Paths are compared lexicographically by this sequence of strings.

The implementation must choose the lexicographically smallest key among all shortest paths.

A breadth-first search that expands next states in ascending order of serialized `UnitExpr` satisfies this rule.

When multiple relationship applications produce the same next `UnitExpr`, their ordering does not matter, provided the resulting magnitude scale is the same. If multiple applications produce the same next `UnitExpr` with different numeric scales, the implementation must choose the application whose relationship target `UnitId` is alphabetically first. If still tied, forward application is ordered before reverse application.

---

## 8.6 Visited States

During one conversion evaluation, the conversion search tracks visited `UnitExpr` states.

The initial source `UnitExpr` is marked visited.

If applying a relationship would produce a `UnitExpr` that has already been visited in the current conversion search, that application is skipped.

The search must not revisit a previously visited `UnitExpr` in the same conversion evaluation.

Encountering a previously visited `UnitExpr` does not itself produce an error.

If all reachable unvisited states are exhausted without reaching the target `UnitExpr`, report:

```text
Error: cannot convert <source-unit> to <target-unit>.
```

---

## 8.7 Cycles

Relationship cycles are allowed.

Cycles are not rejected when defining relationships.

A conversion search must avoid infinite search by using visited `UnitExpr` states as described above.

This relationship graph is allowed:

```text
unit:m
unit:cm
relate:cm:m:0.01 m
relate:m:cm:100 cm
```

A cycle is not, by itself, an invalid relationship.

---

## 8.8 Shortest-Path Example with Inconsistent Cycle

Given:

```text
relate:cm:m:0.01 m
relate:m:cm:101 cm
evaluate:1 m:cm
```

The target is:

```text
cm
```

The source is:

```text
m
```

The relationship:

```text
1 cm = 0.01 m
```

provides a reverse application:

```text
m -> cm
scale = 100
```

This reaches the target in one relationship application.

Therefore conversion succeeds immediately with the shortest path:

```text
m -> cm
```

and produces:

```text
100 cm
```

The search does not continue through longer cyclic paths after a shortest target path has been found.

---

## 8.9 Invalid Relationships During Conversion

```text
Error: invalid relationship.
```

is reported when:

```text
a stored relationship has a non-finite factor
a stored relationship has factor == 0
a stored relationship has a non-normalized basis
applying a relationship would require a non-real numeric operation
applying a relationship would produce a non-finite numeric scale
```

Do not use:

```text
Error: invalid relationship.
```

merely because a relationship graph contains a cycle.

---

## 8.10 Convertibility

Two units are convertible when conversion search can find a finite sequence of relationship applications from the source `UnitExpr` to the target `UnitExpr`.

Conversion failures must use:

```text
Error: cannot convert <source-unit> to <target-unit>.
```

---

# 9. Serialization

Unit serialization:

```text
{}       => 1
{m: 1}   => m
{m: 1, s: -1} => m/s
{kg: 1, m: 1, s: -2} => kg*m/s^2
{m: 2}   => m^2
{s: -1}  => 1/s
{m: 0.5} => m^0.5
```

Rules:

```text
positive exponents appear in numerator
negative exponents appear in denominator
identifiers are sorted lexicographically within numerator and denominator
exponent 1 is omitted
other exponents use "^"
```

If all exponents are negative, the numerator is serialized as:

```text
1
```

Magnitude serialization must be deterministic, finite, and parseable by the number grammar.

If `evaluate` omits the output unit, the value is printed using the unit produced by formula evaluation.

If the value is scalar, the serialized unit is:

```text
1
```

Examples:

```text
evaluate:2 + 3
```

prints:

```text
5 1
```

and:

```text
evaluate:2 m/s
```

prints a value equivalent to:

```text
2 m/s
```

---

# 10. Errors

All errors are printed as one line beginning with:

```text
Error:
```

Required errors:

```text
Error: unknown command.
Error: invalid command syntax.
Error: invalid formula.
Error: invalid output unit.
Error: invalid unit name.
Error: invalid variable name.
Error: invalid unit list.
Error: unknown variable <name>.
Error: unknown unit <name>.
Error: cannot convert <source-unit> to <target-unit>.
Error: exponent must be scalar.
Error: log argument must be scalar.
Error: log argument must be positive.
Error: exp argument must be scalar.
Error: division by zero.
Error: invalid relationship.
Error: numeric result is not finite.
Error: numeric result is not real.
```

Conversion failures must use:

```text
Error: cannot convert <source-unit> to <target-unit>.
```

For `evaluate` commands, if an `output-unit-formula` is present, it is parsed and evaluated before the `value-formula`.

Therefore errors in the `output-unit-formula` take precedence over errors in the `value-formula`.

If `evaluate` has no `output-unit-formula`, no conversion is attempted.

Except where this specification explicitly defines error precedence, if multiple errors are possible, any applicable required error may be reported.

A recoverable error does not terminate the CLI.

A failed command leaves the environment unchanged.
