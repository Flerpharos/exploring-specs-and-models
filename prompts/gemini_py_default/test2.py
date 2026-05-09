from unit_formula_harness import assert_transcript
from formula import run_transcript

assert_transcript(
    run_transcript,
    [
        "unit:m",
        "evaluate:2 m^2^3",
        "evaluate:-2^2",
        "evaluate:-(2^2)",
        "unit:s",
        "evaluate:m_s",
        "set:X:2",
        "evaluate:X m"
    ],
    [
        "Error: invalid formula.",
        "4.0 1",
        "-4.0 1",
        "Error: unknown unit m_s.",
        "Error: invalid formula."
    ]
)
print("More tests passed.")
