import json, sys
from collections import Counter

train_data, val_data = [], []

with open(r'E:\project\huayangyunke\chem\chemagent\data\chemagent_lora_train.jsonl', encoding='utf-8') as f:
    for line in f:
        if line.strip(): train_data.append(json.loads(line))

with open(r'E:\project\huayangyunke\chem\chemagent\data\chemagent_lora_val.jsonl', encoding='utf-8') as f:
    for line in f:
        if line.strip(): val_data.append(json.loads(line))

all_data = train_data + val_data
total = len(all_data)

print('=== 数据自检报告 ===')
print(f'训练集: {len(train_data)} / 4000', 'OK' if len(train_data)>=4000 else '不足')
print(f'验证集: {len(val_data)} / 1000', 'OK' if len(val_data)>=1000 else '不足')
print(f'总计:   {total} / 5000', 'OK' if total>=5000 else '不足')

role_counts = Counter()
for item in all_data:
    role_counts[item.get('role', 'unknown')] += 1

print('\n--- 角色分布 ---')
for r in ['sales','formula','production','maintenance','qc']:
    c = role_counts.get(r, 0)
    print(f'  {r}: {c}', 'OK' if c>=1000 else '不足')

chems = set()
for item in all_data:
    out = item.get('output', '{}')
    if isinstance(out, str):
        try: out = json.loads(out)
        except: continue
    c = out.get('chemical', '')
    if c: chems.add(c)

print(f'\n--- 化学品覆盖 ---')
print(f'  种类: {len(chems)} / 100', 'OK' if len(chems)>=100 else '不足')

valid = sum(1 for item in all_data 
    if isinstance((out:=item.get('output','{}')), str) and (lambda: json.loads(out) or True)())
valid = 0
for item in all_data:
    out = item.get('output', '{}')
    if isinstance(out, str):
        try: json.loads(out); valid += 1
        except: pass
    else: valid += 1

print(f'\n--- 数据质量 ---')
print(f'  JSON有效: {valid}/{total}', 'OK' if valid==total else '有问题')
print(f'  问题模板: {len(set(item.get("instruction","")[:30] for item in all_data))}')

print(f'\n--- 结论 ---')
short = 5000 - total
if short <= 0:
    print('数据充分，可直接训练')
elif total >= 2000:
    print(f'数据量 {total}/5000，尚可接受但缺 {short} 条，建议先补充化学品再跑训练')
else:
    print(f'数据严重不足 ({total}/5000)，无法训练')
