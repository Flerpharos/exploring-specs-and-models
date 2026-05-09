from unit_formula_harness import assert_transcript
from formula import run_transcript

assert_transcript(
    run_transcript,
    [
        "unit:m",
        "set:X:2",
        "evaluate:X * m"
    ],
    [
        "2.0 m"
    ]
)
print("X * m works!")
