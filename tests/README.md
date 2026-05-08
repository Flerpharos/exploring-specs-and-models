# Test Harness

This directory contains reusable harness infrastructure for the Unit-Aware
Formula CLI specification. It does not contain the conformance test suite yet.

The harness is transcript-based. A compliant implementation supplies an adapter
that starts a fresh empty session, feeds command lines in order, and returns only
the emitted output lines.

Adapters may wrap any implementation surface:

- an in-process object or function
- a library API
- a subprocess
- a model endpoint
- any other transport that preserves the spec-visible session behavior

The harness must not require prompts, stdout versus stderr behavior, command
echoing, process lifecycle details, parser internals, AST shape, class names, or
module layout.

## Python

Add `tests/python` to `PYTHONPATH`, then import:

```python
from unit_formula_harness import RunTranscript, assert_single_evaluation
```

The synchronous adapter contract is:

```python
run_transcript(commands: list[str]) -> Iterable[str]
```

Async adapters can use `assert_transcript_async` and may return either an
`Iterable[str]`, an `AsyncIterable[str]`, or an awaitable of either.

Example shape for an implementation-owned pytest fixture:

```python
import pytest


@pytest.fixture
def run_transcript():
    def run(commands: list[str]) -> list[str]:
        session = create_fresh_session()
        output: list[str] = []
        for command in commands:
            output.extend(session.handle_command_line(command))
        return output

    return run
```

## TypeScript

Import the neutral helper module:

```ts
import type { RunTranscript } from "./tests/typescript/unitFormulaHarness";
import { assertSingleEvaluation } from "./tests/typescript/unitFormulaHarness";
```

The adapter contract is:

```ts
type RunTranscript =
  (commands: string[]) => Iterable<string> | AsyncIterable<string> |
  PromiseLike<Iterable<string> | AsyncIterable<string>>;
```

Example adapter shape:

```ts
const runTranscript: RunTranscript = async (commands) => {
  const session = createFreshSession();
  const output: string[] = [];
  for (const command of commands) {
    const emitted = await session.handleCommandLine(command);
    output.push(...emitted);
  }
  return output;
};
```

## Assertion Semantics

- Successful evaluation lines are parsed as `<magnitude> <unit>`.
- Magnitudes are compared numerically with configurable finite tolerances.
- Serialized units are compared exactly.
- Required error lines are compared exactly when using the exact error helpers.
- Ambiguous spec cases should use only helpers that match the behavior the spec
  actually requires.
- Numeric helpers use the host language's finite numeric type. Future tests for
  extreme precision or range should use raw line assertions or custom parsing.
- The TypeScript harness is checked with the `tests/typescript/tsconfig.json`
  settings, including ES2018 library/runtime assumptions.
