import os
import yaml
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# 配置路径
YAML_FILE = 'video_annotation_transcript.yaml'
OUTPUT_DIR_AH = './crop_videos/AH'
OUTPUT_DIR_NO_AH = './crop_videos/no_AH'

def ensure_dirs():
    """创建必要的输出目录"""
    os.makedirs(OUTPUT_DIR_AH, exist_ok=True)
    os.makedirs(OUTPUT_DIR_NO_AH, exist_ok=True)

def process_single_video(video_path, info):
    """处理单个视频的逻辑"""
    global_ah = info.get('global_ah')
    # 获取文件名（不含扩展名）和扩展名
    video_stem = Path(video_path).stem
    video_ext = Path(video_path).suffix
    
    # 检查原始文件是否存在
    if not os.path.exists(video_path):
        print(f"Warning: 文件未找到 - {video_path}")
        return

    try:
        if global_ah == 0:
            # 逻辑 1: 直接拷贝到 no_AH 文件夹
            target_path = os.path.join(OUTPUT_DIR_NO_AH, f"{video_stem}{video_ext}")
            shutil.copy2(video_path, target_path)
            print(f"Success: [Copy] {video_path} -> {target_path}")

        elif global_ah == 1:
            # 逻辑 2: 根据 time_detailed_ah 裁剪视频
            time_segments = info.get('time_detailed_ah', [])
            for i, segment in enumerate(time_segments):
                start_time, end_time = segment
                # 构造输出文件名：原文件名_i.mp4 (i从1开始)
                output_filename = f"{video_stem}_{i+1}{video_ext}"
                output_path = os.path.join(OUTPUT_DIR_AH, output_filename)
                
                # 使用 ffmpeg 进行裁剪
                # -ss 开始时间, -to 结束时间, -i 输入文件, -c copy (快速流拷贝)
                # 注意：如果需要极高的时间精度，建议移除 "-c copy" 改为重新编码，但速度会变慢
                # cmd = [
                #     'ffmpeg', '-y', '-ss', str(start_time), '-to', str(end_time),
                #     '-i', video_path, '-c', 'copy', output_path
                # ]

                cmd = [
                        'ffmpeg', '-y', 
                        '-ss', str(start_time), 
                        '-to', str(end_time),
                        '-i', video_path, 
                        '-c:v', 'libx264',    # 视频编码器：使用 H.264
                        '-crf', '18',         # 质量参数：18-23 之间（数值越小质量越高，18接近无损）
                        '-preset', 'veryfast',# 编码速度预设
                        '-c:a', 'aac',        # 音频编码器
                        '-strict', 'experimental',
                        output_path
                ]
                # 运行 ffmpeg，忽略标准输出，只捕获错误
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
                print(f"Success: [Trim] {video_path} Segment {i+1} -> {output_path}")

    except Exception as e:
        print(f"Error processing {video_path}: {e}")

def main():
    ensure_dirs()
    
    # 读取 YAML 文件
    # 使用 FullLoader 因为示例中包含 !!python/tuple 等特殊标签
    with open(YAML_FILE, 'r', encoding='utf-8') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    
    if not data:
        print("YAML 文件为空或格式错误。")
        return

    # 使用线程池进行多线程处理
    # max_workers 可以根据你的 CPU 核心数进行调整
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for video_path, info in data.items():
            # 提交任务到线程池
            futures.append(executor.submit(process_single_video, video_path, info))
        
        # 等待所有任务完成
        for future in futures:
            future.result()

if __name__ == "__main__":
    main()
