import sys
from mypy import api

# Run mypy programmatically on the repository root, ignoring missing imports.
# We exclude 'llmnova-core' (invalid package name) and 'backend' (duplicate
# module name `main.py`) to avoid errors that stop a full repo scan.
args = ['.', '--ignore-missing-imports', '--exclude', 'llmnova-core|backend']

result = api.run(args)
stdout, stderr, exit_status = result
if stdout:
    print("STDOUT:\n" + stdout)
if stderr:
    print("STDERR:\n" + stderr, file=sys.stderr)
sys.exit(exit_status)
