from unit_formula_harness import assert_transcript, EvaluationLine
from formula import run_transcript

assert_transcript(
    run_transcript,
    [
        "unit:m",
        "unit:cm",
        "relate:cm:m:0.01 m",
        "evaluate:1 m:cm"
    ],
    [
        "100.0 cm"
    ]
)
print("Basic functionality works.")
