# coding=utf-8
import base64
import cv2
import os
import tempfile
import numpy as np
import json
import re
import jsonlines
from openai import OpenAI
import httpx

def extract_all_frames(video_path):
    """
    从视频中提取所有帧（不跳帧），保持原始顺序和分辨率，使用 JPEG 压缩。
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")
    
    temp_files = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        cv2.imwrite(temp_file.name, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        temp_files.append(temp_file.name)
        frame_idx += 1

    cap.release()
    print(f"✅ 成功提取 {len(temp_files)} 帧（全部帧）")
    return temp_files

def extract_frames_uniformly(video_path, max_frames=45):
    """
    从视频中均匀提取多帧，保持原始分辨率，但使用 JPEG 压缩以节省体积。
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if total_frames <= 0:
        total_frames = 0
        while True:
            ret, _ = cap.read()
            if not ret: break
            total_frames += 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
    num_frames = min(max_frames, total_frames) if total_frames > 0 else max_frames
    indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    indices = sorted(list(set(indices)))

    temp_files = []
    print(f"视频 FPS: {fps:.2f}, 总帧数: {total_frames}")
    print(f"计划抽取: {len(indices)} 帧")

    for i in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret:
            continue
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        cv2.imwrite(temp_file.name, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        temp_files.append(temp_file.name)
        
    cap.release()
    return temp_files

def image_to_base64_url(image_path):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"

def parse_model_answer(text):
    """从模型输出中提取 <answer>Yes/No</answer>"""
    match = re.search(r"<answer>\s*(Yes|No)\s*</answer>", text, re.IGNORECASE)
    if match:
        return f"<answer>{match.group(1).capitalize()}</answer>"
    return None

def main():
    # === 配置 ===
    JSONL_PATH = "/dfs/data/ms-swift/examples/eval/output_sorted_no.jsonl"  # 替换为你的 .jsonl 文件路径
    API_KEY = ""
    BASE_URL = ""
    MODEL = "qwen3.5-plus"
    MAX_FRAMES = 200

    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        http_client=httpx.Client(verify=False, timeout=120.0)
    )

    correct = 0
    total = 0

    with jsonlines.open(JSONL_PATH, mode='r') as reader:
        for idx, item in enumerate(reader):
            if idx >= 10:
                break  # 只处理前50个样本
            video_path = item["video"][0]
            ground_truth = item["solution"].strip()
            prompt_text = item["messages"][0]["content"]
#             prompt_text = '''Analyze the emotions exhibited in the video frames (extracted from the <video> clip) to determine if Ambivalence/Hesitancy is present. Follow these steps strictly:
# 1. Visual Analysis:
#    - Examine the subject's facial expressions (e.g., furrowed brows, uncertain eye gaze, lip biting, conflicting facial cues)
#    - Analyze body language and physical movements (e.g., hesitant gestures, fidgeting, paused actions, contradictory postures, slow/indecisive movements)
#    - Identify any non-verbal cues that indicate mixed feelings, uncertainty, or reluctance
# 2. Emotion Judgment:
#    - Based on the above visual evidence, determine if the video clip exhibits Ambivalence/Hesitancy emotions
# 3. Output Requirement:
#    - Final answer must be in the format <answer>Yes</answer> or <answer>No</answer>
#    - Only include "Yes" or "No" inside the <answer> tags (no extra words, punctuation, or explanations)'''

            print(f"\n[样本 {idx+1}] 处理视频: {os.path.basename(video_path)}")
            print(f"Ground Truth: {ground_truth}")

            try:
                frame_paths = extract_frames_uniformly(video_path, max_frames=MAX_FRAMES)
                #frame_paths = extract_all_frames(video_path)
                if not frame_paths:
                    print("跳过：未提取到帧")
                    continue

                content_parts = [{"type": "text", "text": prompt_text}]
                for p in frame_paths:
                    img_url = image_to_base64_url(p)
                    content_parts.append({"type": "image_url", "image_url": {"url": img_url}})

                messages = [{"role": "user", "content": content_parts}]

                completion = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    temperature=0,
                    # top_p = 0.95,
                    stream=False  # 改为非流式，便于解析完整回答
                )

                model_output = completion.choices[0].message.content.strip()
                predicted = parse_model_answer(model_output)

                print(f"模型输出: {model_output}")
                print(f"解析结果: {predicted}")
                print(f"groud truth: {ground_truth}")

                if predicted == ground_truth:
                    correct += 1
                    print("✅ 正确")
                else:
                    print("❌ 错误")

                total += 1

            except Exception as e:
                print(f"⚠️ 处理失败: {e}")
                # 可选择跳过或记录错误

            finally:
                # 清理临时帧文件
                for p in frame_paths if 'frame_paths' in locals() else []:
                    if os.path.exists(p):
                        os.unlink(p)

    # 输出最终准确率
    if total > 0:
        accuracy = correct / total * 100
        print(f"\n📊 总样本数: {total}, 正确数: {correct}, 准确率: {accuracy:.2f}%")
    else:
        print("没有成功处理的样本。")

if __name__ == "__main__":
    main()