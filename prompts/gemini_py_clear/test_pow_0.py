import sys
from unit_formula import run_command, Env
env = Env()
print("0 ^ -1 ->", run_command("evaluate:0 ^ -1", env))
