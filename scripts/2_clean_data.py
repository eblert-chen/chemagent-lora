"""
脚本2：清洗 NIOSH 数据 — 去重、格式化、校验
输入：raw/niosh_raw.json
输出：clean/niosh_clean.json, clean/niosh_dropped.json, clean/cleaning_report.txt
"""
import json, re, os

INPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "raw", "niosh_raw.json")
CLEAN_FILE = os.path.join(os.path.dirname(__file__), "..", "clean", "niosh_clean.json")
DROPPED_FILE = os.path.join(os.path.dirname(__file__), "..", "clean", "niosh_dropped.json")
REPORT_FILE = os.path.join(os.path.dirname(__file__), "..", "clean", "cleaning_report.txt")
os.makedirs(os.path.dirname(CLEAN_FILE), exist_ok=True)

print("=" * 60)
print("ChemAgent 数据清洗 — NIOSH")
print("=" * 60)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)
print(f"\n原始数据: {len(raw)} 条")

stats = {"total": len(raw), "deduped": 0, "incomplete": 0, "encoding_fixed": 0, "html_cleaned": 0}

# ── 1. CAS 号格式统一 ──
def normalize_cas(cas):
    m = re.match(r'^(\d{1,7})-(\d{2})-(\d)$', str(cas))
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    digits = re.sub(r'[^0-9]', '', str(cas))
    if len(digits) >= 5:
        return f"{digits[:-3]}-{digits[-3:-1]}-{digits[-1]}"
    return cas

for r in raw:
    if "cas" in r:
        old = r["cas"]
        r["cas"] = normalize_cas(old)
        if old != r["cas"]:
            stats["encoding_fixed"] += 1

# ── 2. 去重 ──
seen_cas = {}
cleaned = []
dropped = []
for r in raw:
    cas = r.get("cas", "")
    if cas in seen_cas:
        existing = seen_cas[cas]
        if len(r) > len(existing):
            dropped.append({"cas": cas, "reason": "重复(保留更完整版本)", "dropped_record": existing})
            seen_cas[cas] = r
        else:
            dropped.append({"cas": cas, "reason": "重复", "dropped_record": r})
            stats["deduped"] += 1
    else:
        seen_cas[cas] = r

# ── 3. 清理 HTML 标签 ──
def strip_html(text):
    if not text: return text
    old = text
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if old != text: stats["html_cleaned"] += 1
    return text

result = []
for r in seen_cas.values():
    for k, v in list(r.items()):
        if isinstance(v, str):
            r[k] = strip_html(v)
    has_safety = any(k in r for k in ["rel", "pel", "idlh"])
    has_first_aid = "first_aid" in r and len(r.get("first_aid", "")) > 20
    r["data_completeness"] = "full" if (has_safety and has_first_aid) else "partial"
    if r["data_completeness"] == "partial":
        stats["incomplete"] += 1
    result.append(r)

# ── 4. 保存 ──
with open(CLEAN_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
with open(DROPPED_FILE, "w", encoding="utf-8") as f:
    json.dump(dropped, f, ensure_ascii=False, indent=2)

report = f"""NIOSH 数据清洗报告
═══════════════════════════
原始数据: {stats['total']} 条
去重: {stats['deduped']} 条
格式修复: {stats['encoding_fixed']} 条
HTML清理: {stats['html_cleaned']} 条
部分字段缺失: {stats['incomplete']} 条 (已标注 data_completeness=partial)
───────────────────────────
输出: {len(result)} 条
丢弃: {len(dropped)} 条
"""
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(report)

print(report)
print(f"清洗后数据: {CLEAN_FILE}")
print(f"清洗报告: {REPORT_FILE}")
