import json
import re
import os

def process_video_evaluation(input_file, output_file):
    # 1. 读取原始数据
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    details = data.get("details", [])
    video_groups = {}

    # 2. 视频分组逻辑
    # 匹配模式：将结尾处的 _1.mp4, _2_1.mp4 等替换回 .mp4 得到原长视频路径
    suffix_pattern = re.compile(r'(_\d+)+\.mp4$')

    for item in details:
        original_path = suffix_pattern.sub('.mp4', item['video'])
        
        if original_path not in video_groups:
            video_groups[original_path] = {
                "ground_truth_label": item['ground_truth_label'],
                "predictions": [],
                "details_samples": item  # 保留一份元数据样本
            }
        video_groups[original_path]["predictions"].append(item['prediction_label'])

    # 3. 重新判定与指标统计
    new_details = []
    tp, tn, fp, fn = 0, 0, 0, 0

    for i, (path, info) in enumerate(video_groups.items()):
        gt = info["ground_truth_label"]
        preds = info["predictions"]
        
        # 逻辑：
        # 对于 GT 为 Yes：片段只要有一个 Yes，最终预测就是 Yes (正确)
        # 对于 GT 为 No ：片段只要有一个 Yes，最终预测就是 Yes (错误)
        # 归纳：只要片段序列中存在任何一个 "Yes"，长视频预测即为 "Yes"
        
        final_prediction = "Yes" if "Yes" in preds else "No"
        is_correct = (final_prediction == gt)

        # 更新计数器
        if gt == "Yes" and final_prediction == "Yes": tp += 1
        elif gt == "No" and final_prediction == "No": tn += 1
        elif gt == "No" and final_prediction == "Yes": fp += 1
        elif gt == "Yes" and final_prediction == "No": fn += 1

        # 构建新的 detail 条目
        new_entry = {
            "index": i,
            "video": path,
            "prediction_label": final_prediction,
            "ground_truth_label": gt,
            "is_correct": is_correct,
            "snippet_count": len(preds) # 附加信息：由多少个片段合并而来
        }
        new_details.append(new_entry)

    # 4. 计算 summary 指标
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    output_data = {
        "summary": {
            "Accuracy": f"{accuracy:.2%}",
            "Precision": f"{precision:.2%}",
            "Recall": f"{recall:.2%}",
            "F1-Score": f"{f1:.4f}"
        },
        "raw_counts": {
            "total": total,
            "correct": tp + tn,
            "TP": tp,
            "TN": tn,
            "FP": fp,
            "FN": fn
        },
        "details": new_details
    }

    # 5. 存储结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    print(f"处理完成！结果已保存至: {output_file}")

if __name__ == "__main__":
    # 请确保 input.json 路径正确
    process_video_evaluation('evaluation_results_b64_lr1e-5_2epoch_full_datav2_100.json', 'output_long_video_b64_lr1e-5_2epoch_full_datav2_100.json')
