import sys
from unit_formula import run_command, Env
env = Env()
run_command("unit:m", env)
print("2 m^2^3 ->", run_command("evaluate:2 m^2^3", env))
print("2 (m)^3 ->", run_command("evaluate:2 (m)^3", env))
print("(2 m)^3 ->", run_command("evaluate:(2 m)^3", env))
