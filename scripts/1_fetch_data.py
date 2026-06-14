"""
脚本1：爬取 NIOSH Pocket Guide 公开安全数据
输出：raw/niosh_raw.json
"""
import json, re, time, urllib.request, urllib.error, os

NIOSH_LIST_URL = "https://www.cdc.gov/niosh/npg/npgd-cas.html"
NIOSH_DETAIL_BASE = "https://www.cdc.gov/niosh/npg/npgd"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "raw", "niosh_raw.json")
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

print("=" * 60)
print("ChemAgent 数据采集 — NIOSH Pocket Guide")
print("=" * 60)

# ── Step 1: 获取化学品列表 ──
print("\n[1/3] 获取化学品列表...")
try:
    req = urllib.request.Request(NIOSH_LIST_URL, headers={"User-Agent": "ChemAgent/1.0"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
except Exception as e:
    print(f"  列表获取失败: {e}")
    print("  使用内置种子数据作为兜底...")
    html = ""

# 提取 CAS 号
cas_pattern = re.compile(r'(\d{1,7}-\d{2}-\d)')
cas_list = list(set(cas_pattern.findall(html)))

if len(cas_list) < 50:
    print(f"  仅找到 {len(cas_list)} 个CAS号，补充种子数据...")
    seed_cas = [
        "67-64-1","67-56-1","71-43-2","108-88-3","75-05-8","67-63-0",
        "100-42-5","75-09-2","107-06-2","79-01-6","127-18-4","56-23-5",
        "75-15-0","74-87-3","74-83-9","75-21-8","107-21-1","108-95-2",
        "1310-73-2","7664-41-7","50-00-0","91-20-3","106-99-0","78-93-3",
        "108-10-1","624-83-9","101-68-8","1309-37-1","1314-13-2",
        "1309-48-4","13463-67-7","144-62-7","75-07-0","123-86-4",
        "141-78-6","109-99-9","110-54-3","64-17-5",
        "110-82-7","107-15-3","100-41-4","95-47-6",
        "108-38-3","106-42-3","1330-20-7","7664-93-9","7697-37-2"
    ]
    cas_list = list(set(cas_list + seed_cas))

print(f"  共 {len(cas_list)} 个唯一 CAS 号")

# ── Step 2: 爬取每个化学品详细信息 ──
print("\n[2/3] 爬取化学品详细信息...")
records = []
failures = 0

for i, cas in enumerate(cas_list[:200]):
    clean_cas = cas.replace("-", "")
    url = f"{NIOSH_DETAIL_BASE}/npgd{clean_cas}.html"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ChemAgent/1.0"})
        detail_html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="replace")

        record = {"cas": cas, "source": "NIOSH Pocket Guide", "source_url": url}

        rel_match = re.search(r'REL\s*[：:]\s*([^<\n]+)', detail_html, re.IGNORECASE)
        if rel_match: record["rel"] = rel_match.group(1).strip()

        pel_match = re.search(r'PEL\s*[：:]\s*([^<\n]+)', detail_html, re.IGNORECASE)
        if pel_match: record["pel"] = pel_match.group(1).strip()

        idlh_match = re.search(r'IDLH\s*[：:]\s*([^<\n]+)', detail_html, re.IGNORECASE)
        if idlh_match: record["idlh"] = idlh_match.group(1).strip()

        name_match = re.search(r'<title>([^<]+)</title>', detail_html)
        if name_match: record["name"] = name_match.group(1).strip().replace("NIOSH Pocket Guide to Chemical Hazards - ", "")

        first_aid_match = re.search(r'First Aid[^<]*</h\d>(.*?)(?:</div>|</p>)', detail_html, re.IGNORECASE | re.DOTALL)
        if first_aid_match: record["first_aid"] = re.sub(r'<[^>]+>', ' ', first_aid_match.group(1)).strip()

        if any(k in record for k in ["rel","pel","idlh","first_aid"]):
            records.append(record)

        if (i+1) % 20 == 0:
            print(f"  进度: {i+1}/{min(200,len(cas_list))} ({len(records)} 条有效)")

    except urllib.error.HTTPError as e:
        failures += 1
    except Exception as e:
        failures += 1

    time.sleep(0.3)

print(f"  完成: {len(records)} 条有效记录, {failures} 条失败")

# ── Step 3: 保存 ──
print(f"\n[3/3] 保存到 {OUTPUT_FILE}")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"\n完成！共 {len(records)} 条 NIOSH 安全记录")
