import os
import json

def generate_jsonl(path1, path2, output_file):
    # 获取 path1 下所有 .mp4 文件（不含子目录）
    mp4_files = {f: os.path.join(path1, f) for f in os.listdir(path1) if f.lower().endswith('.mp4')}
    
    results = []

    for mp4_name, mp4_path in mp4_files.items():
        # 构造对应的 .wav 文件名（去掉 .mp4 后缀，加上 .wav）
        base_name = os.path.splitext(mp4_name)[0]
        wav_name = base_name + '.wav'
        wav_path = os.path.join(path2, wav_name)

        # 检查 .wav 文件是否存在
        if os.path.isfile(wav_path):
            entry = {
                "messages": [
                    {
                        "role": "user",
                        "content": "Combine the <video> and <audio> content to analyze whether this video clip exhibits Ambivalence/Hesitancy emotions. Output the answer in the format <answer>answer is here</answer>, responding only with Yes or No."
                    },
                    {
                        "role": "assistant",
                        "content": "<answer>Yes</answer>"  # 注意：这里默认是"Yes"，实际可能需要模型预测
                    }
                ],
                "video": [mp4_path],
                "audio": [wav_path]
            }
            results.append(entry)
        else:
            print(f"Warning: No matching .wav file for {mp4_name}")

    # 写入 JSONL 文件（每行一个 JSON 对象）
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in results:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"Successfully wrote {len(results)} entries to {output_file}")

# === 使用示例 ===
if __name__ == "__main__":
    path1 = "/dfs/data/BAH/data_testset/data/crop_along_time_5/Videos"   # 替换为你的 mp4 路径
    path2 = "/dfs/data/BAH/data_testset/data/crop_along_time_5/Audios"   # 替换为你的 wav 路径
    output_file = "/dfs/data/train_file/data_testset.jsonl"

    generate_jsonl(path1, path2, output_file)