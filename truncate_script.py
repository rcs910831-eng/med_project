import os
import sys

path = '전부_코드화_데이터통합시스템.py'
if not os.path.exists(path):
    print(f"File not found: {path}")
    sys.exit(1)

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Original lines: {len(lines)}")
truncated = lines[:1450]
print(f"Truncated lines: {len(truncated)}")

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(truncated)

print("Truncation complete.")
