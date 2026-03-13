import json
from collections import Counter

def calculate_metrics(tp, tn, fp, fn):
    """计算准确率、精确率、召回率和 F1-Score"""
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "Accuracy": f"{accuracy:.2%}",
        "Precision": f"{precision:.2%}",
        "Recall": f"{recall:.2%}",
        "F1-Score": f"{f1:.4f}"
    }

def process_voting(file_paths, output_path):
    # 1. 加载所有JSON文件
    all_files_data = []
    for path in file_paths:
        with open(path, 'r', encoding='utf-8') as f:
            all_files_data.append(json.load(f))

    # 2. 建立视频映射表：video_path -> (prediction, ground_truth)
    # 使用字典方便通过视频路径快速检索
    maps = []
    for data in all_files_data:
        # 提取 details 列表中的信息
        v_map = {item['video']: (item['prediction_label'], item['ground_truth_label']) 
                 for item in data.get('details', [])}
        maps.append(v_map)

    # 3. 寻找三个文件共有的视频路径 (取交集)
    video_sets = [set(m.keys()) for m in maps]
    common_videos = sorted(list(set.intersection(*video_sets)))
    
    if not common_videos:
        print("警告：没有找到共同的视频文件，请检查输入文件。")
        return

    final_details = []
    tp, tn, fp, fn = 0, 0, 0, 0

    # 4. 遍历共有视频并进行投票
    for idx, video in enumerate(common_videos):
        # 获取三个文件对该视频的预测
        preds = [maps[0][video][0], maps[1][video][0], maps[2][video][0]]
        # 获取 Ground Truth (取第一个文件的GT，假设三个文件GT一致)
        gt = maps[0][video][1]
        
        # 多数投票逻辑 (2 vs 1)
        # Counter().most_common(1) 返回 [('Yes', 2)] 这种形式
        voted_label = Counter(preds).most_common(1)[0][0]
        
        is_correct = (voted_label == gt)
        
        # 统计 TP, TN, FP, FN (假设标签是 "Yes" 和 "No")
        if voted_label == "Yes" and gt == "Yes":
            tp += 1
        elif voted_label == "No" and gt == "No":
            tn += 1
        elif voted_label == "Yes" and gt == "No":
            fp += 1
        elif voted_label == "No" and gt == "Yes":
            fn += 1

        # 构造 detail 条目
        final_details.append({
            "index": idx,
            "video": video,
            "prediction_label": voted_label,
            "ground_truth_label": gt,
            "is_correct": is_correct,
            "snippet_count": 1 # 默认值，或者你可以从原数据中提取
        })

    # 5. 生成汇总数据
    summary_metrics = calculate_metrics(tp, tn, fp, fn)
    
    output_data = {
        "summary": summary_metrics,
        "raw_counts": {
            "total": len(common_videos),
            "correct": tp + tn,
            "TP": tp,
            "TN": tn,
            "FP": fp,
            "FN": fn
        },
        "details": final_details
    }

    # 6. 保存为 JSON 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print(f"处理完成！")
    print(f"共有视频数: {len(common_videos)}")
    print(f"投票后准确率: {summary_metrics['Accuracy']}")
    print(f"结果已保存至: {output_path}")

# --- 执行脚本 ---
if __name__ == "__main__":
    # 输入你的三个 JSON 文件路径
    input_json_files = [
        "output_long_video_lora_datav1.json", 
        "output_long_video_b64_lr1e-5_3epoch_full_datav1.json", 
        "output_long_video_b64_lr1e-5_2epoch_full_datav2_100.json"
    ]
    output_json_file = "voted_final_result.json"
    
    process_voting(input_json_files, output_json_file)
