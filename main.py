from pathlib import Path
from solver.solver import Solver, Board


path1 = Path(__file__).parent / "entry.json"
path2 = Path(__file__).parent / "solver" / "_backup_.json"
solver = Solver(Board.create_from_json(path2 if path2.exists() else path1))

print()
log = solver.solve()

if log:
    log.display_steps()
    print("SOLVED!")
else:
    print("Somehow cannot solve this...")
