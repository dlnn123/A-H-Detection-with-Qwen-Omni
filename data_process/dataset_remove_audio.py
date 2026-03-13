import json
import argparse

def remove_audio_key(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as fin, \
         open(output_file, 'w', encoding='utf-8') as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue  # 跳过空行
            try:
                data = json.loads(line)
                data.pop('audio', None)  # 安全删除 audio 键，不存在也不报错
                fout.write(json.dumps(data, ensure_ascii=False) + '\n')
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON line: {line[:100]}... Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Remove 'audio' key from each line of a JSONL file.")
    parser.add_argument("input", help="Input JSONL file path")
    parser.add_argument("output", help="Output JSONL file path")
    args = parser.parse_args()

    remove_audio_key(args.input, args.output)
    print(f"Processing complete. Output written to {args.output}")

if __name__ == "__main__":
    main()

