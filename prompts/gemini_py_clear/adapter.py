from unit_formula import run_command, Env
from typing import Iterable

def run_transcript(commands: list[str]) -> Iterable[str]:
    """Adapter for unit_formula_harness.py."""
    env = Env()
    output = []
    for cmd in commands:
        if not cmd.strip():
            continue
        # Backup environment in case of failure
        env_backup = Env()
        env_backup.units = set(env.units)
        env_backup.variables = dict(env.variables)
        env_backup.relationships = dict(env.relationships)
        
        res = run_command(cmd, env)
        
        if res is not None and res.startswith("Error:"):
            # Restore environment on error
            env.units = env_backup.units
            env.variables = env_backup.variables
            env.relationships = env_backup.relationships
            
        if res is not None:
            output.append(res)
    return output
