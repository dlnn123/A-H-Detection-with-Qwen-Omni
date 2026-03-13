#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import argparse
from typing import Optional

try:
    import cv2  # pip install opencv-python
except Exception as e:
    raise SystemExit(
        "ERROR: OpenCV not installed. Run: pip install opencv-python\n"
        f"Import error: {e}"
    )


def iter_mp4(root: str):
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if fn.lower().endswith(".mp4"):
                yield os.path.join(dp, fn)


def check_one(path: str, min_frames: int = 2) -> Optional[str]:
    """
    返回 None 表示正常；返回字符串表示坏的原因
    """
    if not os.path.exists(path):
        return "not_exist"

    try:
        if os.path.getsize(path) <= 0:
            return "empty_file"
    except Exception:
        return "stat_failed"

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return "opencv_cannot_open"

    # 基本信息（有些容器/编码会返回 0 或 NaN）
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0.0
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0.0

    # 最重要：能不能解码出一帧
    ok_read, frame = cap.read()
    cap.release()

    if (w <= 0) or (h <= 0):
        return "invalid_resolution"

    if (not ok_read) or (frame is None):
        return "cannot_decode_first_frame"

    # 帧数校验：有些文件 CAP_PROP_FRAME_COUNT 取不到（=0），这时用“连续读”来判断是否>=min_frames
    if frame_count and frame_count > 0:
        try:
            if int(frame_count) < min_frames:
                return f"frame_count<{min_frames}"
        except Exception:
            pass
    else:
        # frame_count 取不到时：再次打开，尝试读够 min_frames 帧
        cap2 = cv2.VideoCapture(path)
        if not cap2.isOpened():
            return "opencv_cannot_reopen"
        cnt = 0
        while cnt < min_frames:
            ok, fr = cap2.read()
            if not ok or fr is None:
                break
            cnt += 1
        cap2.release()
        if cnt < min_frames:
            return f"decoded_frames<{min_frames}"

    # fps 缺失有时也会导致上游处理出问题（可按需认为“坏”）
    if fps <= 0:
        return "fps_missing_or_invalid"

    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="要扫描的目录")
    ap.add_argument("--out", default="bad_videos.jsonl", help="坏视频输出 jsonl")
    ap.add_argument("--min-frames", type=int, default=2, help="最小帧数阈值（默认2，匹配你日志里的FRAME_FACTOR=2）")
    ap.add_argument("--log-every", type=int, default=200, help="每多少个打印一次进度")
    args = ap.parse_args()

    root = os.path.abspath(args.path)
    out_path = os.path.abspath(args.out)

    total = 0
    bad = 0

    with open(out_path, "w", encoding="utf-8") as f:
        for p in iter_mp4(root):
            total += 1
            reason = check_one(p, min_frames=args.min_frames)
            if reason is not None:
                bad += 1
                f.write(json.dumps({"path": p, "reason": reason}, ensure_ascii=False) + "\n")

            if total % args.log_every == 0:
                print(f"checked={total} bad={bad}")

    print(f"Done. checked={total}, bad={bad}")
    print(f"bad list saved to: {out_path}")


if __name__ == "__main__":
    main()
