import re
src = open("frontend/app.js").read()
clean = re.sub(r"//[^\n]*", "", src)
clean = re.sub(r"/\*[\s\S]*?\*/", "", clean)
clean = re.sub(r"'[^'\\\n]*(?:\\.[^'\\\n]*)*'", "''", clean)
clean = re.sub(r'"[^"\\\n]*(?:\\.[^"\\\n]*)*"', '""', clean)
clean = re.sub(r"`[^`\\]*(?:\\.[^`\\]*)*`", "``", clean, flags=re.DOTALL)
print(f"Open  {{: {clean.count('{')}")
print(f"Close }}: {clean.count('}')}")
print(f"Diff: {clean.count('{') - clean.count('}')}")
depth = 0
line = 1
orphan_line = None
for ch in clean:
    if ch == "\n":
        line += 1
    elif ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
        if depth < 0 and orphan_line is None:
            orphan_line = line
print(f"Final depth: {depth}")
if orphan_line:
    print(f"Orphan }} found near line {orphan_line}")
