# README.md

# A-H-Detection-with-Qwen-Omni

This project provides a complete pipeline for video detection tasks, including data preprocessing, model training (SFT & GRPO), and video-level inference evaluation, based on the Qwen3 Omni model and MS-Swift framework.

## 1. Environment Requirements
- Python 3.10+

- CUDA 12.1+ (Required for vLLM / FlashAttention support)

- Linux System (Ubuntu 20.04 / 22.04 recommended)

```bash
pip install -r requirement.txt
```

## 2. Data Preprocessing (data_process/)

All data preprocessing scripts are stored in the `data_process/` directory, following the sequence below:

- `crop_video_yaml.py`: Crop videos according to the configuration file.

- `find_long_video.py`: Detect and identify long videos for optimization.

- `crop_no_AH_videos.py`: Slice and crop the preprocessed videos into standard clips.

- `dataset.py`: Build the standard training and evaluation dataset.

- `dataset_grpo.py`: Construct the dataset specialized for GRPO training.

## 3. Model Training (Based on MS-Swift Framework)

Training scripts are located in `ms-swift/examples/train/`, supporting two training methods:

- **SFT Training**: Use `lora_sft.sh` for LoRA-based supervised fine-tuning.

- **GRPO Training**: Use `grpo/plugin/Qwen3-VL-4B-reward_func.sh` for GRPO (Group Relative Policy Optimization) training with reward function support.

## 4. Inference & Evaluation (inference/)

The inference and evaluation pipeline includes three key scripts for clip-level and video-level prediction:

- `test.py`: Perform basic inference on sliced video clips.

- `max_predict.py`: Conduct clip-level prediction with maximum score selection.

- `vote.py`: Implement video-level prediction through a voting mechanism (Video-Level Prediction).

## Pipeline Overview
1. Environment

2. Preprocess videos: Crop via config → Find long videos → Slice and crop clips

3. Construct datasets (standard dataset & GRPO dataset)

4. Train model: Choose SFT or GRPO training

5. Inference & evaluation: Clip inference → Voting → Video-level prediction