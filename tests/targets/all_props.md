# All Test Proposals

Deduplicated proposal set for `targets/all.md`. Proposals were kept when they provide target coverage not otherwise covered by the remaining set; redundant duplicates were removed.

Each transcript starts from a fresh empty session unless a proposal says otherwise. Successful evaluation lines should be checked with the harness parsers and normal numeric tolerance rather than requiring a particular magnitude spelling.

Proposal count: 140 kept after review integration.

## Session, Commands, Identifiers, And Declarations

### AURORA-001 - Same-line command-looking text is one command

Purpose: Prove that command-looking text after a supported command prefix on
the same input line is part of that single command payload, not a second
command.

Targets: `all.md` Session/Transcript line 9; `SPEC.md` command reader line 205.

Transcript:

```text
unit:m evaluate:1
```

Expected: exact emitted lines:

```text
Error: invalid unit name.
```

### AURORA-002 - Empty lines are ignored and declarations are silent

Purpose: Check that empty command lines emit nothing, successful `unit` emits no
line, and a later `evaluate` emits exactly one result line.

Targets: `all.md` Session/Transcript lines 10-12; `SPEC.md` lines 205 and 314.

Transcript commands:

```text
<empty line>
unit:m
<empty line>
evaluate:1 m
<empty line>
```

Expected: exactly one emitted line. Assert it as one evaluation with magnitude
`1` and unit `m`.

### AURORA-003 - Successful unit, set, and relate state flows through session

Purpose: Confirm that successful `unit`, `set`, and `relate` commands are
silent and that later commands observe their accumulated state.

Targets: `all.md` Session/Transcript lines 11, 12, and 15; Unit Declarations
lines 96, 100-103, and 112.

Transcript:

```text
unit:m
set:X:2 m
relate:cm:m:0.01 m
evaluate:m
evaluate:X:cm
```

Expected: exactly two emitted lines. Assert the first as magnitude `1`, unit
`m`; assert the second as magnitude `200`, unit `cm`.

### AURORA-005 - Command prefixes are case-sensitive

Purpose: Verify that differently cased supported prefixes are unknown commands,
then a correctly cased command still succeeds.

Targets: `all.md` Session/Transcript lines 18 and 19; Error Text line 390.

Transcript:

```text
Unit:m
EVALUATE:1
evaluate:1
```

Expected: three emitted lines. Assert exact first two errors:

```text
Error: unknown command.
Error: unknown command.
```

Assert the third line as an evaluation with magnitude `1` and unit `1`.

### AURORA-006 - Failed unit command does not partially declare a unit

Purpose: A malformed `unit:` payload containing an extra colon must not create
any partial unit name.

Targets: `all.md` Session/Transcript lines 21 and 22; Command Parsing lines 33
and 35; Unit Declarations line 99.

Transcript:

```text
unit:m:extra
evaluate:m
```

Expected: exact emitted lines:

```text
Error: invalid unit name.
Error: unknown unit m.
```

### AURORA-007 - Failed set command neither creates nor replaces variables

Purpose: Show that a failed `set` leaves existing variables intact and does not
create a new variable binding.

Targets: `all.md` Session/Transcript lines 21 and 23; Value Context line 232.

Transcript:

```text
set:X:2
set:X:unknown_unit
set:Y:unknown_unit
evaluate:X
evaluate:Y
```

Expected: four emitted lines. Assert exact first two errors:

```text
Error: unknown unit unknown_unit.
Error: unknown unit unknown_unit.
```

Assert the third line as an evaluation with magnitude `2` and unit `1`. Assert
the fourth line exactly:

```text
Error: unknown variable Y.
```

### AURORA-010 - Successful evaluate conversion does not mutate variables

Purpose: Converting a variable during `evaluate` must not rewrite the stored
variable unit or magnitude.

Targets: `all.md` Session/Transcript line 26; End-To-End line 415.

Transcript:

```text
unit:m
relate:cm:m:0.01 m
set:X:1 m
evaluate:X:cm
evaluate:X
```

Expected: two emitted lines. Assert the first as magnitude `100`, unit `cm`;
assert the second as magnitude `1`, unit `m`.

### AURORA-011 - UTF-8 and non-ASCII identifier-like input use normal errors

Purpose: For byte-oriented adapters, feed this transcript as UTF-8. Non-ASCII
identifier-like characters should be rejected by identifier/formula rules, and
valid ASCII commands in the same session should still be processed normally.

Targets: `all.md` Session/Transcript lines 16, 17, and 27.

Transcript:

```text
unit:méter
set:Å:1
evaluate:2 + 3
```

Expected: three emitted lines. Assert exact first two errors:

```text
Error: invalid unit name.
Error: invalid variable name.
```

Assert the third line as an evaluation with magnitude `5` and unit `1`.

#### Command Parsing and Field Splitting

### AURORA-012 - Command fields are trimmed before validation

Purpose: Leading and trailing spaces around fields should not affect command
validity or stored names.

Targets: `all.md` Command Parsing line 31; `SPEC.md` line 245.

Transcript:

```text
unit:  m
set:  X  :  2 m
relate:  cm  :  m  :  0.01 m
evaluate:  X  :  cm
```

Expected: exactly one emitted line. Assert it as an evaluation with magnitude
`200` and unit `cm`.

### AURORA-013 - Required fields are non-empty after trimming

Purpose: Empty required fields should be rejected as command syntax, even when
the line uses a known command prefix.

Targets: `all.md` Command Parsing lines 32, 34, 49, 50, and 51.

Transcript:

```text
unit:
unit:   
set:X:
evaluate:
evaluate:1:
unit:m
evaluate::m
```

Expected: exact emitted lines:

```text
Error: invalid command syntax.
Error: invalid command syntax.
Error: invalid command syntax.
Error: invalid command syntax.
Error: invalid command syntax.
Error: invalid command syntax.
```

### AURORA-015 - set splits once at the first colon

Purpose: Text after the first colon belongs to the value formula, so an
additional colon should be reported as an invalid formula rather than changing
the variable field.

Targets: `all.md` Command Parsing lines 36 and 40.

Transcript:

```text
set:X:1:2
evaluate:X
```

Expected: exact emitted lines:

```text
Error: invalid formula.
Error: unknown variable X.
```

### AURORA-016 - set rejects missing or empty required fields

Purpose: Cover supported-prefix syntax failures for `set`.

Targets: `all.md` Command Parsing lines 37, 38, and 39.

Transcript:

```text
set:X
set::1
set:X:
```

Expected: exact emitted lines:

```text
Error: invalid command syntax.
Error: invalid command syntax.
Error: invalid command syntax.
```

### AURORA-017 - relate splits twice from the left

Purpose: After the first two colons, the remaining suffix is the relationship
formula, so `1:extra` is parsed as that formula.

Targets: `all.md` Command Parsing lines 41 and 45.

Transcript:

```text
unit:a
relate:t:a:1:extra
evaluate:t
```

Expected: exact emitted lines:

```text
Error: invalid formula.
Error: unknown unit t.
```

### AURORA-018 - relate rejects missing target, source list, or formula

Purpose: Cover the required-field parsing failures for `relate`.

Targets: `all.md` Command Parsing lines 42, 43, and 44.

Transcript:

```text
relate::m:1 m
relate:t::1
relate:t:m:
relate:t:m
```

Expected: exact emitted lines:

```text
Error: invalid command syntax.
Error: invalid command syntax.
Error: invalid command syntax.
Error: invalid command syntax.
```

### AURORA-019 - evaluate without colon has no output-unit field

Purpose: A payload with no colon should evaluate the value formula directly and
must not attempt output-unit parsing or conversion.

Targets: `all.md` Command Parsing line 46; Error Text line 409.

Transcript:

```text
unit:m
evaluate:1 m
```

Expected: exactly one emitted line. Assert it as an evaluation with magnitude
`1` and unit `m`.

### AURORA-020 - evaluate splits at the last colon

Purpose: Distinguish last-colon splitting from first-colon splitting by making
the last field a valid output unit and the earlier colon invalid in the value
formula.

Targets: `all.md` Command Parsing lines 47 and 48.

Transcript:

```text
unit:m
evaluate:1:2:m
```

Expected: exact emitted lines:

```text
Error: invalid formula.
```

### AURORA-022 - Valid unit identifier forms

Purpose: Exercise the valid `UnitId` shapes: single lowercase, multi-letter
lowercase, and underscores after the first character.

Targets: `all.md` Identifier Rules lines 55, 56, and 57; `SPEC.md` lines
100-118.

Transcript:

```text
unit:m
unit:meter
unit:meters_per_second
evaluate:1 m
evaluate:1 meter
evaluate:1 meters_per_second
```

Expected: three emitted lines. Assert them as evaluations with magnitude `1`
and units `m`, `meter`, and `meters_per_second`, respectively.

### AURORA-023 - Invalid unit identifier forms

Purpose: Reject unit identifiers that start with underscore, contain digits, or
contain uppercase letters.

Targets: `all.md` Identifier Rules lines 58, 59, and 60; Unit Declarations line
99.

Transcript:

```text
unit:_m
unit:m2
unit:Meter
unit:METER
```

Expected: exact emitted lines:

```text
Error: invalid unit name.
Error: invalid unit name.
Error: invalid unit name.
Error: invalid unit name.
```

### AURORA-024 - Valid variable identifier forms

Purpose: Exercise the valid `VariableId` shapes: single uppercase, multi-letter
uppercase, and underscores after the first character.

Targets: `all.md` Identifier Rules lines 61, 62, and 63; `SPEC.md` lines
100-118.

Transcript:

```text
set:X:1
set:SPEED:2
set:SPEED_AVG:3
evaluate:X
evaluate:SPEED
evaluate:SPEED_AVG
```

Expected: three emitted lines. Assert them as evaluations with magnitudes `1`,
`2`, and `3`, each with unit `1`.

### AURORA-025 - Invalid variable identifier forms

Purpose: Reject variable identifiers that start with underscore, contain digits,
or contain lowercase letters.

Targets: `all.md` Identifier Rules lines 64, 65, and 66.

Transcript:

```text
set:_X:1
set:X2:1
set:Speed:1
set:speed:1
```

Expected: exact emitted lines:

```text
Error: invalid variable name.
Error: invalid variable name.
Error: invalid variable name.
Error: invalid variable name.
```

### AURORA-026 - Mixed-case and digit-containing formula identifiers are invalid

Purpose: Formula lexing should reject mixed-case and digit-containing identifier
tokens before name lookup.

Targets: `all.md` Identifier Rules line 67; Number/Token Lexing line 92.

Transcript:

```text
evaluate:Speed
evaluate:X2
evaluate:m2
```

Expected: exact emitted lines:

```text
Error: invalid formula.
Error: invalid formula.
Error: invalid formula.
```

### AURORA-027 - Lowercase and uppercase namespaces are distinct

Purpose: Lowercase identifiers resolve only as units and uppercase identifiers
resolve only as variables, even when the spellings differ only by case.

Targets: `all.md` Identifier Rules lines 68, 69, and 70.

Transcript:

```text
unit:x
set:X:7 x
evaluate:x
evaluate:X
```

Expected: two emitted lines. Assert the first as magnitude `1`, unit `x`; assert
the second as magnitude `7`, unit `x`.

### AURORA-032 - Malformed number tokens are rejected

Purpose: Reject a decimal point without following digits, exponent markers
without digits, and whitespace-split numeric text.

Targets: `all.md` Number/Token Lexing lines 82, 83, and 85.

Transcript:

```text
evaluate:1.
evaluate:1e
evaluate:1E+
evaluate:1 e3
```

Expected: exact emitted lines:

```text
Error: invalid formula.
Error: invalid formula.
Error: invalid formula.
Error: invalid formula.
```

### AURORA-033 - Non-finite numeric literal is rejected

Purpose: A numeric literal that the implementation's `Real` parser reports as
non-finite must not be accepted as a finite value.

Targets: `all.md` Number/Token Lexing line 84.

Implementation-owned transcript/setup:

```text
evaluate:<numeric-literal-that-parses-non-finite-for-this-Real>
```

Expected/assertion style: assert exactly one recoverable error line beginning
with `Error:` and no successful evaluation line. Do not require a particular
portable literal or exact error text for this case; the spec requires finite
number parsing but does not assign a separate exact parse-overflow error.

### AURORA-034 - Whitespace is ignored between unambiguous formula tokens

Purpose: Whitespace around operators and parentheses should not affect token
recognition.

Targets: `all.md` Number/Token Lexing line 86; `SPEC.md` line 176.

Transcript:

```text
evaluate:( 2 + 3 ) * 4
```

Expected: exactly one emitted line. Assert it as an evaluation with magnitude
`20` and unit `1`.

### AURORA-036 - Formula token surface and trailing input errors

Purpose: Cover valid value-formula token classes, then assert non-whitespace
trailing input and invalid characters are rejected.

Targets: `all.md` Number/Token Lexing lines 89, 91, and 92.

Transcript:

```text
set:X:2
evaluate:] [ (X + 1)
evaluate:X (2)
evaluate:2 @ 3
```

Expected: three emitted lines. Assert the first as a scalar evaluation with
magnitude `3` within normal numeric tolerance if the implementation evaluates
`exp(log(3))` directly. Assert the next two exactly:

```text
Error: invalid formula.
Error: invalid formula.
```

#### Unit Declarations and Source Unit Lists

### AURORA-037 - Unit declaration and redeclaration are silent and usable

Purpose: Declaring an already-declared unit should succeed without duplicate
observable output, and the unit should remain usable.

Targets: `all.md` Unit Declarations lines 96 and 97.

Transcript:

```text
unit:m
unit:m
evaluate:1 m
```

Expected: exactly one emitted line. Assert it as an evaluation with magnitude
`1` and unit `m`.

### AURORA-038 - Declared units do not imply conversion relationships

Purpose: Two declared units are not convertible unless a relationship is
defined.

Targets: `all.md` Unit Declarations line 98.

Transcript:

```text
unit:m
unit:s
evaluate:1 m:s
```

Expected: exact emitted lines:

```text
Error: cannot convert m to s.
```

### AURORA-041 - Multiple source unit list items are comma-separated and trimmed

Purpose: A source unit list can contain multiple declared units with whitespace
around the comma-separated items.

Targets: `all.md` Unit Declarations lines 104 and 105; `SPEC.md` lines
249-255.

Transcript:

```text
unit:m
unit:s
relate:n:  m , s  :m/s
evaluate:1 n:m/s
```

Expected: exactly one emitted line. Assert it as an evaluation with magnitude
`1` and unit `m/s`.

### AURORA-042 - Source unit list rejects missing and empty item forms

Purpose: A completely missing source-list field is command syntax, while
non-empty source-list fields that contain empty comma-separated items should
report the required source-list error.

Targets: `all.md` Command Parsing line 43; Unit Declarations lines 106, 107,
and 111.

Transcript:

```text
unit:m
unit:s
relate:t::1
relate:t: , :1 m
relate:t:m,,s:1 m
relate:t:,m:1 m
relate:t:m,:1 m
```

Expected: exact emitted lines:

```text
Error: invalid command syntax.
Error: invalid unit list.
Error: invalid unit list.
Error: invalid unit list.
Error: invalid unit list.
```

### AURORA-043 - Source unit list rejects duplicates, invalid names, and undeclared units

Purpose: Source unit list validation should reject duplicate entries, invalid
unit identifiers, and syntactically valid but undeclared units with the same
required error.

Targets: `all.md` Unit Declarations lines 108, 109, 110, and 111.

Transcript:

```text
unit:m
relate:t:m,m:1 m
relate:t:m,S:1 m
relate:t:m,unknown:1 m
```

Expected: exact emitted lines:

```text
Error: invalid unit list.
Error: invalid unit list.
Error: invalid unit list.
```

### AURORA-045 - Relationship target may not appear in its own source list

Purpose: Even if the target is already declared, listing it as a source unit
must be rejected.

Targets: `all.md` Unit Declarations line 113.

Transcript:

```text
unit:m
relate:m:m:1 m
evaluate:1 m
```

Expected: two emitted lines. Assert the first exactly:

```text
Error: invalid unit list.
```

Assert the second as an evaluation with magnitude `1` and unit `m`.

## Value Syntax, Formulas, And Output Units

### BRIAR-01: Scalar number literal forms

- Purpose: Verify scalar value literals for integer, decimal, leading-dot
  decimal, and signed scientific notation forms.
- Transcript commands:

```text
evaluate:2
evaluate:2.5
evaluate:.5
evaluate:1e+3
evaluate:1E-3
```

- Expected: five emitted evaluation lines with magnitudes `2`, `2.5`, `0.5`,
  `1000`, and `0.001`, each with unit `1`.
- Targets: Number and Token Lexing (`all.md:76-81`); Value Literals and Unit
  Syntax (`all.md:117`).

### BRIAR-02: Declared unit literals and adjacency tokenization

- Purpose: Verify that declared units attach to adjacent or whitespace-separated
  numbers equivalently, including a compound quotient.
- Transcript commands:

```text
unit:m
unit:s
evaluate:1m
evaluate:1 m
evaluate:1m/s
evaluate:1 m / s
```

- Expected: four emitted evaluation lines with magnitudes all `1`; units are
  `m`, `m`, `m/s`, and `m/s`.
- Targets: Number and Token Lexing (`all.md:87-88`); Value Literals and Unit
  Syntax (`all.md:118,122`).

### BRIAR-03: Scalar and unit addition fail in the required direction

- Purpose: Verify that `2 + 3 m` and `2 m + 3` parse as value-literal addition
  and report the specified failed conversion direction.
- Transcript commands:

```text
unit:m
evaluate:2 + 3 m
evaluate:2 m + 3
```

- Expected emitted lines:

```text
Error: cannot convert m to 1.
Error: cannot convert 1 to m.
```

- Targets: Value Literals and Unit Syntax (`all.md:119-120,124`); Arithmetic
  and Numeric Semantics (`all.md:248,256,258`).

### BRIAR-04: Longest unit-section consumption before formula continuation

- Purpose: Verify that value-literal unit sections consume quotient and product
  syntax before normal formula parsing resumes.
- Transcript commands:

```text
unit:m
unit:s
evaluate:2 m/s
evaluate:2 m * s
evaluate:2 m / s + 1
```

- Expected: first line magnitude `2`, unit `m/s`; second line magnitude `2`,
  unit `m*s`; third emitted line exactly:

```text
Error: cannot convert 1 to m/s.
```

- Targets: Value Literals and Unit Syntax (`all.md:121-123,125`); Serialization and
  Output (`all.md:371`).

### BRIAR-05: Unit-section operators require a following unit factor

- Purpose: Verify that `*` and `/` consumed by a value-literal unit section
  cannot fall back to binary formula operators when no valid unit factor follows.
- Transcript commands:

```text
unit:m
set:S:3
evaluate:2 m^2^3
evaluate:2 m *
evaluate:2 m * S
evaluate:2 m / + 1
```

- Expected emitted lines:

```text
Error: invalid formula.
Error: invalid formula.
Error: invalid formula.
Error: invalid formula.
```

- Targets: Value Literals and Unit Syntax (`all.md:126,128-130`); Value Formula
  Grammar and Precedence (`all.md:175`).

### BRIAR-06: Signed exponents, parenthesized unit sections, and attachment before power

- Purpose: Verify signed integer unit exponents, parenthesized unit sections,
  and that `2 m ^ 2` is a value literal `2 m^2` rather than a formula power.
- Transcript commands:

```text
unit:m
unit:s
evaluate:2 m^+1
evaluate:2 m^ -1
evaluate:2 (m/s)^2
evaluate:2 m ^ 2
```

- Expected: four emitted evaluation lines with `(2, m)`, `(2, 1/m)`,
  `(2, m^2/s^2)`, and `(2, m^2)`.
- Targets: Value Literals and Unit Syntax (`all.md:127,131,142,148`); Value
  Formula Grammar and Precedence (`all.md:163`).

### BRIAR-07: Scalar primary `1` is not a value-literal unit section

- Purpose: Verify that unit-section grammar for value literals does not accept
  scalar primary `1`, while parenthesized real units still work.
- Transcript commands:

```text
unit:m
evaluate:2 1
evaluate:2 (1)
evaluate:2 (m)
```

- Expected: first two emitted lines are exactly `Error: invalid formula.`; third
  line has magnitude `2` and unit `m`.
- Targets: Value Literals and Unit Syntax (`all.md:132-134,146`).

### BRIAR-08: No implicit multiplication with variables or parenthesized expressions

- Purpose: Verify that adjacent formula expressions are invalid and variables
  cannot appear inside value-literal unit sections.
- Transcript commands:

```text
unit:m
set:X:3 m
evaluate:2 X
evaluate:2 (X + 1 m)
evaluate:X (2)
```

- Expected emitted lines:

```text
Error: invalid formula.
Error: invalid formula.
Error: invalid formula.
```

- Targets: Value Literals and Unit Syntax (`all.md:135-138`); Value Formula
  Grammar and Precedence (`all.md:175`).

### BRIAR-09: Explicit multiplication with variables is valid

- Purpose: Verify that the same operands rejected by adjacency work when `*`
  and parentheses are used as formula syntax.
- Transcript commands:

```text
unit:m
set:X:3 m
evaluate:2 * X
evaluate:2 * (X + 1 m)
```

- Expected: two emitted evaluation lines with `(6, m)` and `(8, m)`.
- Targets: Value Literals and Unit Syntax (`all.md:139`); Value Formula Grammar
  and Precedence (`all.md:154,158`).

### BRIAR-10: Unit algebra normalizes repeated and cancelling units

- Purpose: Verify multiplication, division, exponent combination, cancellation,
  and deterministic serialization of numerator and denominator identifiers.
- Transcript commands:

```text
unit:m
unit:s
unit:kg
evaluate:2 m*m/s/s
evaluate:3 s/m/m
evaluate:4 kg*m/s^2
evaluate:5 m/m
evaluate:6/s
```

- Expected: five emitted evaluation lines with `(2, m^2/s^2)`, `(3, s/m^2)`,
  `(4, kg*m/s^2)`, `(5, 1)`, and `(6, 1/s)`.
- Targets: Value Literals and Unit Syntax (`all.md:140-144`); Serialization and
  Output (`all.md:364-373,378`).

### BRIAR-12: Unknown unit in value-literal unit section

- Purpose: Verify that an undeclared lowercase identifier following a number is
  reported as an unknown unit rather than a generic formula error.
- Transcript commands:

```text
evaluate:2 missing
```

- Expected emitted line:

```text
Error: unknown unit missing.
```

- Targets: Value Literals and Unit Syntax (`all.md:149`).

#### Value Formula Grammar and Precedence

### BRIAR-13: Value formulas resolve variables and unit identifiers

- Purpose: Verify value formulas support value literals, variable identifiers,
  unit identifiers, and addition of compatible unit-bearing values.
- Transcript commands:

```text
unit:m
set:X:4 m
evaluate:X
evaluate:m
evaluate:X + 2 m
evaluate:Y
evaluate:s
evaluate:Speed
```

- Expected: six emitted lines. The first three are evaluation lines with
  `(4, m)`, `(1, m)`, and `(6, m)`. The last three are exactly:

```text
Error: unknown variable Y.
Error: unknown unit s.
Error: invalid formula.
```

- Targets: Value Formula Grammar and Precedence (`all.md:153-155`); Value
  Context and Identifier Resolution (`all.md:221-227`).

### BRIAR-14: Parentheses override multiplication and power operands

- Purpose: Verify parenthesized expressions bind as operands for multiplication
  and power.
- Transcript commands:

```text
evaluate:2 * (3 + 4)
evaluate:(2 + 3) * 4
evaluate:(2 + 3)^2
evaluate:2^(1 + 2)
```

- Expected: four emitted evaluation lines with magnitudes `14`, `20`, `25`, and
  `8`, each with unit `1`.
- Targets: Value Formula Grammar and Precedence (`all.md:158,161`).

### BRIAR-15: Multiplication and division bind tighter than addition and subtraction

- Purpose: Verify ordinary binary precedence among `*`, `/`, `+`, and `-`.
- Transcript commands:

```text
evaluate:2 + 3 * 4
evaluate:20 - 6 / 3
evaluate:20 / 5 + 1
evaluate:18 - 2 * 3
```

- Expected: four emitted evaluation lines with magnitudes `14`, `18`, `5`, and
  `12`, each with unit `1`.
- Targets: Value Formula Grammar and Precedence (`all.md:164-166`).

### BRIAR-16: Binary associativity for power, division, multiplication, and subtraction

- Purpose: Verify `^` is right-associative while `*`, `/`, `+`, and `-` are
  left-associative.
- Transcript commands:

```text
evaluate:2^3^2
evaluate:1+2+3
evaluate:20/5/2
evaluate:10-3-2
evaluate:2*3/4
```

- Expected: five emitted evaluation lines with magnitudes `512`, `6`, `2`,
  `5`, and `1.5`, each with unit `1`.
- Targets: Value Formula Grammar and Precedence (`all.md:157,168-170`).

### BRIAR-17: Unary operators bind tighter than power and wrap unit literals

- Purpose: Verify the spec-specific parse of `-2^2`, parenthesized negation of
  a power, chained unary and prefix operators, and unit attachment in the
  presence of unary operators. The `-2 m^2^3` case distinguishes the required
  unit-attachment parse from a parser that treats the trailing power as a
  formula-level exponent after unary parsing.
- Transcript commands:

```text
unit:m
evaluate:-2^2
evaluate:-(2^2)
evaluate:+-+2
evaluate:-[2.718281828459045
evaluate:-2 m^2^3
evaluate:-2 m + 2 m
```

- Expected: six emitted lines. The first four are evaluation lines with
  `(4, 1)`, `(-4, 1)`, `(-2, 1)`, and `(-1, 1)`. The fifth is exactly
  `Error: invalid formula.`. The sixth is an evaluation line with `(0, m)`.
- Targets: Value Formula Grammar and Precedence (`all.md:156,162,171-173`);
  Arithmetic and Numeric Semantics (`all.md:239-240`).

### BRIAR-18: Prefix log and exp bind tighter than power

- Purpose: Verify prefix `[` and `]` are parsed before binary `^` in expressions
  where the alternate parse changes the numeric result.
- Transcript commands:

```text
evaluate:[2.718281828459045^2
evaluate:]2^0
evaluate:-2^2
```

- Expected: three emitted scalar evaluation lines with magnitudes `1`, `1`, and
  `4`, each with unit `1`.
- Targets: Value Formula Grammar and Precedence (`all.md:159-160,167`);
  Arithmetic and Numeric Semantics (`all.md:268`).

### BRIAR-20: Malformed value formulas report invalid formula

- Purpose: Verify malformed parentheses, missing operands, missing prefix
  operands, and leftover adjacent tokens all report the required formula error.
- Transcript commands:

```text
evaluate:(2+3
evaluate:2 *
evaluate:* 2
evaluate:[
evaluate:]
evaluate:2 3
```

- Expected emitted lines:

```text
Error: invalid formula.
Error: invalid formula.
Error: invalid formula.
Error: invalid formula.
Error: invalid formula.
Error: invalid formula.
```

- Targets: Value Formula Grammar and Precedence (`all.md:174-177`); Number and
  Token Lexing (`all.md:91`).

#### Log and Exp Semantics

### BRIAR-22: Log rejects unit-bearing and non-positive inputs

- Purpose: Verify required log errors for non-scalar, zero, and negative scalar
  arguments.
- Transcript commands:

```text
unit:m
evaluate:[1 m
evaluate:[0
evaluate:[-1
```

- Expected emitted lines:

```text
Error: log argument must be scalar.
Error: log argument must be positive.
Error: log argument must be positive.
```

- Targets: Arithmetic and Numeric Semantics (`all.md:262-265`); Error Text and
  Precedence (`all.md:401-402`).

### BRIAR-23: Exp rejects unit-bearing inputs

- Purpose: Verify required exp errors for unit-bearing value literals and unit
  identifiers.
- Transcript commands:

```text
unit:m
evaluate:]1 m
evaluate:]m
```

- Expected emitted lines:

```text
Error: exp argument must be scalar.
Error: exp argument must be scalar.
```

- Targets: Arithmetic and Numeric Semantics (`all.md:266-267`); Error Text and
  Precedence (`all.md:403`).

#### Output-Unit Formulas

### BRIAR-24: Output units accept unit-expression constructs and normalize target text

- Purpose: Verify output-unit formulas accept declared units, products,
  quotients, integer powers, parentheses, and scalar `1`.
- Transcript commands:

```text
unit:m
unit:s
unit:kg
evaluate:2 kg*m/s^2
evaluate:2 kg*m/s^2:kg*m/s^2
evaluate:4 m^2/s^2:(m/s)^2
evaluate:5 m/m:1
```

- Expected: four emitted evaluation lines with `(2, kg*m/s^2)`,
  `(2, kg*m/s^2)`, `(4, m^2/s^2)`, and `(5, 1)`.
- Targets: Output Unit Formulas (`all.md:205,213,216-217`); Serialization and
  Output (`all.md:382-383`).

### BRIAR-25: Output unit `1` requests scalar output

- Purpose: Verify scalar output succeeds for scalar values and fails for an
  unconvertible unit-bearing value.
- Transcript commands:

```text
unit:m
evaluate:2:1
evaluate:2 m:1
```

- Expected: first line has magnitude `2`, unit `1`; second emitted line exactly:

```text
Error: cannot convert m to 1.
```

- Targets: Output Unit Formulas (`all.md:213`); Unit Conversion Basics
  (`all.md:305-306`).

### BRIAR-26: Output-unit conversion prints the requested target unit

- Purpose: Verify an output-unit formula triggers conversion and serializes the
  requested target unit.
- Transcript commands:

```text
unit:m
relate:cm:m:0.01 m
evaluate:1 m:cm
evaluate:1 cm:m
evaluate:1 m:missing
```

- Expected: two emitted evaluation lines with `(100, cm)` and `(0.01, m)`,
  followed by exactly `Error: unknown unit missing.`.
- Targets: Output Unit Formulas (`all.md:208`); Serialization and Output
  (`all.md:383`); Unit Conversion Basics (`all.md:311,318`).

### BRIAR-27: Output units reject numeric magnitude syntax other than exact `1`

- Purpose: Verify output-unit formulas do not accept value-formula numeric
  magnitudes such as `2`, `1.0`, `.5`, or `1e0`.
- Transcript commands:

```text
evaluate:1:2
evaluate:1:1.0
evaluate:1:.5
evaluate:1:1e0
unit:m
evaluate:1:+m
evaluate:1:m-m
evaluate:1:[m
evaluate:1:]m
```

- Expected emitted lines:

```text
Error: invalid output unit.
Error: invalid output unit.
Error: invalid output unit.
Error: invalid output unit.
Error: invalid output unit.
Error: invalid output unit.
Error: invalid output unit.
Error: invalid output unit.
```

- Targets: Output Unit Formulas (`all.md:206-207,210`).

### BRIAR-29: Output-unit errors take precedence over value-formula errors

- Purpose: Verify the output-unit field is parsed and resolved before the value
  formula field in `evaluate`.
- Transcript commands:

```text
unit:m
evaluate:BAD +:missing
evaluate:BAD +:m^0.5
```

- Expected emitted lines:

```text
Error: unknown unit missing.
Error: invalid output unit.
```

- Targets: Output Unit Formulas (`all.md:209-212`); Error Text and Precedence
  (`all.md:408`).

### BRIAR-30: Compound output units require explicit separators and `m_s` is single

- Purpose: Verify `m_s` is one unit identifier, `m/s` is division, and adjacent
  output-unit identifiers without `*` or `/` are invalid.
- Transcript commands:

```text
unit:m
unit:s
unit:m_s
evaluate:1 m_s:m_s
evaluate:1 m/s:m/s
evaluate:1 m_s:m/s
evaluate:1 m:m s
```

- Expected: first two lines have `(1, m_s)` and `(1, m/s)`; third line is
  exactly `Error: cannot convert m_s to m/s.`; fourth line is exactly
  `Error: invalid output unit.`.
- Targets: Output Unit Formulas (`all.md:214-216`); Identifier Rules and
  Namespaces (`all.md:72`).

### BRIAR-31: Formula-produced fractional exponents serialize, but input unit syntax rejects them

- Purpose: Verify formula power can produce `m^0.5`, while value-literal unit
  sections and output-unit formulas reject non-integer exponent syntax.
- Transcript commands:

```text
unit:m
evaluate:(4 m)^0.5
evaluate:(4 m)^0.5
evaluate:1 m^0.5
evaluate:1 m:m^0.5
```

- Expected: first two lines both have magnitude `2` and unit `m^0.5`, and the
  raw serialized unit strings are identical. Third line exactly
  `Error: invalid formula.`; fourth line exactly `Error: invalid output unit.`.
- Targets: Arithmetic and Numeric Semantics (`all.md:246-247`); Serialization
  and Output (`all.md:374-377`); Output Unit Formulas (`all.md:210`).

## Value Context, Arithmetic, And Serialization

### 3. Variable Replacement and Snapshot Assignment

Purpose: Verify that `set` creates and replaces bindings, and that assigning one
variable from another stores a snapshot value rather than an alias.

Transcript commands:

```text
unit:m
set:A:1 m
set:B:A
set:A:2 m
evaluate:B
evaluate:A
```

Expected/assertion style:

- Exactly two emitted lines.
- Line 1 parses as magnitude `1`, unit `m`.
- Line 2 parses as magnitude `2`, unit `m`.

Targets: `all.md` Value Context and Identifier Resolution lines 221, 228-230,
235.

### 7. Multiplication and Division Combine Units Without Compatibility Checks

Purpose: Verify magnitude arithmetic and algebraic unit combination for `*` and
`/`, including that incompatible units are allowed for these operators.

Transcript commands:

```text
unit:m
unit:s
evaluate:(6 m) * (2 s)
evaluate:(6 m) / (2 s)
```

Expected/assertion style:

- Exactly two emitted lines.
- Line 1 parses as magnitude `12`, unit `m*s`.
- Line 2 parses as magnitude `3`, unit `m/s`.

Targets: `all.md` Arithmetic lines 241-242, 261; Serialization lines 365-368,
371, and 382.

### 8. Division by Zero Is the Required Error

Purpose: Verify division by zero is detected before any successful evaluation
line is emitted.

Transcript commands:

```text
unit:m
evaluate:(1 m) / 0
```

Expected emitted lines:

```text
Error: division by zero.
```

Targets: `all.md` Arithmetic line 243; Error Text line 404.

### 9. Power Requires Scalar Exponents

Purpose: Verify successful unit-bearing power with a scalar exponent and the
required error for a unit-bearing exponent.

Transcript commands:

```text
unit:m
evaluate:(2 m)^3
evaluate:(2 m)^(1 m)
```

Expected/assertion style:

- Exactly two emitted lines.
- Line 1 parses as magnitude `8`, unit `m^3`.
- Line 2 is exactly `Error: exponent must be scalar.`

Targets: `all.md` Arithmetic lines 244-246; Error Text line 400;
Serialization lines 368-369.

### 11. Non-Finite Numeric Result Error

Purpose: Verify numeric-result validation reports the required error when an
otherwise parsed and evaluated expression produces a non-finite result.

Implementation-owned setup:

- Use a numeric-evaluation hook, a configured `Real` fixture, or an
  implementation-specific expression that is known for that implementation to
  produce a non-finite numeric result after successful formula parsing.
- Do not require `0^-1`; the spec leaves some real numeric edge cases
  implementation-specific.

Expected emitted line:

```text
Error: numeric result is not finite.
```

Targets: `all.md` Arithmetic line 269; Error Text line 406.

### 12. Non-Real Numeric Result Error

Purpose: Verify numeric-result validation reports the required error when an
otherwise parsed and evaluated expression produces a non-real result.

Implementation-owned setup:

- Use a numeric-evaluation hook, a configured `Real` fixture, or an
  implementation-specific expression that is known for that implementation to
  produce a non-real numeric result after successful formula parsing.
- Do not require `(-1)^0.5`; the spec leaves power over negative bases and
  fractional exponents implementation-specific except for final result
  validation.

Expected emitted line:

```text
Error: numeric result is not real.
```

Targets: `all.md` Arithmetic line 270; Error Text line 407.

### 19. Multiplication Binds Tighter Than Addition

Purpose: Verify arithmetic precedence and that parentheses override the default
binding.

Transcript commands:

```text
evaluate:2 + 3 * 4
evaluate:(2 + 3) * 4
```

Expected/assertion style:

- Exactly two emitted lines.
- Line 1 parses as magnitude `14`, unit `1`.
- Line 2 parses as magnitude `20`, unit `1`.

Targets: `all.md` Value Formula Grammar lines 161, 164-165; Arithmetic lines
241, 260.

### 20. Identical-Unit Addition and Subtraction Preserve Units

Purpose: Verify unit-unifying operators on identical unit expressions add or
subtract magnitudes and preserve that unit expression.

Transcript commands:

```text
unit:m
evaluate:2 m + 3 m
evaluate:5 m - 2 m
```

Expected/assertion style:

- Exactly two emitted lines.
- Line 1 parses as magnitude `5`, unit `m`.
- Line 2 parses as magnitude `3`, unit `m`.

Targets: `all.md` Arithmetic lines 248-249, 253-254.

### 22. Unit Unification Does Not Mutate Variable Operands

Purpose: Verify addition with conversion does not rewrite either variable's
stored value.

Transcript commands:

```text
unit:m
unit:cm
relate:cm:m:0.01 m
set:L:1 m
set:R:50 cm
evaluate:L + R
evaluate:L
evaluate:R
```

Expected/assertion style:

- Exactly three emitted lines.
- Line 1 parses as magnitude `1.5`, unit `m`.
- Line 2 parses as magnitude `1`, unit `m`.
- Line 3 parses as magnitude `50`, unit `cm`.

Targets: `all.md` Arithmetic lines 250 and 255; Value Context lines 221, 228,
233-234.

### 23. Incompatible Addition and Subtraction Report Right-to-Left Failure

Purpose: Verify incompatible unit-unifying operators report conversion failure
from the right operand unit to the left operand unit when both directions fail.

Transcript commands:

```text
unit:m
unit:s
evaluate:2 m + 3 s
evaluate:2 m - 3 s
```

Expected emitted lines:

```text
Error: cannot convert s to m.
Error: cannot convert s to m.
```

Targets: `all.md` Arithmetic lines 256-259; Error Text line 399.

### 27. Formula Result Unit Is Printed When Output Unit Is Omitted

Purpose: Verify `evaluate` without an output-unit field performs no conversion
and prints the formula-produced unit.

Transcript commands:

```text
unit:m
unit:s
evaluate:2 m/s
```

Expected/assertion style:

- Exactly one emitted line.
- The line parses as magnitude `2`, unit `m/s`.

Targets: `all.md` Value Literals lines 118, 122; Serialization lines 371, 382,
385; Error Text line 409.

### 32. Non-Integer Exponent Syntax Is Rejected in Input Unit Syntax

Purpose: Verify non-integer unit exponents are not accepted in value-literal
unit sections or output-unit formulas.

Transcript commands:

```text
unit:m
evaluate:2 m^0.5
evaluate:2:m^0.5
```

Expected emitted lines:

```text
Error: invalid formula.
Error: invalid output unit.
```

Targets: `all.md` Value Literals line 147; Serialization lines 376-377;
Error Text lines 392-393.

### 33. Conversion Failure Uses Normalized Source and Target Units

Purpose: Verify conversion errors serialize the source and target unit
expressions in normalized form.

Transcript commands:

```text
unit:kg
unit:m
unit:s
unit:a
evaluate:1 m*kg/s^2:a
```

Expected emitted lines:

```text
Error: cannot convert kg*m/s^2 to a.
```

Targets: `all.md` Unit Conversion Basics lines 303-304; Serialization lines
367, 372; Error Text line 399.

### 34. Full Workflow With Variables, Conversion, Arithmetic, and Serialization

Purpose: Verify a complete transcript combines declarations, variable reuse,
relationship conversion, arithmetic, output-unit conversion, and result
serialization.

Transcript commands:

```text
unit:m
unit:cm
unit:s
relate:cm:m:0.01 m
set:DISTANCE:1 m + 50 cm
set:TIME:2 s
evaluate:DISTANCE / TIME:cm/s
```

Expected/assertion style:

- Exactly one emitted line.
- The line parses as magnitude `75`, unit `cm/s`.

Targets: `all.md` Value Context lines 221, 226, 228, and 233-234; Arithmetic
lines 241-242 and 248; Serialization lines 371 and 383; End-To-End lines 414
and 419.

## Relationship Definition And Context

### 1. Undeclared `relate` target becomes a usable unit and conversion target

- Purpose: prove a valid relationship can introduce its target unit, store the
  conversion rule, and implement the `relate:cm:m:0.01 m` example.
- Transcript commands:

```text
unit:m
relate:cm:m:0.01 m
evaluate:1 cm:m
evaluate:1 m:cm
```

- Expected emitted lines or assertion style: exactly two evaluation lines; line
  1 is magnitude close to `0.01` with unit `m`, line 2 is magnitude close to
  `100` with unit `cm`.
- Target refs: `all.md:274`, `all.md:276`, `all.md:292`; `SPEC.md:283-292`,
  `SPEC.md:78-82`.

### 2. A declared target may later receive a relationship

- Purpose: prove `relate` is allowed for an already-declared target unit and
  still stores the relationship.
- Transcript commands:

```text
unit:m
unit:cm
relate:cm:m:0.01 m
evaluate:250 cm:m
```

- Expected emitted lines or assertion style: exactly one evaluation line with
  magnitude close to `2.5` and unit `m`.
- Target refs: `all.md:275`, `all.md:276`; `SPEC.md:286-292`.

### 4. A failed relationship replacement leaves the old relationship intact

- Purpose: prove invalid evaluated relationships do not replace existing stored
  relationships.
- Transcript commands:

```text
unit:m
relate:cm:m:0.01 m
evaluate:1 cm:m
relate:cm:m:0 m
evaluate:1 cm:m
```

- Expected emitted lines or assertion style: line 1 is an evaluation line with
  magnitude close to `0.01` and unit `m`; line 2 is exactly
  `Error: invalid relationship.`; line 3 is an evaluation line with magnitude
  close to `0.01` and unit `m`.
- Target refs: `all.md:280`, `all.md:284`, `all.md:291`; `SPEC.md:84-90`,
  `SPEC.md:290-292`.

### 5. Invalid relationship target names are rejected before relationship setup

- Purpose: prove relationship targets must be valid unit identifiers and report
  the required unit-name error.
- Transcript commands:

```text
unit:m
relate:CM:m:1 m
relate:_cm:m:1 m
relate:c2:m:1 m
```

- Expected emitted lines or assertion style: exactly three lines, each exactly
  `Error: invalid unit name.`.
- Target refs: `all.md:281-282`; `SPEC.md:283-285`,
  `SPEC.md:1447-1455`.

### 6. Source unit list validation rejects malformed, duplicate, undeclared, and self-source lists

- Purpose: prove invalid source lists are rejected without evaluating an
  otherwise valid scalar formula.
- Transcript commands:

```text
unit:m
unit:s
relate:a:m,,s:1
relate:b:m,m:1
relate:c:x:1
relate:d:M:1
relate:m:m:1
```

- Expected emitted lines or assertion style: exactly five lines, each exactly
  `Error: invalid unit list.`.
- Target refs: `all.md:111`, `all.md:296`; `SPEC.md:252-263`,
  `SPEC.md:287-288`.

### 7. Source unit list items are trimmed

- Purpose: prove whitespace around source-list items is ignored before
  validation and relationship-context resolution.
- Transcript commands:

```text
unit:m
relate:cm:  m  :0.01 m
evaluate:1 cm:m
```

- Expected emitted lines or assertion style: exactly one evaluation line with
  magnitude close to `0.01` and unit `m`.
- Target refs: `all.md:105`, `all.md:297`; `SPEC.md:255-263`.

### 8. Multi-source composite relationship matches the `n` example

- Purpose: prove relationship formulas can use multiple source identifiers,
  multiplication, division, integer power, and the `relate:n:kg,m,s:kg*m/s^2`
  example.
- Transcript commands:

```text
unit:kg
unit:m
unit:s
relate:n:kg,m,s:kg*m/s^2
evaluate:3 n:kg*m/s^2
evaluate:3 kg*m/s^2:n
```

- Expected emitted lines or assertion style: exactly two evaluation lines; line
  1 has magnitude close to `3` and unit `kg*m/s^2`, line 2 has magnitude close
  to `3` and unit `n`.
- Target refs: `all.md:182`, `all.md:184`, `all.md:293`;
  `SPEC.md:500-510`, `SPEC.md:671-674`.

### 9. Relationship formulas support value literals with unit sections

- Purpose: prove a value literal such as `2 m/s` can define a relationship
  factor and basis.
- Transcript commands:

```text
unit:m
unit:s
relate:speed_unit:m,s:2 m/s
evaluate:1 speed_unit:m/s
evaluate:2 m/s:speed_unit
```

- Expected emitted lines or assertion style: exactly two evaluation lines; line
  1 has magnitude close to `2` and unit `m/s`, line 2 has magnitude close to `1`
  and unit `speed_unit`.
- Target refs: `all.md:181`; `SPEC.md:500-510`,
  `SPEC.md:685-697`.

### 10. Relationship formula unary precedence is observable

- Purpose: prove unary operators bind tighter than power in relationship
  formulas, so `-2^2 * m` defines factor `4`, not `-4`.
- Transcript commands:

```text
unit:m
relate:u:m:-2^2 * m
relate:v:m:+2 * m
evaluate:1 u:m
evaluate:1 v:m
```

- Expected emitted lines or assertion style: exactly two evaluation lines. The
  first has magnitude close to `4` and unit `m`; the second has magnitude close
  to `2` and unit `m`.
- Target refs: `all.md:183`, `all.md:186`; `SPEC.md:500-510`,
  `SPEC.md:646-657`.

### 11. Relationship formula power is right-associative

- Purpose: prove `2^3^2 * m` is evaluated as `2^(3^2) * m`.
- Transcript commands:

```text
unit:m
relate:p:m:2^3^2 * m
evaluate:1 p:m
```

- Expected emitted lines or assertion style: exactly one evaluation line with
  magnitude close to `512` and unit `m`.
- Target refs: `all.md:184`, `all.md:187`; `SPEC.md:500-510`.

### 12. Relationship formula multiplication and division are left-associative

- Purpose: prove `8/4/2 * m` is evaluated as `((8 / 4) / 2) * m`.
- Transcript commands:

```text
unit:m
relate:q:m:8/4/2 * m
evaluate:1 q:m
```

- Expected emitted lines or assertion style: exactly one evaluation line with
  magnitude close to `1` and unit `m`.
- Target refs: `all.md:184`, `all.md:188`; `SPEC.md:500-510`.

### 13. Relationship formula parentheses override precedence

- Purpose: prove parentheses alter the factor in a relationship formula.
- Transcript commands:

```text
unit:m
relate:r:m:8/(4/2) * m
evaluate:1 r:m
```

- Expected emitted lines or assertion style: exactly one evaluation line with
  magnitude close to `4` and unit `m`.
- Target refs: `all.md:185`, `all.md:189`; `SPEC.md:500-510`.

### 14. Relationship formulas reject binary plus

- Purpose: prove relationship formulas do not allow binary `+`.
- Transcript commands:

```text
unit:m
relate:bad:m:m+m
```

- Expected emitted lines or assertion style: exactly one line,
  `Error: invalid formula.`.
- Target refs: `all.md:190`, `all.md:200`; `SPEC.md:513-525`.

### 15. Relationship formulas reject binary minus

- Purpose: prove relationship formulas do not allow binary `-`.
- Transcript commands:

```text
unit:m
relate:bad:m:m-m
```

- Expected emitted lines or assertion style: exactly one line,
  `Error: invalid formula.`.
- Target refs: `all.md:191`, `all.md:200`; `SPEC.md:513-525`.

### 16. Relationship formulas reject prefix log and prefix exp

- Purpose: prove relationship formulas do not allow prefix `[` or prefix `]`.
- Transcript commands:

```text
unit:m
relate:bad_log:m:[m
relate:bad_exp:m:]m
```

- Expected emitted lines or assertion style: exactly two lines, each exactly
  `Error: invalid formula.`.
- Target refs: `all.md:192-193`, `all.md:200`; `SPEC.md:513-525`,
  `SPEC.md:659-666`.

### 18. Relationship-context identifiers resolve only from the source list

- Purpose: prove a declared unit outside the source list is still unknown when
  used as a bare relationship-context identifier.
- Transcript commands:

```text
unit:m
unit:s
relate:u:m:s
```

- Expected emitted lines or assertion style: exactly one line,
  `Error: unknown unit s.`.
- Target refs: `all.md:194`, `all.md:196`, `all.md:201`;
  `SPEC.md:668-679`.

### 19. Existing variables are ignored in relationship context

- Purpose: prove an uppercase existing variable is not available to a
  relationship formula.
- Transcript commands:

```text
unit:m
set:S:7
relate:u:m:S
```

- Expected emitted lines or assertion style: exactly one line,
  `Error: unknown unit S.`.
- Target refs: `all.md:195`, `all.md:201`; `SPEC.md:668-678`.

### 20. Relationship value-literal unit sections resolve only from the source list

- Purpose: prove unit names inside relationship value-literal unit sections do
  not see declared units outside the source list.
- Transcript commands:

```text
unit:m
unit:s
relate:u:m:1 s
```

- Expected emitted lines or assertion style: exactly one line,
  `Error: unknown unit s.`.
- Target refs: `all.md:196`, `all.md:198`, `all.md:201`;
  `SPEC.md:679-683`.

### 21. Existing relationships are not applied while evaluating a relationship formula

- Purpose: prove a relationship formula using `cm` stores basis `cm`, rather
  than expanding `cm` through an existing relationship at definition time.
- Transcript commands:

```text
unit:m
relate:cm:m:0.01 m
relate:inch:cm:2.54 cm
relate:cm:m:0.02 m
evaluate:1 inch:cm
```

- Expected emitted lines or assertion style: exactly one evaluation line with
  magnitude close to `2.54` and unit `cm`. A result near `1.27 cm` would show
  that the old `cm -> m` conversion was incorrectly applied during
  `inch` definition.
- Target refs: `all.md:197`, `all.md:295`; `SPEC.md:681`,
  `SPEC.md:290-292`.

### 22. The relationship target is not resolvable from its own formula

- Purpose: prove the target unit cannot appear in its relationship formula
  unless it is illegally listed as a source.
- Transcript commands:

```text
unit:m
unit:s
relate:m:s:1 m
```

- Expected emitted lines or assertion style: exactly one line,
  `Error: unknown unit m.`.
- Target refs: `all.md:199`, `all.md:298`; `SPEC.md:699`.

### 23. A relationship basis may omit some listed source units

- Purpose: prove not every unit in the source list must appear in the evaluated
  basis.
- Transcript commands:

```text
unit:m
unit:s
relate:minute:m,s:60 s
evaluate:1 minute:s
```

- Expected emitted lines or assertion style: exactly one evaluation line with
  magnitude close to `60` and unit `s`.
- Target refs: `all.md:288`; `SPEC.md:694-696`.

### 25. A scalar-normalized basis is accepted

- Purpose: prove a relationship whose basis normalizes to scalar `1` is valid
  when the factor is finite and nonzero.
- Transcript commands:

```text
unit:m
relate:dozen:m:12 m/m
evaluate:2 dozen:1
```

- Expected emitted lines or assertion style: exactly one evaluation line with
  magnitude close to `24` and unit `1`.
- Target refs: `all.md:289`; `SPEC.md:84-90`, `SPEC.md:685-697`.

### 28. Negative finite relationship factors are valid and exponent signs matter

- Purpose: prove finite nonzero negative factors are valid and conversion uses
  `factor^e` for odd, even, and negative integer exponents.
- Transcript commands:

```text
unit:m
relate:neg:m:-2 m
evaluate:3 neg:m
evaluate:4 neg^2:m^2
evaluate:8 / neg:1/m
```

- Expected emitted lines or assertion style: exactly three evaluation lines; line
  1 has magnitude close to `-6` and unit `m`, line 2 has magnitude close to
  `16` and unit `m^2`, line 3 has magnitude close to `-4` and unit `1/m`.
- Target refs: `all.md:285`, `all.md:332`; `SPEC.md:84-90`.

### 30. Inspect valid stored relationships for key, target, factor, and basis invariants

- Purpose: inspect that every stored valid relationship is keyed by its target,
  has `target` equal to that key, has a finite nonzero factor, and stores a
  normalized basis.
- Transcript commands:

```text
unit:m
unit:s
relate:cm:m:0.01 m
relate:u:m,s:3 m*s/s
```

- Expected emitted lines or assertion style: exact emitted output is `[]`. Then
  inspect the implementation environment and assert:
  - the `Relationships` keys include `cm` and `u`;
  - `Relationships["cm"].target == "cm"` and `Relationships["u"].target == "u"`;
  - both factors are finite and nonzero;
  - `Relationships["u"].basis` is normalized to exactly `{m: 1}` with no `s: 0`
    entry.
- Target refs: `all.md:277-279`; `SPEC.md:68-95`.

### 32. Seeded conversion rejects a stored non-finite-factor relationship

- Purpose: prove conversion reports the required invalid-relationship error when
  a corrupted stored relationship has a non-finite factor.
- Seeded setup: create a session with units `bad` and `m`, and seed
  `Relationships["bad"] = UnitRelationship(target="bad", factor=Infinity, basis={m: 1})`
  or an implementation-equivalent non-finite real factor.
- Transcript commands:

```text
evaluate:1 bad:m
```

- Expected emitted lines or assertion style: exactly one line,
  `Error: invalid relationship.`.
- Target refs: `all.md:330`, `all.md:405`; `SPEC.md:1335-1349`,
  `SPEC.md:1447-1465`.

## Conversion Search And Relationship Application

### UF-EMBERLY-01: Forward relationship applications scale powers and reciprocals

Purpose: Verify that `relate:cm:m:0.01 m` applies in the forward direction,
replaces `cm^e` with `m^e`, and multiplies by `factor^e` for positive,
powered, and negative exponents.

Transcript commands:

```text
unit:m
relate:cm:m:0.01 m
evaluate:2 cm:m
evaluate:3 cm^2:m^2
evaluate:4/cm:1/m
```

Expected emitted lines / assertion style:

- Assert exactly three emitted lines.
- Parse as evaluation lines with default numeric tolerance:
  - `0.02 m`
  - `0.0003 m^2`
  - `400 1/m`

Targets: Unit Conversion Basics, all.md:309-313; SPEC.md forward application,
8.2.

### UF-EMBERLY-02: Reverse relationship applications scale powers and reciprocals

Purpose: Verify the reverse direction of the same centimeter relationship,
including `factor^-e` scaling.

Transcript commands:

```text
unit:m
relate:cm:m:0.01 m
evaluate:2 m:cm
evaluate:3 m^2:cm^2
evaluate:4/m:1/cm
```

Expected emitted lines / assertion style:

- Assert exactly three emitted lines.
- Parse as evaluation lines with default numeric tolerance:
  - `200 cm`
  - `30000 cm^2`
  - `0.04 1/cm`

Targets: Unit Conversion Basics, all.md:316-320; SPEC.md reverse application,
8.3.

### UF-EMBERLY-03: Composite reverse applications choose largest proportional occurrence

Purpose: Exercise reverse conversion from a composite basis to the target unit,
including exact, powered, partial, and reciprocal forms.

Transcript commands:

```text
unit:kg
unit:m
unit:s
relate:n:kg,m,s:kg*m/s^2
evaluate:2 kg*m/s^2:n
evaluate:3 kg^2*m^2/s^4:n^2
evaluate:5 kg*m^2/s^2:m*n
evaluate:7 s^2/(kg*m):1/n
```

Expected emitted lines / assertion style:

- Assert exactly four emitted lines.
- Parse as evaluation lines:
  - `2 n`
  - `3 n^2`
  - `5 m*n`
  - `7 1/n`

Targets: Unit Conversion Basics, all.md:321-324; SPEC.md reverse application
examples, 8.3.

### UF-EMBERLY-04: Reverse application ratio sign rule and absent-unit ratio zero

Purpose: Show that absent basis units count as ratio zero during partial
reverse replacement, while mixed-sign nonzero ratios reject reverse
replacement.

Transcript commands:

```text
unit:kg
unit:m
unit:s
relate:n:kg,m,s:kg*m/s^2
evaluate:8 kg/s^2:n/m
evaluate:1 kg*s^2:n/m
```

Expected emitted lines / assertion style:

- Assert exactly two emitted lines.
- First line parses as `8 n/m`.
- Second line is exactly `Error: cannot convert kg*s^2 to n/m.`

Targets: Unit Conversion Basics, all.md:325; Conversion Search, all.md:359;
conversion failure text, all.md:399; SPEC.md:1081-1175.

### UF-EMBERLY-07: Relationship formulas can store non-integer bases

Purpose: Prove that a relationship formula can produce a non-integer basis and
that later forward and reverse conversions use that stored basis.

Transcript commands:

```text
unit:m
relate:sqrt_m:m:2 * m^0.5
evaluate:9 sqrt_m^2:m
evaluate:16 m:sqrt_m^2
```

Expected emitted lines / assertion style:

- Assert exactly two emitted lines.
- Parse as evaluation lines:
  - `36 m`
  - `4 sqrt_m^2`

Targets: Relationship Definition and Validation, all.md:290; SPEC.md:849-855
and 1177-1199.

### UF-EMBERLY-10: Multi-step conversion can mix forward and reverse applications

Purpose: Confirm conversion search finds a finite sequence where the first
application is forward and the second is reverse.

Transcript commands:

```text
unit:b
relate:a:b:2 b
relate:c:b:3 b
evaluate:6 a:c
```

Expected emitted lines / assertion style:

- Assert one evaluation line with magnitude `4` and unit `c`.
- Reasoning: `6 a -> 12 b -> 4 c`.

Targets: Conversion Search, Cycles, and Tie-Breaking, all.md:336-337;
SPEC.md:1177-1199.

### UF-EMBERLY-11: Shortest path beats longer cyclic alternatives

Purpose: Build a cyclic graph with a direct one-step conversion and a longer
cycle, then verify the one-step path determines the result.

Transcript commands:

```text
unit:b
unit:q
relate:a:b:2 b
relate:c:a:3 a
relate:b:c:5 c
relate:p:q:7 q
evaluate:1 a:b
```

Expected emitted lines / assertion style:

- Assert one evaluation line with magnitude `2` and unit `b`.
- A longer cyclic route `a -> c -> b` exists but must not override the
  one-application `a -> b` path.
- The unrelated valid `p <-> q` relationship must not prevent the shortest
  conversion from succeeding.

Targets: Conversion Search, Cycles, and Tie-Breaking, all.md:338-340 and
346; SPEC.md:1203-1235 and 1261-1278.

### UF-EMBERLY-14: Cyclic graphs terminate with a reachable target

Purpose: Confirm relationship cycles are accepted and conversion search
terminates once the shortest reachable target path is found.

Transcript commands:

```text
unit:m
relate:cm:m:0.01 m
relate:m:cm:101 cm
evaluate:1 m:cm
```

Expected emitted lines / assertion style:

- Assert exactly one evaluation line with magnitude `100` and unit `cm`.
- Assert no error lines are emitted by either `relate` command.

Targets: Relationship Definition and Validation, all.md:294; Conversion
Search, Cycles, and Tie-Breaking, all.md:339, 346, 349, 351-352;
SPEC.md:1261-1278 and 1282-1331.

### UF-EMBERLY-15: Cyclic graphs terminate with cannot-convert when target is unreachable

Purpose: Verify visited-state handling prevents infinite search and reports
the normal conversion failure when a cycle cannot reach the requested unit.
Use the public transcript for termination/error behavior and an
implementation-owned conversion-search trace for the visited-state details.

Transcript commands:

```text
unit:m
unit:kg
relate:cm:m:0.01 m
relate:m:cm:100 cm
evaluate:1 cm:kg
```

Expected emitted lines / assertion style:

- Assert exactly one emitted line:
  - `Error: cannot convert cm to kg.`
- Run under the normal unit-test timeout.
- If the implementation exposes a conversion-search trace, assert that the
  initial source `cm` is marked visited before expansion, applications that
  would return to a visited `UnitExpr` are skipped, no serialized `UnitExpr` is
  expanded twice, and skipped visited states do not themselves emit errors.

Targets: Conversion Search, Cycles, and Tie-Breaking, all.md:342-350;
conversion failure text, all.md:399; SPEC.md:1241-1278.

### UF-EMBERLY-16: Exhausted conversion search uses normalized source and target serialization

Purpose: Check conversion failure text after unit-expression normalization.

Transcript commands:

```text
unit:m
unit:s
unit:kg
evaluate:1 s*m/m^2:kg
```

Expected emitted lines / assertion style:

- Assert exactly one emitted line:
  - `Error: cannot convert s/m to kg.`

Targets: Unit Conversion Basics, all.md:303-304; Serialization and Output,
all.md:367 and 372; Error Text and Precedence, all.md:399;
SPEC.md:1177-1199 and 1361-1369.

### UF-EMBERLY-19: Negative relationship factors fail on non-real fractional conversion

Purpose: A negative finite nonzero relationship factor is valid, but applying
it to a non-integer exponent can require a non-real numeric operation and must
report `Error: invalid relationship.`

Transcript commands:

```text
unit:m
relate:neg:m:-4 m
evaluate:(9 neg)^0.5 + (1 m)^0.5
```

Expected emitted lines / assertion style:

- Assert exactly one emitted line:
  - `Error: invalid relationship.`

Targets: Unit Conversion Basics, all.md:327; Error Text and Precedence,
all.md:405; SPEC.md:1335-1355.

### UF-EMBERLY-20: Relationship replacement changes later conversion results

Purpose: Confirm that replacing a stored relationship changes subsequent
conversion search output and does not leave stale conversion edges behind.

Transcript commands:

```text
unit:m
relate:cm:m:0.01 m
evaluate:1 m:cm
relate:cm:m:0.02 m
evaluate:1 m:cm
```

Expected emitted lines / assertion style:

- Assert exactly two evaluation lines:
  - first magnitude `100`, unit `cm`
  - second magnitude `50`, unit `cm`

Targets: Relationship Definition and Validation, all.md:280; Conversion
Search, Cycles, and Tie-Breaking, all.md:356; SPEC.md command effects and
8.4.

### UF-EMBERLY-21: Composite conversions chain across derived units

Purpose: Exercise conversion search across multiple composite relationships,
including reverse applications that normalize the result.

Transcript commands:

```text
unit:kg
unit:m
unit:s
relate:n:kg,m,s:kg*m/s^2
relate:j:n,m:n*m
evaluate:2 kg*m^2/s^2:j
```

Expected emitted lines / assertion style:

- Assert one evaluation line with magnitude `2` and unit `j`.

Targets: Conversion Search, Cycles, and Tie-Breaking, all.md:336 and 357;
Unit Conversion Basics, all.md:321 and 326; SPEC.md:1177-1199.

### UF-EMBERLY-22: Unit conversions work in denominators

Purpose: Verify conversion applications operate on denominator units and
normalize the requested reciprocal output unit.

Transcript commands:

```text
unit:s
relate:hz:s:1/s
evaluate:3 hz:1/s
evaluate:4/s:hz
```

Expected emitted lines / assertion style:

- Assert exactly two evaluation lines:
  - `3 1/s`
  - `4 hz`

Targets: Conversion Search, Cycles, and Tie-Breaking, all.md:358; Unit
Conversion Basics, all.md:309, 316, and 326; SPEC.md:1029-1175.

#### Optional Internal-State Proposals

These targets explicitly allow inspect/seed coverage. They should be used only
by implementation-owned conformance suites that can inject or observe internal
conversion state without changing the public transcript contract.

### UF-EMBERLY-I01: Stored relationship with zero factor fails during conversion

Purpose: Seed a stored relationship that violates the invariant
`factor != 0`, then verify conversion reports the required relationship error.

Setup and transcript:

- Seed internal state with declared units `bad` and `m`, and relationship
  `bad -> m` whose target is `bad`, factor is `0`, and basis is `{m: 1}`.
- Run:

```text
evaluate:1 bad:m
```

Expected emitted lines / assertion style:

- Assert exactly one emitted line:
  - `Error: invalid relationship.`

Targets: Unit Conversion Basics, all.md:329; Error Text and Precedence,
all.md:405; SPEC.md:1335-1355.

### UF-EMBERLY-I02: Stored relationship with non-normalized basis fails during conversion

Purpose: Seed a relationship whose basis contains canceling or repeated unit
entries that are not normalized and verify conversion reports the required
relationship error.

Setup and transcript:

- Seed internal state with declared units `bad` and `m`, and relationship
  target `bad`, finite nonzero factor `1`, and a deliberately non-normalized
  basis representation equivalent to `{m: 1, m: 0}` or duplicated `m` entries,
  depending on the implementation's internal representation.
- Run:

```text
evaluate:1 bad:m
```

Expected emitted lines / assertion style:

- Assert exactly one emitted line:
  - `Error: invalid relationship.`

Targets: Unit Conversion Basics, all.md:331; Error Text and Precedence,
all.md:405; SPEC.md:1335-1355.

## Error Text, Recovery, And Workflows

### FROST-001 - Scalar evaluation line shape

Purpose: Verify a successful scalar `evaluate` emits exactly one line in
`<magnitude> <serialized-unit>` form, with scalar unit serialized as `1`.

Transcript commands:

```text
evaluate:2 + 3
```

Expected assertion style: exactly one emitted line. Parse it as an evaluation
line; assert magnitude close to `5` and unit exactly `1`. Also assert the raw
line matches the harness evaluation-line parser, which requires one ASCII space
between magnitude and unit.

Target refs: `all.md:12`, `all.md:363`, `all.md:364`, `all.md:384`.

### FROST-014 - Empty output-unit field is invalid command syntax

Purpose: Verify `evaluate` rejects a present but empty output-unit field using
the required command-syntax error and then recovers.

Transcript commands:

```text
evaluate:1:
evaluate:1
```

Expected assertion style: exactly two emitted lines. First line exactly
`Error: invalid command syntax.`. Second line parses as magnitude close to `1`,
unit exactly `1`.

Target refs: `all.md:50`, `all.md:391`, `all.md:14`.

### FROST-017 - Name and list validation exact errors

Purpose: Verify invalid unit names, variable names, and source unit lists use the
exact required error strings.

Transcript commands:

```text
unit:M
set:x:1
unit:m
relate:cm:m,,s:1 m
```

Expected emitted lines:

```text
Error: invalid unit name.
Error: invalid variable name.
Error: invalid unit list.
```

Target refs: `all.md:99`, `all.md:111`, `all.md:231`, `all.md:394`,
`all.md:395`, `all.md:396`.

### FROST-025 - Multiple applicable value errors allow either required error

Purpose: Capture an intentionally ambiguous multi-error case outside explicit
precedence rules while still requiring exactly one applicable required error
line.

Transcript commands:

```text
evaluate:UNKNOWN + missing
evaluate:1
```

Expected assertion style: exactly two emitted lines. First line must be exactly
one of:

```text
Error: unknown variable UNKNOWN.
Error: unknown unit missing.
```

Second line parses as magnitude close to `1`, unit exactly `1`, proving
recovery after whichever applicable error was reported.

Target refs: `all.md:13`, `all.md:14`, `all.md:397`, `all.md:398`,
`all.md:410`.

#### Recovery and Environment Preservation

### FROST-034 - Inconsistent cycle chooses shortest one-step conversion

Purpose: Verify cycles are allowed, conversion search terminates, and a
one-step shortest path wins over a longer inconsistent cyclic path.

Transcript commands:

```text
unit:m
relate:cm:m:0.01 m
relate:m:cm:101 cm
evaluate:1 m:cm
```

Expected assertion style: exactly one evaluation line; magnitude close to `100`;
unit exactly `cm`.

Target refs: `all.md:348`, `all.md:351`, `all.md:352`, `all.md:421`.

## Supplemental Inspection And Edge Cases

### EXTRA-001: Inspect Formula Token Classes Including EOF

Purpose: Verify the formula lexer recognizes every token class named by the
spec, including the explicit end-of-input token.

Inspection input:

```text
] [ (X + 1) * 2 m/s^-3 - 4
```

Expected assertion style:

- Use an implementation-owned lexer/token inspection hook.
- Assert the token kind sequence is:
  `]`, `[`, `(`, `VARIABLE_IDENTIFIER`, `+`, `NUMBER`, `)`, `*`, `NUMBER`,
  `UNIT_IDENTIFIER`, `/`, `UNIT_IDENTIFIER`, `^`, `-`, `NUMBER`, `-`,
  `NUMBER`, `EOF`.
- Assert the identifier lexemes are `X`, `m`, and `s`, and the number lexemes
  are `1`, `2`, `3`, and `4`.
- Do not require this proposal for adapters that expose only transcript I/O.

Targets: `all.md` Number/Token Lexing line 90.

### EXTRA-002: Scalar `1` Is Accepted By Unit-Expression Syntax

Purpose: Verify `1` denotes the scalar unit expression in unit syntax where the
full unit-expression grammar is used.

Transcript commands:

```text
unit:m
evaluate:6 m/m:1
evaluate:7:(1)
```

Expected/assertion style:

- Exactly two emitted lines.
- Line 1 parses as magnitude `6`, unit `1`.
- Line 2 parses as magnitude `7`, unit `1`.

Targets: `all.md` Value Literals and Unit Syntax line 145.

### EXTRA-003: Addition Fallback Uses Left-To-Right Conversion After Right-To-Left Fails

Purpose: Verify the specified unit-unification fallback branch for addition.
With ordinary valid relationships, successful convertibility is typically
symmetric, so this is an implementation-owned unit-unification proposal rather
than a generic transcript test.

Inspection setup:

- Invoke the implementation's unit-unification or addition evaluator with
  `left = Value(1, a)` and `right = Value(2, b)`.
- Instrument or stub only the conversion dependency for this isolated test:
  converting `b -> a` returns cannot-convert, while converting `a -> b` returns
  magnitude `10`, unit `b`.

Expected assertion style:

- Assert conversion is attempted first from `b` to `a`.
- Assert conversion is then attempted from `a` to `b`.
- Assert the addition result is magnitude `12`, unit `b`.
- Do not apply this proposal to a black-box adapter unless it exposes an
  equivalent spec-level conversion-attempt trace.

Targets: `all.md` Arithmetic and Numeric Semantics line 251.

### EXTRA-004: Subtraction Uses The Same Unit-Unification Order As Addition

Purpose: Verify subtraction uses the same right-to-left-then-left-to-right
unification order as addition.

Inspection setup:

- Use the same isolated conversion behavior as `EXTRA-003`:
  `left = Value(1, a)`, `right = Value(2, b)`, `b -> a` cannot convert, and
  `a -> b` converts the left magnitude to `10`.

Expected assertion style:

- Assert conversion attempts occur in the same order as addition: `b -> a`,
  then `a -> b`.
- Assert the subtraction result is magnitude `8`, unit `b`.
- Do not apply this proposal to a black-box adapter unless it exposes an
  equivalent spec-level conversion-attempt trace.

Targets: `all.md` Arithmetic and Numeric Semantics line 252.

### EXTRA-005: Relationship Definition Rejects A Non-Finite Factor

Purpose: Verify relationship validation rejects an evaluated relationship whose
factor is not finite.

Inspection setup:

- Use an implementation-owned relationship-validation hook, or a formula
  evaluation hook feeding relationship validation, with:
  `Value(non_finite, {m: 1})`.
- The active source-unit list contains `m`.

Expected assertion style:

- Assert relationship formation is rejected with `Error: invalid relationship.`.
- Assert the target unit is not added and no relationship is stored.
- Avoid choosing a public numeric expression solely because it overflows on one
  runtime; the overflow threshold is implementation dependent.

Targets: `all.md` Relationship Definition and Validation lines 283 and 291.

### EXTRA-006: Scalar-Basis Relationship Converts In Both Directions

Purpose: Verify a relationship whose basis normalizes to scalar supports forward
conversion from the target unit to scalar `1`, and reverse conversion from
scalar `1` to the target unit with scale `1 / factor`.

Transcript commands:

```text
unit:m
relate:dozen:m:12 m/m
evaluate:2 dozen:1
evaluate:24:dozen
```

Expected/assertion style:

- Exactly two emitted lines.
- Line 1 parses as magnitude `24`, unit `1`.
- Line 2 parses as magnitude `2`, unit `dozen`.

Targets: `all.md` Unit Conversion Basics lines 307 and 308.

### EXTRA-007: Conversion Application Reports Invalid Relationship For Non-Finite Scale

Purpose: Verify conversion reports the required relationship error when applying
a valid stored relationship would produce a non-finite numeric scale.

Implementation-owned setup:

- Choose finite representable values `F` and integer exponent `E` for the
  implementation's `Real` type such that `F^E` is non-finite.
- Create a valid relationship equivalent to `relate:huge:m:F m`.
- Run a conversion that applies the relationship forward to `huge^E`, for
  example `evaluate:1 huge^E:m^E`, using the implementation's concrete integer
  spelling for `E`.

Expected assertion style:

- Assert exactly one emitted line:

```text
Error: invalid relationship.
```

- This proposal is not required when an implementation's numeric model cannot
  produce a non-finite scale from finite relationship factors and valid integer
  exponents.

Targets: `all.md` Unit Conversion Basics line 328; Error Text line 405.

### EXTRA-008: Same-Next Applications With The Same Scale Are Equivalent

Purpose: Verify that when multiple relationship applications produce the same
next unit expression with the same numeric scale, the public result is
independent of which application is selected.

Transcript commands:

```text
unit:cm
relate:m:cm:100 cm
relate:cm:m:0.01 m
evaluate:1 m:cm
```

Expected/assertion style:

- Exactly one emitted line.
- The line parses as magnitude `100`, unit `cm`.
- Optional inspection: if the implementation exposes conversion candidates,
  assert both candidate applications produce next `UnitExpr` `cm` with the same
  scale, and either candidate is accepted as equivalent.

Targets: `all.md` Conversion Search, Cycles, and Tie-Breaking line 354.

### EXTRA-009: Same-Next Tie Comparator Orders Forward Before Reverse As Final Tie-Breaker

Purpose: Verify the final same-next-state tie-break rule. This rule is best
tested against the implementation's conversion-candidate ordering logic because
the public transcript does not reliably expose a naturally occurring valid graph
where next unit expression, scale, and relationship target are all tied while
only direction differs.

Inspection setup:

- Construct two conversion candidates with identical serialized next `UnitExpr`,
  identical scale, and identical relationship target `u`.
- Mark one candidate as a forward application and the other as a reverse
  application.

Expected assertion style:

- Assert the candidate-ordering comparator sorts the forward application before
  the reverse application.
- Do not require this proposal for adapters that expose only transcript I/O.

Targets: `all.md` Conversion Search, Cycles, and Tie-Breaking line 355.

### EXTRA-010: Relationship Basis Cannot Contain Units Outside The Source List

Purpose: Verify relationship validation enforces that an evaluated basis
contains only units named in the relationship source-unit list. Public
relationship formulas usually fail earlier by source-context name resolution, so
this proposal uses an implementation-owned validation hook.

Inspection setup:

- The source-unit list is exactly `{m}`.
- Feed relationship validation a candidate result `Value(1, {m: 1, s: 1})`.

Expected assertion style:

- Assert relationship formation is rejected with `Error: invalid relationship.`.
- Assert the target unit is not added and no relationship is stored.

Targets: `all.md` Relationship Definition and Validation lines 287 and 291.

### EXTRA-011: Self Conversion Uses Scale `1`

Purpose: Verify converting a unit expression to itself succeeds without changing
the magnitude.

Transcript commands:

```text
unit:m
unit:s
evaluate:7 m/s:m/s
```

Expected/assertion style:

- Exactly one emitted line.
- The line parses as magnitude `7`, unit `m/s`.

Targets: `all.md` Unit Conversion Basics line 302.

### EXTRA-012: Complete Transcript Shows Shortest-Path Choice Among Competing Paths

Purpose: Verify shortest-path conversion behavior through a complete transcript
with two competing equal-length conversion paths whose observable scales differ.

Transcript commands:

```text
unit:a
unit:z
relate:s:a:2 a
relate:a:z:3 z
relate:b:s:0.5 s
relate:z:b:0.25 b
evaluate:1 s:z
```

Expected/assertion style:

- Exactly one emitted line.
- The line parses as magnitude `6`, unit `z`.
- The competing shortest paths are `s -> a -> z` with scale `6` and
  `s -> b -> z` with scale `8`; the path through `a` wins because `a`
  serializes before `b`.

Targets: `all.md` Conversion Search, Cycles, and Tie-Breaking lines 341 and 420.

### EXTRA-013: Every Error Line Starts With `Error:`

Purpose: Verify the generic error-prefix invariant over a transcript that
produces the catalog of specified recoverable errors.

Transcript commands:

```text
bogus
unit:M
set:x:1
unit:m
unit:s
set:X
relate:t:m,,s:1 m
evaluate:1 @ 2
evaluate:1:m^0.5
evaluate:X
evaluate:u
evaluate:1 m:s
evaluate:(1 m)^m
evaluate:[ 1 m
evaluate:[ 0
evaluate:] 1 m
evaluate:1 / 0
relate:z:m:0 m
```

Expected/assertion style:

- Assert exactly sixteen emitted lines.
- Assert every emitted line starts with `Error:`.
- Exact message text can be checked by the more specific error-text proposals;
  this proposal only covers the common prefix invariant.

Targets: `all.md` Error Text and Precedence line 389.

### EXTRA-014: Internal Whitespace Is Not Allowed In Identifier Names

Purpose: Verify leading/trailing field trimming does not permit whitespace
inside unit or variable identifiers.

Transcript commands:

```text
unit:m s
set:X Y:1
```

Expected emitted lines:

```text
Error: invalid unit name.
Error: invalid variable name.
```

Targets: `all.md` Identifier Rules line 71.

### EXTRA-015: Failed Evaluate Does Not Mutate Existing State

Purpose: Verify a failed `evaluate` command leaves declared units, stored
variables, and stored relationships unchanged.

Transcript commands:

```text
unit:m
relate:cm:m:0.01 m
set:X:1 m
evaluate:Y
evaluate:X
evaluate:1 m:cm
```

Expected/assertion style:

- Exactly three emitted lines.
- Line 1 is exactly `Error: unknown variable Y.`
- Line 2 parses as magnitude `1`, unit `m`.
- Line 3 parses as magnitude `100`, unit `cm`.

Targets: `all.md` Session/Transcript lines 21 and 25.

### EXTRA-016: Relationship Replacement And Error Recovery Are Observable

Purpose: Verify relationship replacement affects later conversion and that an
error between successful commands does not erase prior state or prevent later
success.

Transcript commands:

```text
unit:m
relate:cm:m:0.01 m
evaluate:1 m:cm
bogus
relate:cm:m:0.02 m
evaluate:1 m:cm
```

Expected/assertion style:

- Exactly three emitted lines.
- Line 1 parses as magnitude `100`, unit `cm`.
- Line 2 is exactly `Error: unknown command.`
- Line 3 parses as magnitude `50`, unit `cm`.

Targets: `all.md` End-To-End lines 416 and 417.

### EXTRA-017: Scalar-Only Workflow Needs No Declared Units

Purpose: Verify a transcript using only scalar values, variables, and scalar
arithmetic works without declaring any units.

Transcript commands:

```text
set:X:4
evaluate:2 + 3
evaluate:X * 2
```

Expected/assertion style:

- Exactly two emitted lines.
- Line 1 parses as magnitude `5`, unit `1`.
- Line 2 parses as magnitude `8`, unit `1`.

Targets: `all.md` End-To-End line 418.

### EXTRA-018: Same-Next Different-Scale Tie Chooses Alphabetically First Target

Purpose: Verify same-next-state tie-breaking when multiple relationship
applications produce the same next unit expression with different numeric
scales.

Transcript commands:

```text
unit:cm
relate:m:cm:101 cm
relate:cm:m:0.01 m
evaluate:1 m:cm
```

Expected/assertion style:

- Exactly one emitted line.
- The line parses as magnitude `100`, unit `cm`.
- Both relationships can produce next unit expression `cm`; because relationship
  target `cm` sorts before `m`, the `cm` relationship's reverse application
  determines the result.

Targets: `all.md` Conversion Search, Cycles, and Tie-Breaking line 353.

### EXTRA-019: Magnitude Serialization Is Deterministic

Purpose: Verify repeated identical scalar evaluations emit the same raw
magnitude spelling while remaining finite and parseable by the number grammar.

Transcript commands:

```text
evaluate:10 / 4
evaluate:10 / 4
```

Expected/assertion style:

- Exactly two emitted lines.
- Both lines parse as magnitude `2.5`, unit `1`.
- The raw magnitude substrings are exactly identical across both lines.

Targets: `all.md` Serialization and Output lines 379-381.

### EXTRA-020: Relationship Formula Units Normalize Before Later Conversion

Purpose: Verify repeated or canceling source units in a relationship formula are
normalized when the relationship is stored and later applied.

Transcript commands:

```text
unit:m
unit:s
relate:u:m,s:3 m*s/s
evaluate:2 u:m
```

Expected/assertion style:

- Exactly one emitted line.
- The line parses as magnitude `6`, unit `m`.

Targets: `all.md` Relationship Definition and Validation line 286.

### EXTRA-021: Non-Integer Unit Exponents Participate In Conversion

Purpose: Verify relationship applications support non-integer application
exponents and that value-formula-produced non-integer unit expressions can be
unified through conversion.

Transcript commands:

```text
unit:m
relate:cm:m:0.01 m
evaluate:(4 cm)^0.5 + (1 m)^0.5
evaluate:(1 m)^0.5 + (4 cm)^0.5
```

Expected/assertion style:

- Exactly two emitted lines.
- Line 1 parses as magnitude `12`, unit `cm^0.5`.
- Line 2 parses as magnitude `1.2`, unit `m^0.5`.

Targets: `all.md` Unit Conversion Basics lines 314-315.
