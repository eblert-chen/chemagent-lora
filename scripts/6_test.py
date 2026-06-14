import torch
"""
ChemAgent LoRA 模型推理测试
用法: python test_model.py
"""
import json, time

MODEL_PATH = "/home/administratoruser/chemagent/output/chemagent_lora"

# 5 个岗位各一条测试
TESTS = [
    {
        "role": "销售支持",
        "question": "客户说价格太贵，怎么回？客户在比价，竞品报价低20%。",
    },
    {
        "role": "配方研发",
        "question": "这个原料能不能替代？客户要求降本15%，目前的进口固化剂太贵。",
    },
    {
        "role": "产线操作",
        "question": "反应釜温度持续上升到 189°C，催化剂已加完，怎么处理？",
    },
    {
        "role": "设备维修",
        "question": "离心泵检修前需要确认哪些安全事项？",
    },
    {
        "role": "质量检验",
        "question": "这批产品 VOC 检测值 420g/L，标准要求 ≤400g/L，能不能放行？",
    },
]


def load_model():
    print("加载模型...")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    print(f"  模型加载完成，显存占用: {torch.cuda.max_memory_allocated()/1024**3:.1f}GB")
    return model, tokenizer


def test_one(model, tokenizer, role, question):
    # 短期 system prompt——格式已被 LoRA 内化
    system = (
        f"你是 ChemAgent {role} Agent。输出严格 JSON。"
        "涉及安全操作提示隔离/挂牌/作业票。涉及放行标准提示企业复核。"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]

    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer([text], return_tensors="pt").to(model.device)

    start = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=400,
            temperature=0.2,
            do_sample=True,
            top_p=0.9,
        )
    elapsed = time.time() - start

    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
    )

    # 尝试解析 JSON
    try:
        parsed = json.loads(response)
        is_json = True
    except json.JSONDecodeError:
        # 尝试提取 JSON 块
        import re
        match = re.search(r"\{[\s\S]*\}", response)
        try:
            parsed = json.loads(match.group(0)) if match else None
            is_json = parsed is not None
        except json.JSONDecodeError:
            parsed = None
            is_json = False

    return {
        "role": role,
        "question": question,
        "is_json": is_json,
        "keys": list(parsed.keys())[:8] if parsed else [],
        "time": f"{elapsed:.1f}s",
        "raw": response[:200],
    }


def main():
    try:
        import torch  # noqa
    except ImportError:
        print("PyTorch 未安装。请先: pip install torch")
        return

    model, tokenizer = load_model()

    print("\n" + "=" * 60)
    print("ChemAgent LoRA 推理测试")
    print("=" * 60)

    results = []
    for i, test in enumerate(TESTS):
        print(f"\n[{i+1}/5] {test['role']}: {test['question'][:50]}...")
        result = test_one(model, tokenizer, **test)
        results.append(result)
        print(f"  JSON: {'✅' if result['is_json'] else '❌'}  "
              f"字段: {result['keys']}  耗时: {result['time']}")

    # 汇总
    json_rate = sum(1 for r in results if r["is_json"]) / len(results)
    avg_time = sum(float(r["time"].replace("s", "")) for r in results) / len(results)
    print(f"\n{'='*60}")
    print(f"汇总: JSON命中率 {json_rate*100:.0f}%  |  平均耗时 {avg_time:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
