#!/bin/bash
export PATH=/home/administratoruser/.local/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/lib/python3.10/dist-packages/nvidia/cuda_cupti/lib:/usr/local/lib/python3.10/dist-packages/nvidia/cufile/lib:/usr/local/lib/python3.10/dist-packages/nvidia/cuda_runtime/lib:/usr/local/lib/python3.10/dist-packages/nvidia/cublas/lib:/usr/local/lib/python3.10/dist-packages/nvidia/cudnn/lib
export HTTP_PROXY=http://172.25.192.1:7898
export HTTPS_PROXY=http://172.25.192.1:7898

cd /mnt/e/project/huayangyunke/chem/chemagent
mkdir -p output data

python3 -c "import json; json.dump({'chemagent_lora':{'file_name':'../data/train_converted2.jsonl','formatting':'sharegpt','columns':{'messages':'messages'}},'chemagent_lora_val':{'file_name':'../data/val_converted2.jsonl','formatting':'sharegpt','columns':{'messages':'messages'}}}, open('data/dataset_info.json','w'), ensure_ascii=False, indent=2)"
echo "OK"

llamafactory-cli train chemagent_qwen_lora.yaml 2>&1 | tee output/train.log
echo "DONE"
