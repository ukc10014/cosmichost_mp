#!/usr/bin/env python3
"""
Runner script: Sonnet 4.5 ECL 90% scenario evaluation (n=3)
"""
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Mock get_ipython for notebook-converted code
class FakeIPython:
    def system(self, cmd):
        pass
    def run_line_magic(self, *a, **kw):
        pass

def get_ipython():
    return FakeIPython()

import builtins
builtins.get_ipython = get_ipython

with open("/tmp/cosmichost_mp_converted.py", "r") as f:
    lines = f.readlines()

code = "".join(lines[:5596])
code = code.replace(
    'print("fallback" in inspect.getsource(parse_ranking_response))',
    '# skipped inspect.getsource debug check'
)

ns = {"__name__": "__main__", "__file__": "cosmichost_mp.py", "get_ipython": get_ipython}
exec(compile(code, "cosmichost_mp.py", "exec"), ns)

print("\n" + "="*60)
print("Starting Sonnet 4.5 ECL 90% evaluation (n=3)")
print("="*60 + "\n")

result_path = ns["run_once"](
    model_name="claude-sonnet-4-5",
    scenarios=ns["SCENARIOS"],
    conditions=["eclpilled_90ch"],
    num_runs=3,
    temperature=1.0,
    system_prompt_style="consider",
    include_rationale=True,
    exclude_option_types=["proceduralist"],
    test_scenarios=True
)

print(f"\nResult file: {result_path}")
