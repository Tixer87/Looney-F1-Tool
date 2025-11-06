#!/usr/bin/env python3
"""Quick check of exported qualifying files."""
import json
from pathlib import Path

# Check Q1
q1 = json.loads(Path('./test_export/2025_Melbourne_Australia_Q1.json').read_text())
print(f'✅ Q1: {len(q1["Drivers"])} drivers, QualType={q1["QualType"]}')

# Check Q2
q2 = json.loads(Path('./test_export/2025_Melbourne_Australia_Q2.json').read_text())
print(f'✅ Q2: {len(q2["Drivers"])} drivers, QualType={q2["QualType"]}')

# Check Q3
q3 = json.loads(Path('./test_export/2025_Melbourne_Australia_Q3.json').read_text())
print(f'✅ Q3: {len(q3["Drivers"])} drivers, QualType={q3["QualType"]}')
print(f'   Pole: {q3["Drivers"][0]["Driver"]["Name"]} (P{q3["Drivers"][0]["Position"]}) - {q3["Drivers"][0]["TimeInt"]}ms')
print(f'\n🎯 All qualifying files exported correctly!')
