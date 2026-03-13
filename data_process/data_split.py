import json
import random
import os
from pathlib import Path
from typing import List


def split_jsonl(
    input_file: str,
    test_size: int = 400,
    train_suffix: str = "_train.jsonl",
    test_suffix: str = "_test.jsonl",
    shuffle: bool = True,
    encoding: str = "utf-8"
):
    """
    将一个 jsonl 文件随机拆分为训练集和测试集（测试集固定200行）
    
    参数:
        input_file: 输入的 jsonl 文件路径
        test_size: 测试集行数，默认 200
        train_suffix: 训练集输出文件名后缀
        test_suffix: 测试集输出文件名后缀
        shuffle: 是否随机打乱（强烈推荐）
        encoding: 文件编码
    
    输出:
        两个新文件：原文件名_train.jsonl 和 原文件名_test.jsonl
    """
    input_path = Path(input_file)
    if not input_path.is_file():
        print(f"错误：文件不存在 → {input_file}")
        return

    # 读取所有行
    print(f"正在读取文件: {input_file}")
    with open(input_path, 'r', encoding=encoding) as f:
        lines = [line.strip() for line in f if line.strip()]

    total_lines = len(lines)
    print(f"总行数: {total_lines}")

    if total_lines < test_size:
        print(f"警告：总行数 {total_lines} < 测试集要求 {test_size}，将全部放入测试集，训练集为空")
        test_lines = lines
        train_lines: List[str] = []
    else:
        # 随机打乱（推荐保持随机性，尤其是数据有顺序偏见时）
        if shuffle:
            random.shuffle(lines)
            print("已随机打乱数据顺序")

        # 前 200 行 → 测试集，其余 → 训练集
        test_lines = lines[:test_size]
        train_lines = lines[test_size:]

    # 输出路径
    base_dir = input_path.parent
    base_name = input_path.stem

    train_file = base_dir / f"{base_name}{train_suffix}"
    test_file = base_dir / f"{base_name}{test_suffix}"

    # 写入训练集
    if train_lines:
        with open(train_file, 'w', encoding=encoding) as f:
            for line in train_lines:
                f.write(line + '\n')
        print(f"训练集已保存: {train_file}  ({len(train_lines)} 行)")
    else:
        print("训练集为空，未生成训练文件")

    # 写入测试集
    with open(test_file, 'w', encoding=encoding) as f:
        for line in test_lines:
            f.write(line + '\n')
    print(f"测试集已保存: {test_file}  ({len(test_lines)} 行)")

    print("拆分完成！")


if __name__ == "__main__":
    # ==================== 修改这里 ====================
    INPUT_JSONL = "/dfs/data/BAH/data_crop_along_time_5/data_shuffle.jsonl"           # 替换成你的 jsonl 文件路径
    TEST_SIZE = 400                                # 测试集固定行数
    # ==================================================

    # 可选：如果你想输出到其他目录，可以这样写
    # split_jsonl(INPUT_JSONL, test_size=TEST_SIZE, train_suffix="_train.jsonl", test_suffix="_dev200.jsonl")

    split_jsonl(
        INPUT_JSONL,
        test_size=TEST_SIZE,
        train_suffix="_train.jsonl",
        test_suffix="_test.jsonl",
        shuffle=True                        # 建议保持 True
    )
