"""Transcript-level harness helpers for Unit-Aware Formula CLI implementations.

This package intentionally contains no conformance cases. Implementations provide
an adapter that runs command lines in a fresh session and returns emitted lines;
future tests can use the helpers here to assert only spec-visible behavior.
"""

from __future__ import annotations

from collections.abc import AsyncIterable, Awaitable, Callable, Iterable, Sequence
from dataclasses import dataclass
from inspect import isawaitable
from math import isclose, isfinite
import re

TranscriptOutput = Iterable[str]
RunTranscript = Callable[[list[str]], TranscriptOutput]
AsyncTranscriptOutput = TranscriptOutput | AsyncIterable[str]
AsyncRunTranscript = Callable[
    [list[str]], AsyncTranscriptOutput | Awaitable[AsyncTranscriptOutput]
]

DEFAULT_RELATIVE_TOLERANCE = 1e-9
DEFAULT_ABSOLUTE_TOLERANCE = 1e-12

_NUMBER_PATTERN = (
    r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
)
_EVALUATION_LINE_PATTERN = re.compile(
    rf"^(?P<magnitude>{_NUMBER_PATTERN}) (?P<unit>\S+)$"
)


@dataclass(frozen=True)
class EvaluationLine:
    """Parsed form of a successful evaluate output line."""

    raw: str
    magnitude_text: str
    magnitude: float
    unit: str


@dataclass(frozen=True)
class TranscriptCase:
    """Data shape for future transcript-based conformance scenarios."""

    name: str
    commands: tuple[str, ...]
    expected_output: tuple[str, ...]
    description: str | None = None


def parse_evaluation_line(line: str) -> EvaluationLine:
    """Parse ``<magnitude> <unit>`` from a successful evaluate output line.

    The parser requires exactly one ASCII space between magnitude and unit. It
    does not reinterpret units; unit comparison helpers compare the serialized
    unit string exactly.
    """

    if not isinstance(line, str):
        raise ValueError(f"evaluation output line must be str, got {type(line)!r}")

    match = _EVALUATION_LINE_PATTERN.match(line)
    if match is None:
        raise ValueError(
            f"expected evaluation output '<magnitude> <unit>', got {line!r}"
        )

    magnitude_text = match.group("magnitude")
    magnitude = float(magnitude_text)
    if not isfinite(magnitude):
        raise ValueError(f"evaluation magnitude must be finite, got {magnitude_text!r}")

    return EvaluationLine(
        raw=line,
        magnitude_text=magnitude_text,
        magnitude=magnitude,
        unit=match.group("unit"),
    )


def assert_lines_equal(
    actual: Iterable[str],
    expected: Sequence[str],
    *,
    context: str | None = None,
) -> list[str]:
    """Assert exact emitted-line equality and return the actual lines as a list."""

    actual_lines = _coerce_lines(actual, label="actual")
    expected_lines = list(expected)
    if actual_lines != expected_lines:
        prefix = f"{context}: " if context else ""
        raise AssertionError(
            f"{prefix}emitted lines differ\n"
            f"expected: {expected_lines!r}\n"
            f"actual:   {actual_lines!r}"
        )
    return actual_lines


def assert_transcript(
    run_transcript: RunTranscript,
    commands: Sequence[str],
    expected_output: Sequence[str],
    *,
    context: str | None = None,
) -> list[str]:
    """Run a transcript adapter and assert exact emitted output lines."""

    actual = run_transcript(list(commands))
    return assert_lines_equal(actual, expected_output, context=context)


async def assert_transcript_async(
    run_transcript: AsyncRunTranscript,
    commands: Sequence[str],
    expected_output: Sequence[str],
    *,
    context: str | None = None,
) -> list[str]:
    """Run a sync or async transcript adapter and assert exact output lines."""

    actual = run_transcript(list(commands))
    if isawaitable(actual):
        actual = await actual
    actual_lines = await _coerce_lines_async(actual, label="actual")
    return assert_lines_equal(actual_lines, expected_output, context=context)


def assert_transcript_case(
    run_transcript: RunTranscript,
    case: TranscriptCase,
) -> list[str]:
    """Run and assert a ``TranscriptCase``."""

    return assert_transcript(
        run_transcript,
        case.commands,
        case.expected_output,
        context=case.name,
    )


def assert_evaluation_line(
    line: str,
    *,
    expected_magnitude: float,
    expected_unit: str,
    rel_tol: float = DEFAULT_RELATIVE_TOLERANCE,
    abs_tol: float = DEFAULT_ABSOLUTE_TOLERANCE,
) -> EvaluationLine:
    """Assert numeric magnitude equivalence and exact serialized unit text."""

    parsed = parse_evaluation_line(line)
    _validate_tolerance(rel_tol, label="rel_tol")
    _validate_tolerance(abs_tol, label="abs_tol")

    if not isfinite(expected_magnitude):
        raise AssertionError(
            f"expected magnitude must be finite, got {expected_magnitude!r}"
        )

    if not isclose(
        parsed.magnitude,
        expected_magnitude,
        rel_tol=rel_tol,
        abs_tol=abs_tol,
    ):
        raise AssertionError(
            f"magnitude differs for {line!r}: "
            f"expected {expected_magnitude!r}, got {parsed.magnitude!r}"
        )

    if parsed.unit != expected_unit:
        raise AssertionError(
            f"unit differs for {line!r}: expected {expected_unit!r}, "
            f"got {parsed.unit!r}"
        )

    return parsed


def assert_single_evaluation(
    lines: Iterable[str],
    *,
    expected_magnitude: float,
    expected_unit: str,
    rel_tol: float = DEFAULT_RELATIVE_TOLERANCE,
    abs_tol: float = DEFAULT_ABSOLUTE_TOLERANCE,
) -> EvaluationLine:
    """Assert a transcript emitted exactly one successful evaluate line."""

    output = _coerce_lines(lines, label="actual")
    if len(output) != 1:
        raise AssertionError(f"expected exactly one output line, got {output!r}")

    return assert_evaluation_line(
        output[0],
        expected_magnitude=expected_magnitude,
        expected_unit=expected_unit,
        rel_tol=rel_tol,
        abs_tol=abs_tol,
    )


def assert_error_line(line: str, expected_error: str) -> None:
    """Assert an exact required error line."""

    if line != expected_error:
        raise AssertionError(f"expected error {expected_error!r}, got {line!r}")


def assert_single_error(lines: Iterable[str], expected_error: str) -> None:
    """Assert a transcript emitted exactly one exact required error line."""

    output = _coerce_lines(lines, label="actual")
    if len(output) != 1:
        raise AssertionError(f"expected exactly one error line, got {output!r}")
    assert_error_line(output[0], expected_error)


def assert_error_prefix(line: str) -> None:
    """Assert only the common spec error prefix for cases with flexible details."""

    if not line.startswith("Error:"):
        raise AssertionError(f"expected line to start with 'Error:', got {line!r}")


def _coerce_lines(lines: Iterable[str], *, label: str) -> list[str]:
    if isinstance(lines, str):
        raise AssertionError(f"{label} lines must be an iterable of str, got str")

    coerced = list(lines)
    for index, line in enumerate(coerced):
        if not isinstance(line, str):
            raise AssertionError(
                f"{label} line {index} must be str, got {type(line)!r}"
            )
    return coerced


async def _coerce_lines_async(
    lines: AsyncTranscriptOutput, *, label: str
) -> list[str]:
    if isinstance(lines, str):
        raise AssertionError(f"{label} lines must be an iterable of str, got str")

    if isinstance(lines, AsyncIterable):
        coerced: list[str] = []
        index = 0
        async for line in lines:
            if not isinstance(line, str):
                raise AssertionError(
                    f"{label} line {index} must be str, got {type(line)!r}"
                )
            coerced.append(line)
            index += 1
        return coerced

    return _coerce_lines(lines, label=label)


def _validate_tolerance(value: float, *, label: str) -> None:
    if not isfinite(value) or value < 0:
        raise AssertionError(f"{label} must be finite and nonnegative, got {value!r}")


__all__ = [
    "DEFAULT_ABSOLUTE_TOLERANCE",
    "DEFAULT_RELATIVE_TOLERANCE",
    "AsyncRunTranscript",
    "AsyncTranscriptOutput",
    "EvaluationLine",
    "RunTranscript",
    "TranscriptOutput",
    "TranscriptCase",
    "assert_error_line",
    "assert_error_prefix",
    "assert_evaluation_line",
    "assert_lines_equal",
    "assert_single_error",
    "assert_single_evaluation",
    "assert_transcript",
    "assert_transcript_async",
    "assert_transcript_case",
    "parse_evaluation_line",
]
