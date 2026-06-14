#!/bin/bash
# ChemAgent LoRA 微调 (WSL2 版)
# 用法: cd /mnt/e/project/huayangyunke/chem/chemagent && bash scripts/5_train.sh
set -e

# 路径配置 - 指向 Windows 文件系统
PROJ_DIR="/mnt/e/project/huayangyunke/chem/chemagent"
MODEL_DIR="/mnt/d/loca_models/Qwen2.5-7B-Instruct"
OUTPUT_DIR="$PROJ_DIR/output"

# CUDA 库路径（修复 WSL 下 CUPTI/libcufile 找不到的问题）
CUDA_LIBS=$(find /usr/local/lib/python3.10/dist-packages/nvidia -name lib -type d 2>/dev/null | tr '\n' ':')
export LD_LIBRARY_PATH=$CUDA_LIBS$LD_LIBRARY_PATH

# 代理配置 (通过 Windows 的 Clash)
PROXY_HOST=$(ip route | grep default | awk '{print $3}')
export HTTP_PROXY="http://$PROXY_HOST:7898"
export HTTPS_PROXY="http://$PROXY_HOST:7898"
export HF_ENDPOINT="https://hf-mirror.com"
export HF_HUB_DISABLE_SYMLINKS_WARNING=1

cd "$PROJ_DIR"
mkdir -p "$OUTPUT_DIR"

echo "═══ ChemAgent LoRA Fine-tuning ═══"
echo "项目: $PROJ_DIR"
echo "模型: $MODEL_DIR"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"

# Step 1: 创建虚拟环境
echo ""
echo "[1/5] 创建 Python 虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -U pip -q

# Step 2: 安装 LLaMA-Factory
echo ""
echo "[2/5] 安装 LLaMA-Factory..."
pip install llamafactory[torch] -q 2>&1 | tail -1

# Step 3: 注册数据集
echo ""
echo "[3/5] 注册数据集..."
python3 -c "
import json, os
info = {}
info['chemagent_lora'] = {
    'file_name': '../data/train_converted.jsonl',
    'formatting': 'sharegpt',
    'columns': {'messages': 'messages'}
}
info['chemagent_lora_val'] = {
    'file_name': '../data/val_converted.jsonl',
    'formatting': 'sharegpt',
    'columns': {'messages': 'messages'}
}
os.makedirs('data', exist_ok=True)
with open('data/dataset_info.json', 'w') as f:
    json.dump(info, f, ensure_ascii=False, indent=2)
echo '  数据集注册完成'
"

# Step 4: 生成训练配置
echo ""
echo "[4/5] 生成训练配置..."
BATCH_SIZE=8
ACCUM=2

cat > chemagent_qwen_lora.yaml << YAML
model_name_or_path: $MODEL_DIR
stage: sft
do_train: true
finetuning_type: lora
lora_rank: 16
lora_alpha: 32
lora_target: q_proj,v_proj,k_proj,o_proj
lora_dropout: 0.05

dataset: chemagent_lora
eval_dataset: chemagent_lora_val
template: qwen
cutoff_len: 1024
preprocessing_num_workers: 4

output_dir: $OUTPUT_DIR/chemagent_lora
logging_steps: 20
save_steps: 200
eval_steps: 200

per_device_train_batch_size: ${BATCH_SIZE}
gradient_accumulation_steps: ${ACCUM}
learning_rate: 2.0e-4
num_train_epochs: 3
lr_scheduler_type: cosine
warmup_ratio: 0.1
fp16: true

load_best_model_at_end: true
metric_for_best_model: loss
greater_is_better: false
YAML

echo "  batch_size=$BATCH_SIZE, accum=$ACCUM"

# Step 5: 训练
echo ""
echo "[5/5] 开始训练 (约 15-20 分钟)..."
llamafactory-cli train chemagent_qwen_lora.yaml 2>&1 | tee $OUTPUT_DIR/train.log

# 完成
echo ""
echo "═══ 训练完成 ═══"
echo "LoRA adapter: $OUTPUT_DIR/chemagent_lora"
echo "日志: $OUTPUT_DIR/train.log"
echo ""
echo "合并模型 (需要 30GB 磁盘):"
echo "  llamafactory-cli export --model_name_or_path $MODEL_DIR --adapter_name_or_path $OUTPUT_DIR/chemagent_lora --template qwen --output_dir $OUTPUT_DIR/chemagent_merged"
echo ""
echo "测试:"
echo "  python3 scripts/6_test.py"
