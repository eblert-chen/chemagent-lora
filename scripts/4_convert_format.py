"""
把 {instruction, input, output} 格式转成 LLaMA-Factory ShareGPT 格式
用法: python convert_data.py --input train.jsonl --output converted.jsonl
"""
import json, argparse, sys

SYSTEM_PROMPT = (
    "你是 ChemAgent 化工行业 AI 助手。"
    "输出严格 JSON 格式，不承诺未经验证的性能，不替代企业标准和法规。"
    "涉及安全操作时必须提示隔离/挂牌/作业票。"
)


def convert(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    converted = []
    skipped = 0
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue

        # 支持三种输入格式
        if "messages" in item:
            # 已经是 ShareGPT 格式，直接保留
            converted.append(item)
            continue

        instruction = item.get("instruction", "")
        user_input = item.get("input", "")
        output = item.get("output", "")

        # 拼接用户消息
        user_content = instruction
        if user_input:
            user_content += "\n" + user_input

        # 确保 output 是字符串
        if isinstance(output, dict):
            output = json.dumps(output, ensure_ascii=False)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": output},
        ]
        converted.append({"messages": messages})

    with open(output_file, "w", encoding="utf-8") as f:
        for item in converted:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"  转换完成: {len(converted)} 条 (跳过 {skipped} 条)")
    return len(converted)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    convert(args.input, args.output)
