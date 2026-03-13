import json
import os
import subprocess
from pathlib import Path
from tqdm import tqdm


# def get_cut_points(duration: float) -> list[int]:
#     """
#     根据视频时长返回切割结束时间点（秒）
#     """
#     if duration < 50:
#         return [25]
#     elif duration < 75:
#         return [25, 50]
#     else:
#         return [25, 50, 75]

def get_cut_points(duration: float) -> list[int]:
    """
    新版均匀切割策略：全部切成 10s 以内，无过短片段
    10-20s: 1段 (0-10s)
    20-30s: 2段 (0-10s,10-20s)
    30s+: 每10s一段，最后一段<6s丢弃
    """
    cut_points = []
    current = 5
    while current < duration:
        cut_points.append(current)
        current += 5
    return cut_points

def cut_video_ffmpeg(video_path: str, output_dir: str = None):
    """
    使用 ffmpeg 重编码方式裁剪视频
    所有切片成功后删除原文件
    """
    try:
        # 这里假设 duration 已从 json 传入，如果没有可后续用 ffprobe 获取
        # 为了演示完整性，临时用 moviepy 获取（生产环境建议用 ffprobe）
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(video_path)
        total_duration = clip.duration
        clip.close()

        cut_points = get_cut_points(total_duration)
        if not cut_points:
            print(f"无需切割: {video_path} ({total_duration:.2f}s)")
            return

        basename = Path(video_path).stem
        ext = Path(video_path).suffix
        parent = Path(video_path).parent

        output_base = Path(output_dir) if output_dir else parent
        output_base.mkdir(parents=True, exist_ok=True)

        prev = 0.0
        success_count = 0

        for i, end_time in enumerate(cut_points + [total_duration], 1):
            if end_time > total_duration:
                end_time = total_duration
            if end_time - prev < 3:  # 避免过短片段
                continue

            output_path = output_base / f"{basename}_{i}{ext}"

            # 你指定的 ffmpeg 命令参数
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(prev),             # 起始时间
                '-to', str(end_time),         # 结束时间（绝对时间点）
                '-i', video_path,
                '-c:v', 'libx264',            # 视频编码器：H.264
                '-crf', '18',                 # 质量：18 ≈ 接近视觉无损
                '-preset', 'veryfast',        # 速度优先（比 medium 快很多）
                '-c:a', 'aac',                # 音频编码
                '-strict', 'experimental',    # 兼容旧版 ffmpeg 对 aac 的处理
                str(output_path)
            ]

            print(f"正在生成第 {i} 段：{prev:.1f}s → {end_time:.1f}s  ({end_time-prev:.1f}s)")
            # print("执行命令:", " ".join(cmd))  # 调试时可打开

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"成功生成: {output_path}")
                success_count += 1
            else:
                print(f"裁剪失败 {output_path}")
                print(result.stderr[:300])  # 输出部分错误信息
                # 根据需求可选择 continue 或 return 提前退出

            prev = end_time

        # 所有切片都成功才删除原文件（更安全）
        if success_count > 0:
            try:
                os.remove(video_path)
                print(f"已删除原文件: {video_path}")
            except Exception as e:
                print(f"删除原文件失败: {video_path} → {e}")
        else:
            print(f"警告：{video_path} 部分切片失败，未删除原文件")

    except Exception as e:
        print(f"处理 {video_path} 时发生异常: {e}")


def main(jsonl_path: str, output_dir: str = None):
    if not os.path.isfile(jsonl_path):
        print(f"jsonl 文件不存在: {jsonl_path}")
        return

    total = 0
    processed = 0

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        total = len(lines)

    with tqdm(total=total, desc="处理视频") as pbar:
        for line in lines:
            try:
                data = json.loads(line)
                video_path = data.get("path")
                duration = data.get("duration", 0)

                if not video_path or not os.path.isfile(video_path):
                    print(f"视频不存在，跳过: {video_path}")
                    pbar.update(1)
                    continue

                if duration < 5:
                    print(f"视频过短 ({duration}s)，跳过: {video_path}")
                    pbar.update(1)
                    continue

                print(f"\n处理视频: {video_path}  时长 {duration:.2f}s")
                cut_video_ffmpeg(video_path, output_dir)
                processed += 1

            except json.JSONDecodeError:
                print(f"JSON 解析失败，跳过: {line[:80]}...")
            except Exception as e:
                print(f"未知错误: {e}")

            pbar.update(1)

    print(f"\n处理完成！成功处理 {processed}/{total} 个视频")


if __name__ == "__main__":
    # ==================== 修改这里 ====================
    JSONL_FILE = "/dfs/data/BAH/long_videos_test.jsonl"          # ← 替换成你的 jsonl 路径
    OUTPUT_DIRECTORY = None                            # ← 改成统一输出目录，例如 "/dfs/data/BAH/clipped"，或 None 表示原目录
    # ==================================================

    main(JSONL_FILE, OUTPUT_DIRECTORY)
