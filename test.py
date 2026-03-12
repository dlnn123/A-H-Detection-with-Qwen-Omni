import torch
import json
import os
import re
import soundfile as sf
from transformers import Qwen3OmniMoeForConditionalGeneration, Qwen3OmniMoeProcessor
from qwen_omni_utils import process_mm_info
from prompt import prompt_analysis
# ===================== 配置区域 =====================
MODEL_PATH = "/dfs/data/model/b64_lr1e-5_2epoch_full_datav2"
JSONL_PATH = "/dfs/data/train_file/data_shuffle_test_solution.jsonl"
NUM_SAMPLES = 100  # 想要读取的前 n 条数据
OUTPUT_JSON = "evaluation_results_b64_lr1e-5_2epoch_full_datav22.json"
USE_AUDIO_IN_VIDEO = False  # 是否使用视频内置音频

# ===================== 工具函数 =====================
def extract_answer(text):
    """
    从模型输出或 Ground Truth 中提取 <answer>Yes/No</answer> 内容
    支持大小写不敏感匹配
    """
    if not text or not isinstance(text, str):
        return None
    # 使用正则匹配标签内的内容，忽略空格和大小写
    match = re.search(r'<answer>\s*(Yes|No)\s*</answer>', text, re.IGNORECASE)
    if match:
        return match.group(1).strip().capitalize()
    return None

def calculate_metrics(metrics):
    """计算分类指标"""
    total = metrics["total"]
    if total == 0:
        return "无有效数据"
    
    acc = metrics["correct"] / total
    # 精确率 Precision = TP / (TP + FP)
    precision = metrics["TP"] / (metrics["TP"] + metrics["FP"]) if (metrics["TP"] + metrics["FP"]) > 0 else 0
    # 召回率 Recall = TP / (TP + FN)
    recall = metrics["TP"] / (metrics["TP"] + metrics["FN"]) if (metrics["TP"] + metrics["FN"]) > 0 else 0
    # F1 Score
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "Accuracy": f"{acc:.2%}",
        "Precision": f"{precision:.2%}",
        "Recall": f"{recall:.2%}",
        "F1-Score": f"{f1:.4f}"
    }

# ===================== 加载模型 =====================
print(f"正在加载模型: {MODEL_PATH} ...")
model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    torch_dtype="auto",
    device_map="auto",
    attn_implementation="flash_attention_2",
)
processor = Qwen3OmniMoeProcessor.from_pretrained(MODEL_PATH)

# ===================== 处理函数 =====================
def run_inference(jsonl_path, n):
    results = []
    # 统计指标初始化
    metrics = {"total": 0, "correct": 0, "TP": 0, "TN": 0, "FP": 0, "FN": 0}

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            
            data = json.loads(line)
            
            # 1. 提取路径
            video_path = data.get("video", [None])[0]
            audio_path = data.get("audio", [None])[0] 
            if audio_path is None and video_path:
                audio_path = video_path.replace(".mp4", ".wav")
            
            # 2. 构建对话格式
            content_list = []
            if audio_path and os.path.exists(audio_path):
                content_list.append({"type": "audio", "audio": audio_path})
            if video_path and os.path.exists(video_path):
                content_list.append({"type": "video", "video": video_path})

            # 提示词
            # prompt_analysis = "Combine the <video> and <audio> content to analyze whether this video clip exhibits Ambivalence/Hesitancy emotions. Output the answer in the format <answer>answer is here</answer>, responding only with Yes or No."
            content_list.append({"type": "text", "text": prompt_analysis})

            conversation = [{"role": "user", "content": content_list}]

            # 3. 推理准备
            text_prompt = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
            audios, images, videos = process_mm_info(conversation, use_audio_in_video=USE_AUDIO_IN_VIDEO)

            inputs = processor(
                text=text_prompt, 
                audio=audios, 
                images=images, 
                videos=videos, 
                return_tensors="pt", 
                padding=True, 
                use_audio_in_video=USE_AUDIO_IN_VIDEO
            )
            inputs = inputs.to(model.device).to(model.dtype)

            # 4. 执行生成
            with torch.no_grad():
                text_ids, _ = model.generate(
                    **inputs, 
                    thinker_return_dict_in_generate=True,
                    use_audio_in_video=USE_AUDIO_IN_VIDEO,
                    temperature=0.3,
                    top_p=0.95,
                    max_new_tokens=1024, 
                    do_sample=True,
                )

            # 5. 解码
            output_text = processor.batch_decode(
                text_ids.sequences[:, inputs["input_ids"].shape[1] :],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )[0]

            # 6. 解析答案与统计
            pred_label = extract_answer(output_text)
            gt_raw = data.get("solution", "")
            gt_label = extract_answer(gt_raw)

            is_correct = False
            if pred_label and gt_label:
                metrics["total"] += 1
                is_correct = (pred_label == gt_label)
                if is_correct:
                    metrics["correct"] += 1
                    if gt_label == "Yes": metrics["TP"] += 1
                    else: metrics["TN"] += 1
                else:
                    if pred_label == "Yes": metrics["FP"] += 1
                    else: metrics["FN"] += 1
            else:
                print(f"Warning: 第 {i+1} 条数据解析失败。预测: {pred_label}, 真值: {gt_label}")

            # 打印实时进度
            print(f"[{i+1}/{n}] 视频: {os.path.basename(video_path)}")
            print(f"   模型输出: {output_text.strip()}")
            print(f"   Ground Truth: {gt_raw.strip()}")
            print(f"   结果: {'✓' if is_correct else '✗'}")
            
            results.append({
                "index": i,
                "video": video_path,
                "prediction_raw": output_text,
                "prediction_label": pred_label,
                "ground_truth_label": gt_label,
                "is_correct": is_correct
            })

    # --- 最终汇总 ---
    stats = calculate_metrics(metrics)
    
    print("\n" + "="*50)
    print("                最终评测结果")
    print("="*50)
    print(f"测试样本总数: {n}")
    print(f"有效解析样本: {metrics['total']}")
    if isinstance(stats, dict):
        for k, v in stats.items():
            print(f"{k}: {v}")
        print("-" * 50)
        print(f"True Positive (Yes正确): {metrics['TP']}")
        print(f"True Negative (No正确):  {metrics['TN']}")
        print(f"False Positive (误报):   {metrics['FP']}")
        print(f"False Negative (漏报):   {metrics['FN']}")
    else:
        print(stats)
    print("="*50)

    # 保存统计结果到 JSON
    final_data = {
        "summary": stats,
        "raw_counts": metrics,
        "details": results
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
    print(f"结果已保存至: {OUTPUT_JSON}")

    return results

# 开始执行
if __name__ == "__main__":
    final_outputs = run_inference(JSONL_PATH, NUM_SAMPLES)
