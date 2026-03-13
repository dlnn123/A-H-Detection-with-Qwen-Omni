import random
import json

def shuffle_jsonl(input_file, output_file, seed=None):
    """
    随机打乱 JSONL 文件的行顺序。

    :param input_file: 输入的 .jsonl 文件路径
    :param output_file: 输出的打乱后的 .jsonl 文件路径
    :param seed: 随机种子（可选，用于复现结果）
    """
    if seed is not None:
        random.seed(seed)

    # 读取所有行
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"Read {len(lines)} lines from {input_file}")

    # 可选：验证每行是否为合法 JSON（调试用，可注释掉以提速）
    # valid_lines = []
    # for i, line in enumerate(lines):
    #     line = line.strip()
    #     if line:
    #         try:
    #             json.loads(line)
    #             valid_lines.append(line)
    #         except json.JSONDecodeError:
    #             print(f"Warning: Invalid JSON on line {i+1}, skipping.")
    # lines = [line + '\n' for line in valid_lines]

    # 打乱顺序
    random.shuffle(lines)

    # 写入新文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"Shuffled data written to {output_file}")

# === 使用示例 ===
if __name__ == "__main__":
    input_path = "/dfs/data/BAH/data_crop_along_time_5/data.jsonl"      # 原始 JSONL 文件
    output_path = "/dfs/data/BAH/data_crop_along_time_5/data_shuffle.jsonl"  # 打乱后的文件
    shuffle_jsonl(input_path, output_path, seed=42)  # 设置 seed=42 可复现结果