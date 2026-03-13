#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
import argparse
import shutil
from pathlib import Path


def has_ffprobe():
    """检查系统是否安装了 ffprobe"""
    return shutil.which("ffprobe") is not None


def get_video_duration(path):
    """
    使用 ffprobe 获取视频时长（秒）
    成功返回 float（秒），失败返回 None
    """
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1",
        path
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True,
            check=False
        )
        if result.returncode != 0:
            return None
        duration_str = result.stdout.strip()
        if not duration_str or not duration_str.replace('.', '', 1).isdigit():
            return None
        return float(duration_str)
    except (subprocess.TimeoutExpired, ValueError, Exception):
        return None


def find_mp4_files(root):
    """递归查找所有 .mp4 文件（不区分大小写）"""
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")
    for file_path in root.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() == ".mp4":
            yield str(file_path)


def main():
    parser = argparse.ArgumentParser(description="Find MP4 videos longer than a specified duration.")
    parser.add_argument("path", help="Root directory to scan for .mp4 files")
    parser.add_argument("--out", default="long_videos_test.jsonl", help="Output JSONL file (default: long_videos.jsonl)")
    parser.add_argument("--min-duration", type=float, default=5, help="Minimum duration in seconds (default: 30.0)")
    args = parser.parse_args()

    if not has_ffprobe():
        print("ERROR: ffprobe not found. Please install FFmpeg first.", file=sys.stderr)
        sys.exit(1)

    total = 0
    long_count = 0

    with open(args.out, "w", encoding="utf-8") as fout:
        for video_path in find_mp4_files(args.path):
            total += 1
            duration = get_video_duration(video_path)
            if duration is not None and duration > args.min_duration:
                long_count += 1
                fout.write(json.dumps({
                    "path": video_path,
                    "duration": round(duration, 3)
                }, ensure_ascii=False) + "\n")

            if total % 200 == 0:
                print(f"Processed: {total}, Long videos: {long_count}")

    print(f"\n✅ Done. Total MP4s: {total}, Videos >{args.min_duration}s: {long_count}")
    print(f"Output saved to: {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()