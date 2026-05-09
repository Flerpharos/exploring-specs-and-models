"""Test-harness adapter for unit_formula_harness.

Exposes ``run_transcript`` compatible with the ``RunTranscript`` signature:
    list[str] -> Iterable[str]
"""

from unit_formula import run_session

run_transcript = run_session
