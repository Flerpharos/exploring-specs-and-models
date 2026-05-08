# Consolidated Black-Box Test Targets

This file consolidates the twelve agent-generated target lists into one non-duplicative checklist. It keeps one target for each distinct externally observable behavior and avoids implementation details that are not required by `SPEC.md`.

Source files: `atlas.md`, `boreal.md`, `cypher.md`, `delta.md`, `ember.md`, `flux.md`, `gamma.md`, `helix.md`, `ion.md`, `lumen.md`, `quasar.md`, `vector.md`.

## Session, Transcript, and Command Flow

- [ ] test that command-looking text after a command on the same input line is handled as part of that one command, not as a second command.
- [ ] test that empty input lines are ignored.
- [ ] test that successful `unit`, `set`, and `relate` commands emit no output.
- [ ] test that a successful `evaluate` command emits exactly one result line.
- [ ] test that each recoverable error emits exactly one error line.
- [ ] test that a recoverable error does not terminate the session.
- [ ] test that later commands observe state from earlier successful commands in the same session.
- [ ] test that UTF-8 encoded input is read by the command reader and valid ASCII command syntax reaches normal command processing.
- [ ] test that non-ASCII UTF-8 characters in otherwise identifier-like text are handled through the specified identifier or formula error rules rather than as byte-level input failures.
- [ ] test that command prefixes are case-sensitive.
- [ ] test that unknown command prefixes report `Error: unknown command.`.
- [ ] test that malformed supported commands report `Error: invalid command syntax.` when no more specific required error applies.
- [ ] test that a failed command leaves the entire environment unchanged.
- [ ] test that a failed `unit` command does not add a unit.
- [ ] test that a failed `set` command does not create or replace a variable.
- [ ] test that a failed `relate` command does not create or replace a relationship.
- [ ] test that a failed `evaluate` command does not mutate units, variables, or relationships.
- [ ] test that successful `evaluate` commands, including successful conversions, do not mutate units, variables, or relationships.
- [ ] test that non-ASCII characters inside identifiers are rejected by the identifier rules.

## Command Parsing and Field Splitting

- [ ] test that all command fields are trimmed before validation.
- [ ] test that required command fields must be non-empty after trimming.
- [ ] test that `unit:` treats all payload text after the prefix as the unit name field.
- [ ] test that `unit:` rejects an empty payload.
- [ ] test that `unit:m:extra` is rejected as an invalid unit name.
- [ ] test that `set:` splits its payload once at the first colon.
- [ ] test that `set:` rejects a missing colon after the variable field.
- [ ] test that `set::1` rejects an empty variable field.
- [ ] test that `set:X:` rejects an empty value formula field.
- [ ] test that `set:X:1:2` parses `1:2` as the formula field and rejects it as an invalid formula.
- [ ] test that `relate:` splits its payload twice from the left.
- [ ] test that `relate:` rejects a missing target field.
- [ ] test that `relate:` rejects a missing source-unit-list field.
- [ ] test that `relate:` rejects a missing relationship formula field.
- [ ] test that `relate:t:a:1:extra` is split so `1:extra` is the relationship formula and reports `Error: invalid formula.` when source unit `a` is valid.
- [ ] test that `evaluate:` with no colon in the payload has no output-unit field.
- [ ] test that `evaluate:` splits its payload once at the last colon.
- [ ] test that `evaluate:1:2:m` parses `m` as the output-unit formula and then reports `Error: invalid formula.` for value formula `1:2` when `m` is declared.
- [ ] test that `evaluate:` rejects an empty value formula.
- [ ] test that `evaluate:1:` rejects an empty output-unit formula.
- [ ] test that `evaluate::m` rejects an empty value formula.

## Identifier Rules and Namespaces

- [ ] test that a single lowercase letter is a valid unit identifier.
- [ ] test that multi-letter lowercase unit identifiers are valid.
- [ ] test that unit identifiers may contain underscores after the first character.
- [ ] test that unit identifiers may not start with an underscore.
- [ ] test that unit identifiers may not contain digits.
- [ ] test that unit identifiers may not contain uppercase letters.
- [ ] test that a single uppercase letter is a valid variable identifier.
- [ ] test that multi-letter uppercase variable identifiers are valid.
- [ ] test that variable identifiers may contain underscores after the first character.
- [ ] test that variable identifiers may not start with an underscore.
- [ ] test that variable identifiers may not contain digits.
- [ ] test that variable identifiers may not contain lowercase letters.
- [ ] test that mixed-case identifiers are invalid formula tokens.
- [ ] test that lowercase identifiers are resolved only as units in value formulas.
- [ ] test that uppercase identifiers are resolved only as variables in value formulas.
- [ ] test that lowercase and uppercase spellings in one transcript resolve through distinct unit and variable namespaces.
- [ ] test that identifiers cannot contain whitespace inside the name.
- [ ] test that `m_s` is one identifier, not an implicit product.

## Number and Token Lexing

- [ ] test that integer number literals are accepted.
- [ ] test that decimal literals with digits on both sides of `.` are accepted.
- [ ] test that decimal literals beginning with `.` are accepted.
- [ ] test that scientific notation accepts lowercase `e`.
- [ ] test that scientific notation accepts uppercase `E`.
- [ ] test that scientific notation accepts signed exponents.
- [ ] test that a decimal point without following digits is rejected.
- [ ] test that an exponent marker without exponent digits is rejected.
- [ ] test that a number parsing to a non-finite real value is rejected.
- [ ] test that whitespace cannot split a number token.
- [ ] test that whitespace is ignored between unambiguous formula tokens.
- [ ] test that `1m` and `1 m` tokenize equivalently when `m` is declared.
- [ ] test that `1m/s` and `1 m / s` tokenize equivalently when units are declared.
- [ ] test that value formulas accept the specified number, identifier, operator, parenthesis, and bracket syntax.
- [ ] test or inspect that formula lexing recognizes the specified token classes, including `NUMBER`, unit identifiers, variable identifiers, operators, parentheses, brackets, and `EOF`.
- [ ] test that non-whitespace trailing input after a complete formula is rejected.
- [ ] test that invalid characters in formulas report `Error: invalid formula.`.

## Unit Declarations and Source Unit Lists

- [ ] test that `unit:<valid-unit-id>` declares a unit.
- [ ] test that declaring an already-declared unit succeeds without duplicate observable output.
- [ ] test that declaring a unit does not define any conversion relationship to other declared units.
- [ ] test that invalid unit names in `unit:` report `Error: invalid unit name.`.
- [ ] test that declared units can be used as value-context identifiers.
- [ ] test that declared units can be used in value-literal unit sections.
- [ ] test that declared units can be used in output-unit formulas.
- [ ] test that a source unit list accepts one declared unit.
- [ ] test that a source unit list accepts multiple comma-separated declared units.
- [ ] test that source unit list items are trimmed.
- [ ] test that an empty source unit list is rejected.
- [ ] test that empty source unit list items are rejected.
- [ ] test that duplicate source unit list items are rejected.
- [ ] test that invalid unit identifiers in a source unit list are rejected.
- [ ] test that undeclared units in a source unit list are rejected.
- [ ] test that source unit list failures report `Error: invalid unit list.`.
- [ ] test that a relationship target unit is not required to be declared beforehand.
- [ ] test that the relationship target may not appear in its own source unit list.

## Value Literals and Unit Syntax

- [ ] test that a number without a unit section is scalar and serializes with unit `1`.
- [ ] test that a number followed by a unit creates a value literal with that unit.
- [ ] test that `2 + 3 m` reports `Error: cannot convert m to 1.` when `m` is declared and no conversion relationship exists.
- [ ] test that `2 m + 3` reports `Error: cannot convert 1 to m.` when `m` is declared and no conversion relationship exists.
- [ ] test that value-literal unit sections consume the longest valid unit section.
- [ ] test that `2 m/s` parses as a single value literal with unit `m/s`.
- [ ] test that `2 m * s` parses as a single value literal with unit `m*s`.
- [ ] test that `2 m + 3` parses as a value literal plus a scalar.
- [ ] test that `2 m / s + 1` parses with unit `m/s` before addition.
- [ ] test that `2 m^2^3` is invalid after the unit factor is complete.
- [ ] test that `2 m^ -1` accepts a signed integer unit exponent.
- [ ] test that a `*` consumed as part of a value-literal unit section must be followed by a valid unit factor.
- [ ] test that a `/` consumed as part of a value-literal unit section must be followed by a valid unit factor.
- [ ] test that `2 m / + 1` is invalid because `/` has been consumed by value-literal unit-section parsing.
- [ ] test that parenthesized unit sections such as `2 (m/s)^2` are accepted.
- [ ] test that scalar unit primary `1` is not valid in a value-literal unit section.
- [ ] test that `2 1` is not treated as a value literal with scalar unit section.
- [ ] test that `2 (1)` is rejected because value-literal unit sections do not include scalar unit primary `1`.
- [ ] test that no implicit multiplication exists between formula expressions.
- [ ] test that `2 X` is invalid because variables cannot appear in unit sections.
- [ ] test that `2 (X + 1)` is invalid as a unit section.
- [ ] test that adjacent expressions such as `X (2)` are invalid even when `X` exists.
- [ ] test that `2 * X` and `2 * (X + 1)` are valid value formulas when `X` exists.
- [ ] test that unit expression multiplication adds exponents.
- [ ] test that unit expression division subtracts exponents.
- [ ] test that unit expression power multiplies exponents by an integer in input unit syntax.
- [ ] test that repeated units in a unit expression are combined.
- [ ] test that units with zero exponent are removed during normalization.
- [ ] test that `1` in unit syntax denotes the scalar unit expression.
- [ ] test that parentheses can group unit expressions.
- [ ] test that input unit syntax accepts only integer exponents.
- [ ] test that `+` and `-` are accepted only as signs in integer exponents within unit syntax.
- [ ] test that unknown units in value-literal unit sections report `Error: unknown unit <name>.`.

## Value Formula Grammar and Precedence

- [ ] test that value formulas support value literals.
- [ ] test that value formulas support variable identifiers.
- [ ] test that value formulas support unit identifiers.
- [ ] test that value formulas support unary `+` and unary `-`.
- [ ] test that value formulas support binary `+`, `-`, `*`, `/`, and `^`.
- [ ] test that value formulas support parentheses.
- [ ] test that value formulas support prefix `[` as natural logarithm.
- [ ] test that value formulas support prefix `]` as exponential.
- [ ] test that parentheses override addition before multiplication and override power operands.
- [ ] test that value-literal unit attachment binds tighter than unary operators in a formula where the wrong parse would change the error or result.
- [ ] test that `2 m ^ 2` parses as `2 m^2`, proving value-literal unit attachment binds tighter than binary power.
- [ ] test that `*` and `/` bind tighter than `+` and `-`.
- [ ] test that multiplication binds tighter than addition.
- [ ] test that division binds tighter than subtraction.
- [ ] test that prefix log, prefix exp, and unary operators each bind tighter than power in formulas where the wrong parse would change the result.
- [ ] test that `^` is right-associative.
- [ ] test that `*` and `/` are left-associative.
- [ ] test that `+` and `-` are left-associative.
- [ ] test that `-2^2` parses as `(-2)^2`.
- [ ] test that `-(2^2)` parses as negation of the power result.
- [ ] test that unary and prefix operators compose right-associatively in a mixed operator chain.
- [ ] test that malformed parentheses report `Error: invalid formula.`.
- [ ] test that leftover tokens after a valid expression report `Error: invalid formula.`.
- [ ] test that binary operators missing operands report `Error: invalid formula.`.
- [ ] test that prefix log and exp operators missing operands report `Error: invalid formula.`.

## Relationship Formula Grammar and Context

- [ ] test that relationship formulas support value literals.
- [ ] test that relationship formulas support source-unit identifiers.
- [ ] test that relationship formulas support unary `+` and unary `-`.
- [ ] test that relationship formulas support binary `*`, `/`, and `^`.
- [ ] test that relationship formulas support parentheses.
- [ ] test that relationship formula unary precedence is observable through a later conversion result.
- [ ] test that relationship formula power is right-associative as observed through a later conversion result.
- [ ] test that relationship formula multiplication and division are left-associative as observed through a later conversion result.
- [ ] test that relationship formula parentheses override precedence as observed through a later conversion result.
- [ ] test that relationship formulas reject binary `+`.
- [ ] test that relationship formulas reject binary `-`.
- [ ] test that relationship formulas reject prefix log `[`.
- [ ] test that relationship formulas reject prefix exp `]`.
- [ ] test that relationship-context identifiers resolve only if present in the source unit list.
- [ ] test that existing variables are ignored in relationship context.
- [ ] test that existing declared units outside the source list are ignored in relationship context.
- [ ] test that existing relationships are not applied while evaluating a relationship formula.
- [ ] test that unit names in relationship value-literal unit sections resolve only against the source unit list.
- [ ] test that the relationship target cannot appear in its own relationship formula through identifier resolution.
- [ ] test that invalid relationship formulas report `Error: invalid formula.`.
- [ ] test that unknown source-context units report `Error: unknown unit <name>.`.

## Output Unit Formulas

- [ ] test that output-unit formulas accept the unit-expression constructs `1`, declared unit identifiers, products, quotients, parentheses, and integer powers.
- [ ] test that output-unit formulas accept exactly `1` as the scalar unit expression but reject other numeric magnitude syntax such as `2`, `1.0`, `.5`, or `1e0`.
- [ ] test that output-unit formulas reject value-formula-only syntax such as numeric magnitudes, `+`, binary `-`, prefix `[`, and prefix `]`.
- [ ] test that output-unit formulas resolve only declared units.
- [ ] test that unknown output units report `Error: unknown unit <name>.`.
- [ ] test that invalid output-unit syntax reports `Error: invalid output unit.`.
- [ ] test that `evaluate` parses and evaluates the output-unit field before the value formula.
- [ ] test that output-unit errors take precedence over value-formula errors.
- [ ] test that output unit `1` requests scalar output.
- [ ] test that compound output units require explicit `*` or `/`.
- [ ] test that output unit `m_s` is a single unit identifier.
- [ ] test that output unit `m/s` is division of `m` by `s`.
- [ ] test that output unit `(m/s)^2` requests and prints target unit `m^2/s^2` when `m` and `s` are declared.

## Value Context and Identifier Resolution

- [ ] test that an existing variable identifier resolves to its stored value.
- [ ] test that an unknown variable reports `Error: unknown variable <name>.`.
- [ ] test that an existing unit identifier resolves to value `1 <unit>`.
- [ ] test that an unknown unit reports `Error: unknown unit <name>.`.
- [ ] test that invalid identifier tokens in value context report `Error: invalid formula.`.
- [ ] test that `set` evaluates its formula in value context.
- [ ] test that `evaluate` evaluates its first field in value context.
- [ ] test that a successful `set` creates a variable binding.
- [ ] test that a successful `set` replaces an existing variable binding.
- [ ] test that setting a variable from another variable stores a snapshot value rather than an alias.
- [ ] test that `set` rejects invalid variable names with `Error: invalid variable name.`.
- [ ] test that variables can store scalar values.
- [ ] test that variables can store unit-bearing values.
- [ ] test that variables preserve the unit expression produced by formula evaluation.
- [ ] test that later changes to a source variable do not change variables previously assigned from it.

## Arithmetic and Numeric Semantics

- [ ] test that unary `+` preserves magnitude and unit.
- [ ] test that unary `-` negates magnitude and preserves unit.
- [ ] test that multiplication multiplies magnitudes and multiplies unit expressions.
- [ ] test that division divides magnitudes and divides unit expressions.
- [ ] test that division by zero reports `Error: division by zero.`.
- [ ] test that power requires a scalar exponent.
- [ ] test that non-scalar exponents report `Error: exponent must be scalar.`.
- [ ] test that power raises the magnitude and multiplies unit exponents by the scalar exponent.
- [ ] test that power with a scalar fractional exponent produces the corresponding non-integer unit exponent and serialized output.
- [ ] test that addition requires operands representing the same physical dimension.
- [ ] test that subtraction requires operands representing the same physical dimension.
- [ ] test that addition first attempts to convert the right operand to the left operand unit.
- [ ] test that addition falls back to converting the left operand to the right operand unit.
- [ ] test that subtraction uses the same unit-unification order as addition.
- [ ] test that addition of identical unit expressions adds magnitudes and preserves the unit expression.
- [ ] test that subtraction of identical unit expressions subtracts magnitudes and preserves the unit expression.
- [ ] test that addition and subtraction do not mutate variable operands while unifying units.
- [ ] test that incompatible addition reports `Error: cannot convert <source-unit> to <target-unit>.`.
- [ ] test that incompatible subtraction reports `Error: cannot convert <source-unit> to <target-unit>.`.
- [ ] test that incompatible addition reports the failed right-operand-to-left-operand conversion direction when both unification directions fail.
- [ ] test that incompatible subtraction reports the failed right-operand-to-left-operand conversion direction when both unification directions fail.
- [ ] test that scalar addition and subtraction work with unit `1`.
- [ ] test that multiplication and division do not require compatible units.
- [ ] test that prefix log requires a scalar argument.
- [ ] test that log of a unit-bearing value reports `Error: log argument must be scalar.`.
- [ ] test that log requires a positive magnitude.
- [ ] test that log of zero or a negative scalar reports `Error: log argument must be positive.`.
- [ ] test that prefix exp requires a scalar argument.
- [ ] test that exp of a unit-bearing value reports `Error: exp argument must be scalar.`.
- [ ] test that log and exp produce scalar results when successful.
- [ ] test that non-finite numeric results report `Error: numeric result is not finite.`.
- [ ] test that non-real numeric results report `Error: numeric result is not real.`.

## Relationship Definition and Validation

- [ ] test that a valid `relate` command adds the target unit to the unit set.
- [ ] test that a valid `relate` command is allowed when the target unit was already declared with `unit`.
- [ ] test that a valid `relate` command stores a relationship for the target unit.
- [ ] test or inspect that every stored relationship is keyed by its target unit identifier.
- [ ] test or inspect that every stored relationship satisfies `Relationships[k].target == k`.
- [ ] test or inspect that every stored valid relationship has a finite nonzero factor and a normalized basis.
- [ ] test that a successful `relate` replaces an existing relationship for the same target.
- [ ] test that relationship targets must be valid unit identifiers.
- [ ] test that invalid relationship target names report `Error: invalid unit name.`.
- [ ] test that the relationship factor must be finite.
- [ ] test that the relationship factor must be nonzero.
- [ ] test that finite nonzero negative relationship factors are valid.
- [ ] test that relationship formulas with repeated or canceling source units are normalized before later conversion.
- [ ] test that the relationship basis may contain only source-list units.
- [ ] test that a valid relationship basis may omit some units from the source unit list.
- [ ] test that a relationship whose basis normalizes to scalar is accepted when the factor is finite and nonzero.
- [ ] test that a relationship formula may produce and store a basis with a non-integer real exponent.
- [ ] test that invalid evaluated relationships report `Error: invalid relationship.`.
- [ ] test that `relate:cm:m:0.01 m` defines `1 cm = 0.01 m`.
- [ ] test that `relate:n:kg,m,s:kg*m/s^2` defines `1 n = 1 kg*m/s^2`.
- [ ] test that relationship cycles are accepted at definition time.
- [ ] test that relationship definition does not apply existing conversion relationships.
- [ ] test that an invalid source unit list is rejected when the relationship formula is otherwise valid.
- [ ] test that relationship formulas can use declared source units even when the target was undeclared.
- [ ] test that relationship formulas cannot reference the target unit unless it is also illegally listed as a source.

## Unit Conversion Basics

- [ ] test that converting a unit expression to itself succeeds with scale factor `1`.
- [ ] test that conversion failures report `Error: cannot convert <source-unit> to <target-unit>.`.
- [ ] test that conversion error messages serialize source and target units using normalized unit serialization.
- [ ] test that scalar unit `1` converts to scalar `1` immediately.
- [ ] test that converting a non-scalar unit expression to scalar `1` fails unless relationships transform the unit expression.
- [ ] test that a scalar-basis relationship supports forward conversion from the target unit to scalar `1`.
- [ ] test that a scalar-basis relationship supports reverse conversion from scalar `1` to the target unit with scale factor `1 / factor`.
- [ ] test that a relationship forward application replaces `target^e` with `basis^e`.
- [ ] test that a forward application multiplies magnitude by `factor^e`.
- [ ] test that `cm -> m` uses scale `0.01` for `relate:cm:m:0.01 m`.
- [ ] test that `cm^2 -> m^2` uses scale `0.01^2`.
- [ ] test that `1/cm -> 1/m` uses scale `0.01^-1`.
- [ ] test that relationship applications support non-integer exponents and apply scale factor `factor^e`.
- [ ] test that conversion and unit unification work for formula-produced unit expressions with non-integer exponents.
- [ ] test that a reverse application replaces the largest proportional occurrence of the basis with the target.
- [ ] test that a reverse application multiplies magnitude by `factor^-e`.
- [ ] test that `m -> cm` uses scale `100` for `relate:cm:m:0.01 m`.
- [ ] test that `m^2 -> cm^2` uses scale `100^2`.
- [ ] test that `1/m -> 1/cm` uses scale `100^-1`.
- [ ] test that reverse application handles composite bases such as `kg*m/s^2 -> n`.
- [ ] test that reverse application handles powers such as `kg^2*m^2/s^4 -> n^2`.
- [ ] test that reverse application handles partial composite replacement such as `kg*m^2/s^2 -> m*n`.
- [ ] test that reverse application handles negative exponents such as `s^2/(kg*m) -> 1/n`.
- [ ] test that reverse application is possible only when all nonzero basis ratios share one sign.
- [ ] test that conversion applications normalize the resulting unit expression.
- [ ] test that conversion applications producing non-real numeric operations report `Error: invalid relationship.`.
- [ ] test that conversion applications producing non-finite scales report `Error: invalid relationship.`.
- [ ] test or inspect with seeded internal state that conversion reports `Error: invalid relationship.` when a stored relationship has factor `0`.
- [ ] test or inspect with seeded internal state that conversion reports `Error: invalid relationship.` when a stored relationship has a non-finite factor.
- [ ] test or inspect with seeded internal state that conversion reports `Error: invalid relationship.` when a stored relationship has a non-normalized basis.
- [ ] test that a relationship with a negative factor produces the specified sign for odd positive, even positive, and negative integer exponent conversions.

## Conversion Search, Cycles, and Tie-Breaking

- [ ] test that conversion search performs a multi-step conversion when a finite sequence of relationship applications exists.
- [ ] test that one conversion can require both forward and reverse relationship applications.
- [ ] test that conversion search returns a shortest path by number of relationship applications.
- [ ] test that conversion search stops at the shortest target path rather than continuing through longer cyclic paths.
- [ ] test that unrelated valid relationships do not prevent a valid shortest conversion path from succeeding.
- [ ] test that among shortest paths, the lexicographically smallest sequence of serialized intermediate unit expressions determines the observable conversion result.
- [ ] test or inspect that conversion search marks the initial source `UnitExpr` as visited before relationship expansion.
- [ ] test or inspect that conversion search skips relationship applications that would produce an already visited `UnitExpr`.
- [ ] test or inspect that conversion search does not revisit a previously visited `UnitExpr` during one conversion evaluation.
- [ ] test or inspect that encountering a previously visited `UnitExpr` does not itself produce an error.
- [ ] test that cyclic conversion graphs terminate with the shortest valid result when a target is reachable.
- [ ] test that cyclic conversion graphs terminate with `Error: cannot convert <source-unit> to <target-unit>.` when the target is unreachable.
- [ ] test that cyclic relationship graphs do not cause infinite search.
- [ ] test that a cycle alone is not an invalid relationship.
- [ ] test that an exhausted conversion search reports `Error: cannot convert <source-unit> to <target-unit>.`.
- [ ] test that an inconsistent one-step conversion beats a longer cyclic path.
- [ ] test that `relate:cm:m:0.01 m` and `relate:m:cm:101 cm` still convert `1 m:cm` as `100 cm`.
- [ ] test that multiple applications yielding the same next unit expression choose the alphabetically first relationship target when scales differ.
- [ ] test or inspect that multiple applications yielding the same next `UnitExpr` with the same scale are treated as equivalent for ordering purposes.
- [ ] test or inspect that when same-next-state tie-breaking is still tied, forward application is ordered before reverse application.
- [ ] test that replacing a relationship changes later conversion results.
- [ ] test that composite and powered conversions can be chained across multiple relationships.
- [ ] test that conversion search works for units in numerators and denominators.
- [ ] test that reverse application treats units absent from the current unit expression as ratio zero in a partial-basis conversion.

## Serialization and Output

- [ ] test that successful evaluation output has the form `<magnitude> <serialized-unit>`.
- [ ] test that scalar unit expressions serialize as `1`.
- [ ] test that positive exponents appear in the numerator.
- [ ] test that negative exponents appear in the denominator.
- [ ] test that identifiers are sorted lexicographically within numerator and denominator.
- [ ] test that exponent `1` is omitted.
- [ ] test that exponents other than `1` are written with `^`.
- [ ] test that all-negative unit expressions serialize with numerator `1`.
- [ ] test that `{m: 1, s: -1}` serializes as `m/s`.
- [ ] test that `{kg: 1, m: 1, s: -2}` serializes as `kg*m/s^2`.
- [ ] test that `{s: -1}` serializes as `1/s`.
- [ ] test that a formula-produced non-integer unit exponent such as `m^0.5` can be serialized.
- [ ] test that repeated evaluations producing the same non-integer unit exponent serialize that exponent deterministically.
- [ ] test that a value-literal unit section with non-integer exponent syntax such as `m^0.5` reports `Error: invalid formula.` when `m` is declared.
- [ ] test that an output-unit formula with non-integer exponent syntax such as `m^0.5` reports `Error: invalid output unit.` when `m` is declared.
- [ ] test that normalized unit serialization emits no parentheses.
- [ ] test that magnitude serialization is deterministic for repeated identical evaluations.
- [ ] test that magnitude serialization is finite.
- [ ] test that magnitude serialization is parseable by the spec number grammar.
- [ ] test that `evaluate` without an output unit prints the formula result unit.
- [ ] test that `evaluate` with an output unit prints the requested target unit.
- [ ] test that successful `evaluate:2 + 3` prints a value equivalent to `5 1`.
- [ ] test that successful `evaluate:2 m/s` prints a value equivalent to `2 m/s`.

## Error Text and Precedence

- [ ] test that all errors begin with `Error:`.
- [ ] test that unknown commands report exactly `Error: unknown command.`.
- [ ] test that invalid command syntax reports exactly `Error: invalid command syntax.`.
- [ ] test that invalid formulas report exactly `Error: invalid formula.`.
- [ ] test that invalid output units report exactly `Error: invalid output unit.`.
- [ ] test that invalid unit names report exactly `Error: invalid unit name.`.
- [ ] test that invalid variable names report exactly `Error: invalid variable name.`.
- [ ] test that invalid source unit lists report exactly `Error: invalid unit list.`.
- [ ] test that unknown variables include the variable name in `Error: unknown variable <name>.`.
- [ ] test that unknown units include the unit name in `Error: unknown unit <name>.`.
- [ ] test that conversion failures use exactly `Error: cannot convert <source-unit> to <target-unit>.`.
- [ ] test that non-scalar exponents report exactly `Error: exponent must be scalar.`.
- [ ] test that non-scalar log arguments report exactly `Error: log argument must be scalar.`.
- [ ] test that non-positive log arguments report exactly `Error: log argument must be positive.`.
- [ ] test that non-scalar exp arguments report exactly `Error: exp argument must be scalar.`.
- [ ] test that division by zero reports exactly `Error: division by zero.`.
- [ ] test that invalid relationships report exactly `Error: invalid relationship.`.
- [ ] test that non-finite numeric results report exactly `Error: numeric result is not finite.`.
- [ ] test that non-real numeric results report exactly `Error: numeric result is not real.`.
- [ ] test that `evaluate` output-unit errors take precedence over value-formula errors.
- [ ] test that `evaluate` without an output-unit field does not attempt conversion.
- [ ] test that a concrete input with multiple possible errors outside explicit precedence rules emits exactly one of the enumerated applicable required error lines.

## End-To-End Workflows and Boundaries

- [ ] test that a full transcript can declare base units, define variables, define relationships, and evaluate a converted expression with the expected magnitude and unit.
- [ ] test that variables can be reused across multiple evaluations.
- [ ] test that relationship replacement affects later output conversion.
- [ ] test that errors between successful commands do not erase previous state.
- [ ] test that scalar-only workflows work without declaring any units.
- [ ] test that a compound-unit transcript combines declared units, variables, relationships, and output-unit conversion with the expected final value.
- [ ] test that shortest-path conversion behavior is observable through a complete transcript with competing conversion paths.
- [ ] test that cyclic relationship behavior is observable through transcript output or required errors without access to the internal graph.
