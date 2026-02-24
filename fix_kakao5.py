f = "/home/blueswell/bs_dashboard_flask.py"
lines = open(f, "r", encoding="utf-8").readlines()

# 470번 줄 근처 확인 (0-indexed이므로 469)
print("=== 465~485번 줄 ===")
for i in range(464, min(485, len(lines))):
    print(f"{i+1}: {lines[i].rstrip()}")

print("\n=== 600~615번 줄 ===")
for i in range(599, min(615, len(lines))):
    print(f"{i+1}: {lines[i].rstrip()}")

print("\n=== initMap 포함 줄 ===")
for i, line in enumerate(lines):
    if "initMap" in line:
        print(f"{i+1}: {line.rstrip()}")
