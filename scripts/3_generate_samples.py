"""
脚本3：生成 5 岗位训练样本（~5000 条）
输入：clean/niosh_clean.json + config/roles.json
输出：data/chemagent_lora_train.jsonl, data/chemagent_lora_val.jsonl
"""
import json, os, random, copy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NIOSH_FILE = os.path.join(BASE_DIR, "clean", "niosh_clean.json")
ROLES_FILE = os.path.join(BASE_DIR, "config", "roles.json")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

random.seed(42)

# ── 装载数据 ──
with open(ROLES_FILE, "r", encoding="utf-8") as f:
    roles = json.load(f)

with open(NIOSH_FILE, "r", encoding="utf-8") as f:
    niosh_data = json.load(f)

print(f"角色: {list(roles.keys())}")
print(f"NIOSH 安全数据: {len(niosh_data)} 条")

# ── 每个角色的模板问题 ──
TEMPLATES = {
    "sales": [
        "客户问{chemical}的价格，怎么报？",
        "竞品也在推{chemical}，怎么应对？",
        "客户说{chemical}比市场价贵，怎么回？",
        "今天主推产品里有{chemical}，帮忙写一段微信话术",
        "客户问{chemical}用在什么场景，怎么介绍？",
        "客户想对比{chemical}和传统原料的区别",
        "{chemical}涨价了，怎么跟客户解释？",
        "客户担心{chemical}的安全风险，怎么打消顾虑？",
        "写一段跟进话术：客户上次询价{chemical}后没回音",
        "客户要{chemical}的报价单和规格书，怎么回复？",
    ],
    "formula": [
        "配方中用到了{chemical}，评估一下原料风险",
        "{chemical}有没有国产替代方案？",
        "这个配方干燥太慢，怀疑是{chemical}的问题",
        "设计一个DOE实验，研究{chemical}添加量对性能的影响",
        "降本10%，能否用便宜原料替换{chemical}？",
        "{chemical}在配方中的最佳用量范围是多少？",
        "评估{chemical}的供应商变更风险",
        "客户投诉涂层附着力差，排查{chemical}的影响",
        "用{chemical}替代进口原料需要做哪些验证？",
        "{chemical}的保质期过了，能否继续使用？",
    ],
    "production": [
        "当前批次用到{chemical}，SOP操作要点是什么？",
        "反应温度异常，{chemical}加料后温度持续上升",
        "{chemical}的投料顺序有没有要求？",
        "班组交接：今天用到{chemical}，需要注意什么？",
        "参数漂移：{chemical}的进料流量波动超过5%",
        "追溯批次异常：怀疑{chemical}批次质量问题",
        "{chemical}的储存温度要求是多少？",
        "产线清洗时{chemical}残留怎么处理？",
        "紧急停线判断：{chemical}泄漏报警触发",
        "生成今日生产摘要：涉及{chemical}的批次情况",
    ],
    "maintenance": [
        "涉及{chemical}的设备检修前需要确认哪些安全事项？",
        "{chemical}输送泵故障，可能原因有哪些？",
        "{chemical}管道阀门泄漏，维修方案是什么？",
        "查询{chemical}相关设备的备件库存",
        "生成{chemical}区域的标准维修工单",
        "{chemical}储罐液位计异常，怎么排查？",
        "{chemical}管线需要动火作业，需要哪些票证？",
        "维修{chemical}泵前必须做哪些隔离措施？",
        "生成本周{chemical}区域点检计划",
        "{chemical}换热器结垢严重，推荐清洗方案",
    ],
    "qc": [
        "来了一批{chemical}原料，入厂需检验哪些项目？",
        "{chemical}的出厂标准和检验指标是什么？",
        "{chemical}的COA与标准不一致，偏差分析怎么做？",
        "产品中{chemical}含量偏高，可能原因和放行建议",
        "核对{chemical}的COA，需要确认哪些关键指标？",
        "这批{chemical}能不能放行？检测值在临界线上",
        "{chemical}的留样复检周期是多久？",
        "{chemical}的VOC检测方法是什么？",
        "客户投诉{chemical}批次质量，如何追溯？",
        "生成{chemical}的质检报告草稿",
    ],
}

# ── 为每个角色生成样本 ──
def build_output(role_id, chemical, niosh_record):
    """根据角色和化学品信息生成结构化 JSON 输出"""
    role = roles[role_id]
    schema = role["output_schema"]
    output = {"role": role_id, "chemical": chemical}

    # 从 NIOSH 提取安全信息作为 evidence
    evidence = []
    if "name" in niosh_record:
        evidence.append(f"化学品: {niosh_record['name']}")
    if "cas" in niosh_record:
        evidence.append(f"CAS号: {niosh_record['cas']}")
    if "rel" in niosh_record:
        evidence.append(f"REL(推荐暴露限值): {niosh_record['rel']}")
    if "pel" in niosh_record:
        evidence.append(f"PEL(允许暴露限值): {niosh_record['pel']}")
    if "idlh" in niosh_record:
        evidence.append(f"IDLH(立即危及生命浓度): {niosh_record['idlh']}")
    if "first_aid" in niosh_record:
        evidence.append(f"急救措施: {niosh_record['first_aid'][:100]}")

    output["evidence"] = evidence

    # 填各角色特定字段
    if role_id == "sales":
        output["customer_intent"] = f"询问{chemical}的价格和应用"
        output["recommended_product"] = [f"含{chemical}的标准产品线", "定制配方产品(需确认需求)"]
        output["quote_strategy"] = ["提供标准报价+批量折扣", "重点突出安全合规优势"]
        output["risk_warnings"] = [f"注意{chemical}的运输存储要求", "价格波动需提示客户"]
        output["wechat_reply"] = f"您好，关于{chemical}我们有多款产品可选，标准品价格在行业中等偏上，但安全合规性有保障。方便的话发一下具体用途，我给您推荐最合适的方案。"

    elif role_id == "formula":
        output["material_review"] = [f"{chemical}的物化性质稳定", f"NIOSH安全数据: {evidence[1] if len(evidence)>1 else '参考标准'}"[:80]]
        output["formula_risks"] = ["相容性需小试验证", f"建议测试{chemical}与现有体系的兼容性"]
        output["substitution_candidates"] = [f"国产{chemical}替代方案(需验证性能)", "同类不同供应商样品对比"]
        output["experiment_plan"] = ["小试: 3个浓度梯度", "中试: 确认生产可行性", "EHS复核"]
        output["must_verify"] = ["小试验证", "EHS复核"]
        output["do_not_claim"] = ["不可声称完全替代"]

    elif role_id == "production":
        output["shift_briefing"] = [f"当前批次使用{chemical}", "投料温度: 常温", "注意反应放热监控"]
        output["operation_checklist"] = ["确认物料批号", "检查设备密封性", "按SOP控制加料速度"]
        output["abnormal_signals"] = ["温度异常上升", "压力波动", "进料流量偏差"]
        output["stop_conditions"] = ["温度超过安全上限立即停线", "泄漏报警触发立即停线"]
        output["escalation_path"] = ["班长 → 车间主任 → 生产部长", "涉及安全同时通知EHS"]

    elif role_id == "maintenance":
        output["fault_hypothesis"] = [f"{chemical}相关设备密封老化", "管道腐蚀/堵塞", "仪表读数漂移"]
        output["pre_job_safety"] = ["隔离", "泄压", "置换", "可燃气检测"]
        output["required_permits"] = ["动火作业票", "受限空间作业票", "高处作业票"]
        output["lockout_tagout"] = [f"{chemical}管道阀门上锁", "断电挂牌", "能量隔离确认"]
        output["spare_parts"] = [f"{chemical}泵机械密封", "垫片套装", "压力表"]
        output["work_order_draft"] = f"工单: {chemical}区域设备检修 - 优先级: 中"

    elif role_id == "qc":
        output["inspection_items"] = ["外观检查", "含量测定", "纯度分析", "水分测试"]
        output["coa_check"] = ["核对CAS号", "核对批号", "核对规格指标"]
        output["deviation_analysis"] = [f"{chemical}检测值与标准值偏差分析", "偏差在允差范围内可让步接收"]
        output["retest_suggestion"] = ["建议复检", "加做第三方检测确认"]
        output["release_risk"] = ["指标在合格范围内", "建议按企业标准确认"]
        output["report_draft"] = f"{chemical}检验报告(草稿): 待确认后签字放行"

    if "evidence" in schema:
        output["evidence"] = evidence

    return output


# ── 生成样本 ──
train_samples = []
val_samples = []

for role_id in roles:
    templates = TEMPLATES[role_id]
    # 每个角色 1000 条 = 100 种化学品 x 10 个问题
    chems = random.sample(niosh_data, min(100, len(niosh_data)))
    
    for chem in chems:
        chem_name = chem.get("name", chem.get("cas", "未知化学品"))
        for tmpl in templates:
            question = tmpl.format(chemical=chem_name)
            output = build_output(role_id, chem_name, chem)
            sample = {
                "instruction": question,
                "input": f"角色: {roles[role_id]['name']}\n化学品: {chem_name}",
                "output": output,
                "role": role_id,
                "cas": chem.get("cas", ""),
            }
            # 8:2 划分训练/验证
            if random.random() < 0.8:
                train_samples.append(sample)
            else:
                val_samples.append(sample)

    print(f"  {role_id}: 生成 {100 * len(templates)} 条")

# ── 保存 ──
def save_jsonl(samples, path):
    with open(path, "w", encoding="utf-8") as f:
        for s in samples:
            # output 如果是 dict 转成 json 字符串
            s = copy.deepcopy(s)
            if isinstance(s["output"], dict):
                s["output"] = json.dumps(s["output"], ensure_ascii=False)
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

train_file = os.path.join(DATA_DIR, "chemagent_lora_train.jsonl")
val_file = os.path.join(DATA_DIR, "chemagent_lora_val.jsonl")

save_jsonl(train_samples, train_file)
save_jsonl(val_samples, val_file)

print(f"\n训练集: {len(train_samples)} 条 → {train_file}")
print(f"验证集: {len(val_samples)} 条 → {val_file}")
print(f"总计: {len(train_samples) + len(val_samples)} 条")
