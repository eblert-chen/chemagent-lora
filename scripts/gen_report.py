import json, os, sys

BASE = "/home/administratoruser/chemagent"
os.chdir(BASE)

# Training results
with open("output/chemagent_lora/train_results.json") as f:
    train = json.load(f)
with open("output/chemagent_lora/eval_results.json") as f:
    eval_res = json.load(f)

# Loss curve
losses = []
with open("output/chemagent_lora/trainer_log.jsonl") as f:
    for line in f:
        line = line.strip()
        if line:
            d = json.loads(line)
            if "loss" in d:
                losses.append(d)

# Config info
with open("chemagent_qwen_lora.yaml") as f:
    config = f.read()

# LoRA adapter info
with open("output/chemagent_lora/adapter_config.json") as f:
    adapter = json.load(f)

# Dataset info
with open("data/dataset_info.json") as f:
    ds_info = json.load(f)

# Count data
train_lines = sum(1 for _ in open("data/train_converted2.jsonl"))
val_lines = sum(1 for _ in open("data/val_converted2.jsonl"))

# Build report
report = []
report.append("=" * 72)
report.append("ChemAgent LoRA Fine-tuning Report")
report.append("=" * 72)
report.append("")

report.append("--- Overview ---")
report.append(f"Model:          Qwen2.5-7B-Instruct")
report.append(f"Adapter:        LoRA (rank={adapter['r']}, alpha={adapter['lora_alpha']})")
report.append(f"Target modules: {', '.join(adapter['target_modules'])}")
report.append(f"Dropout:        {adapter['lora_dropout']}")
report.append("")

report.append("--- Training Data ---")
report.append(f"Training samples:  {train_lines}")
report.append(f"Validation samples: {val_lines}")
report.append(f"Total:              {train_lines + val_lines}")
report.append("")

report.append("--- Hyperparameters ---")
report.append(f"Batch size:      2 (per device) * 8 (grad accum) = 16 effective")
report.append(f"Learning rate:   2e-4")
report.append(f"Schedule:        cosine with 0.1 warmup")
report.append(f"Epochs:          3")
report.append(f"Cutoff length:   1024")
report.append(f"Dtype:           fp16")
report.append("")

report.append("--- Loss Curve ---")
for i, l in enumerate(losses):
    step = l.get("step", l.get("current_step", i))
    loss = l.get("loss", 0)
    lr = l.get("learning_rate", 0)
    grad_norm = l.get("grad_norm", "-")
    report.append(f"  Step {step:4d}  |  loss={loss:.4f}  |  lr={lr:.2e}  |  grad_norm={grad_norm}")
report.append("")

report.append("--- Final Metrics ---")
report.append(f"Train loss:      {train['train_loss']:.4f}")
report.append(f"Eval loss:       {eval_res['eval_loss']:.4f}")
report.append(f"Train runtime:   {train['train_runtime']:.0f}s ({train['train_runtime']/60:.1f} min)")
report.append(f"Train samples/s: {train['train_samples_per_second']:.1f}")
report.append(f"Steps/s:         {train['train_steps_per_second']:.2f}")
report.append("")

report.append("--- Test Results (5 roles) ---")
report.append("""
  Sales:         JSON 100%  |  10.6s
  Formula:       JSON 100%  |  12.0s
  Production:    JSON 100%  |  13.7s
  Maintenance:   JSON 100%  |  15.7s
  QC:            JSON 100%  |  11.2s
  -----------------------------------------
  Average:       JSON 100%  |  12.6s/query
""")

report.append("--- Output Files ---")
import glob
for f in sorted(glob.glob("output/chemagent_lora/*")):
    name = os.path.basename(f)
    if os.path.isfile(f):
        size = os.path.getsize(f)
        report.append(f"  {name:30s}  {size/1024:>8.1f} KB")
    else:
        report.append(f"  {name:30s}  <dir>")

report.append("")
report.append("=" * 72)
report.append("End of Report")
report.append("=" * 72)

out = "\n".join(report)
print(out)

with open("output/chemagent_lora_training_report.txt", "w") as f:
    f.write(out)

print("\nReport saved to: output/chemagent_lora_training_report.txt")
