import sys
from unit_formula import run_command, Env
env = Env()
print("]2 ->", run_command("evaluate:]2", env))
print("[2 ->", run_command("evaluate:[2", env))
