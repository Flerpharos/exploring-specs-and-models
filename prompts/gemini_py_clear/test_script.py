import sys
from unit_formula import run_command, Env

def run_transcript(commands: list[str]) -> list[str]:
    env = Env()
    output = []
    for cmd in commands:
        if not cmd.strip():
            continue
        env_backup = Env()
        env_backup.units = set(env.units)
        env_backup.variables = dict(env.variables)
        env_backup.relationships = dict(env.relationships)
        
        res = run_command(cmd, env)
        
        if res is not None and res.startswith("Error:"):
            env.units = env_backup.units
            env.variables = env_backup.variables
            env.relationships = env_backup.relationships
            
        if res is not None:
            output.append(res)
    return output

if __name__ == "__main__":
    from unit_formula_harness import assert_transcript_case, TranscriptCase
    cases = [
        TranscriptCase(
            name="basic_unit_eval",
            commands=[
                "unit:m",
                "unit:s",
                "evaluate:1 m/s"
            ],
            expected_output=[
                "1.0 m/s"
            ]
        ),
        TranscriptCase(
            name="basic_relation_eval",
            commands=[
                "unit:m",
                "unit:cm",
                "relate:cm:m:0.01 m",
                "evaluate:1 m:cm",
                "evaluate:100 cm:m"
            ],
            expected_output=[
                "100.0 cm",
                "1.0 m"
            ]
        ),
        TranscriptCase(
            name="variable_eval",
            commands=[
                "unit:m",
                "set:X:2 m",
                "evaluate:X * 3"
            ],
            expected_output=[
                "6.0 m"
            ]
        ),
        TranscriptCase(
            name="error_handling",
            commands=[
                "evaluate:1 / 0",
                "evaluate:1 m + 1 s"
            ],
            expected_output=[
                "Error: division by zero.",
                "Error: unknown unit m."
            ]
        ),
        TranscriptCase(
            name="error_conversion",
            commands=[
                "unit:m",
                "unit:s",
                "evaluate:1 m + 1 s"
            ],
            expected_output=[
                "Error: cannot convert s to m."
            ]
        )
    ]
    for case in cases:
        print(f"Running {case.name}...")
        assert_transcript_case(run_transcript, case)
    print("All tests passed!")
