# Golden contract tests (Python + TypeScript)

These suites are intentionally **adapter-driven** and now kept **in sync** across languages.

## Adapter contract

- Python: implement `run(command: str) -> str | None`
- TypeScript: implement `run(command: string): string | null | undefined`

Commands that succeed with no output should return empty output (`""`, `None`, `null`, or `undefined`), and commands that print should return exactly one output line.

## Sync guarantee

Both language suites test the same 11 categories:

1. commands and identifier validation
2. literals / unit syntax / serialization
3. value-context identifier resolution
4. operator semantics and precedence
5. add/sub unification via conversion
6. scalar constraints (`^`, `[` , `]`)
7. relationship-context restrictions + replacement behavior
8. evaluate output-unit precedence
9. conversion success and conversion failure
10. shortest-path behavior in inconsistent cycles
11. failed command leaves environment unchanged

## Coverage audit notes (undertest/overtest guardrails)

The suite intentionally:

- **Asserts exact strings for required errors** (e.g. `Error: invalid formula.`) because the spec requires these messages.
- **Asserts unit serialization exactly** because unit canonicalization/ordering is specified.
- **Asserts numeric value semantically** (parsed finite magnitude + tolerance), not exact float text formatting, because the spec requires deterministic parseable numbers but does not lock a single decimal formatting style.

The suite does **not** assert behavior that the spec marks underspecified, including:

- implementation-specific real edge behavior for non-real/overflow-prone power cases beyond required error classes,
- arbitrary tie cases not concretely constrained by the spec’s shortest-path ordering rules.

## Spec coverage matrix

This matrix is the maintenance checklist used to avoid undertesting/overtesting drift.

- **Lexical rules / identifiers**: covered (valid + invalid unit/variable names, digits, case rules).
- **Command syntax and required fields**: covered (`unit`, `set`, `relate`, `evaluate`, unknown command, invalid command syntax).
- **Value literals + unit sections**: covered (compound units, parenthesized unit sections, no implicit multiplication).
- **Value context resolution**: covered (known/unknown variables and units).
- **Operator precedence + associativity**: covered (`-2^2`, `-(2^2)`, `2^3^2`, multiplicative precedence).
- **Scalar constraints**: covered (`^` exponent scalar, log/exp scalar checks, log positivity).
- **Relationship context restrictions**: covered (no `+`/`-`/`[`/`]`, source-list-only unit resolution, target excluded from source list).
- **Relationship replacement semantics**: covered (second `relate` for same target overwrites first).
- **Output-unit context and precedence**: covered (output-unit parse errors and precedence over value-formula errors).
- **Conversion semantics**: covered (forward/reverse, powers, reciprocal units, conversion failure).
- **Shortest-path behavior in inconsistent cycles**: covered (`m <-> cm` inconsistency still resolves shortest path result).
- **Failed command immutability**: covered (failed `set` leaves prior variable value unchanged).

Out-of-scope by design (underspecified in spec): implementation-specific floating text format details, and unconstrained non-real numeric edge behavior beyond required error classes.

## Important scope note

This suite avoids asserting behavior the spec leaves unspecified (for example implementation-specific floating formatting beyond deterministic parseable output, non-real power edge behavior, or tie-break cases not explicitly constructed).

## Usage

### Python

```python
from tests.python.test_spec_contract import UnitAwareSpecContractTests

class MyAdapter:
    def run(self, command: str):
        ...

class TestMyImpl(UnitAwareSpecContractTests):
    create_adapter = MyAdapter
```

### TypeScript

```ts
import { defineUnitAwareSpecContractTests } from "./specContract.test";

class MyAdapter {
  run(command: string) {
    return "";
  }
}

defineUnitAwareSpecContractTests("my implementation", () => new MyAdapter());
```
