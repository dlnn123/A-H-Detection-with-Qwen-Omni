# 22GB
# qwen3: https://github.com/modelscope/ms-swift/blob/main/examples/train/think_model/qwen3_demo1.sh
CUDA_VISIBLE_DEVICES=0,1,2,3 \
#!/bin/bash
swift sft \
    --model /dfs/data/ms-swift/model/Qwen/Qwen3-Omni-30B-A3B-Instruct \
    --tuner_type lora \
    --dataset '/dfs/data/BAH/data_crop_along_time_5/data_shuffle_train_sft.jsonl' \
    --torch_dtype bfloat16 \
    --num_train_epochs 1 \
    --per_device_train_batch_size 2 \
    --per_device_eval_batch_size 2 \
    --learning_rate 1e-5 \
    --lora_rank 8 \
    --lora_alpha 32 \
    --target_modules all-linear \
    --gradient_accumulation_steps 32 \
    --eval_steps 30 \
    --save_steps 30 \
    --save_total_limit 2 \
    --logging_steps 5 \
    --max_length 32768 \
    --max_new_tokens 1024 \
    --output_dir output \
    --system 'You are a Multimodal Emotion Analysis Expert.' \
    --warmup_ratio 0.05 \
    --dataloader_num_workers 4 \
    --model_author swift \
    --model_name swift-robot \
    --truncation_strategy left
    # --padding_side right  \
    # --resume_from_checkpoint /dfs/data/ms-swift/examples/train/output/v11-20260306-105830/checkpoint-120
