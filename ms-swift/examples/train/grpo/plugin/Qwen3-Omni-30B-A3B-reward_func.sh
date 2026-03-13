# register customized plugins in plugin.py file

PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True' \
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
NPROC_PER_NODE=8 \
MAX_PIXELS=602112 \
swift rlhf \
    --rlhf_type grpo \
    --model /dfs/data/ms-swift/model/Qwen/Qwen3-Omni-30B-A3B-Instruct \
    --external_plugins /dfs/data/ms-swift/examples/train/grpo/plugin/plugin.py \
    --reward_funcs external_r1v_acc format \
    --use_vllm true \
    --vllm_mode colocate \
    --vllm_gpu_memory_utilization 0.4 \
    --vllm_tensor_parallel_size 1 \
    --vllm_max_model_len 4096 \
    --tuner_type lora \
    --torch_dtype bfloat16 \
    --dataset '/dfs/data/BAH/data_train_with_solution.jsonl' \
    --overlong_filter false \
    --importance_sampling_level token \
    --epsilon 0.2 \
    --epsilon_high 0.28 \
    --max_completion_length 512 \
    --num_train_epochs 1 \
    --per_device_train_batch_size 1 \
    --learning_rate 1e-6 \
    --gradient_accumulation_steps 8 \
    --steps_per_generation 4 \
    --eval_steps 200 \
    --save_steps 200 \
    --save_total_limit 10 \
    --output_dir /dfs/data/ms-swift/examples/train/grpo/plugin/Qwen3-Omni-30B-A3B-Instruct_grpo \
    --sleep_level 1 \
    --offload_model true \
    --offload_optimizer true \
    --logging_steps 1 \
    --dataloader_num_workers 4 \
    --num_generations 2 \
    --temperature 1.0 \
    --system '/dfs/data/ms-swift/examples/train/grpo/prompt.txt' \
    --deepspeed zero1 \
    --log_completions true \
    --report_to tensorboard swanlab \
    --num_iterations 1 \
    --async_generate false \
    --beta 0.001 \
    --loss_type grpo \
    --vllm_enable_lora false \
    --advantage_estimator grpo
