"""批量生成 AI 训练样本（10线程并发）"""
import json, requests, re, os, time
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = 'sk-edf00fbbd4ea4c73a31bac8f4a0d4f62'
API_URL = 'https://api.deepseek.com/v1/chat/completions'
PROXIES = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
BASE = r'E:\project\huayangyunke\chem\chemagent'

with open(os.path.join(BASE, 'config', 'roles.json'), encoding='utf-8') as f:
    roles = json.load(f)
with open(os.path.join(BASE, 'clean', 'niosh_clean.json'), encoding='utf-8') as f:
    chems = json.load(f)

PER_ROLE = 100  # 每个角色 100 条
results = []
lock = __import__('threading').Lock()

def gen_one(role_id, task_id):
    chem = chems[task_id % len(chems)]
    role = roles[role_id]
    q = role['sample_questions'][task_id % len(role['sample_questions'])]
    cn = chem.get('name', 'unknown')
    
    prompt = ('你是一个化工' + role['name'] + 'Agent。' + role['system_prompt']
        + '\n输出JSON：' + json.dumps(role['output_schema'], ensure_ascii=False)
        + '\n问题：' + q + '\n化学品：' + cn + '（CAS ' + chem.get('cas','') + '）\n只输出JSON。')
    
    try:
        r = requests.post(API_URL, json={
            'model': 'deepseek-chat',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.8, 'max_tokens': 800,
        }, headers={'Authorization': 'Bearer ' + API_KEY},
        proxies=PROXIES, timeout=60)
        if r.status_code != 200:
            return None
        content = r.json()['choices'][0]['message']['content']
        m = re.search(r'\{[\s\S]*\}', content)
        if m and json.loads(m.group(0)):
            return {'instruction': q, 'input': '角色: ' + role['name'] + '\n化学品: ' + cn,
                'output': m.group(0), 'role': role_id, 'cas': chem.get('cas',''), 'source': 'deepseek'}
    except:
        return None

tasks = [(role_id, i) for role_id in roles for i in range(PER_ROLE)]
total_tasks = len(tasks)
print(f'并发生成 {total_tasks} 条（10线程，每角色 {PER_ROLE} 条）...', flush=True)

with ThreadPoolExecutor(max_workers=10) as pool:
    futures = [pool.submit(gen_one, t[0], t[1]) for t in tasks]
    done = 0
    for f in as_completed(futures):
        r = f.result()
        done += 1
        if r:
            with lock:
                results.append(r)
        if done % 100 == 0:
            print(f'  进度: {done}/{total_tasks} 成功 {len(results)}', flush=True)

out = os.path.join(BASE, 'data', 'chemagent_ai_generated.jsonl')
with open(out, 'w', encoding='utf-8') as f:
    for s in results:
        f.write(json.dumps(s, ensure_ascii=False) + '\n')
print(f'\n完成！共 {len(results)} 条 AI 样本 (成功率 {len(results)*100//total_tasks}%)', flush=True)
