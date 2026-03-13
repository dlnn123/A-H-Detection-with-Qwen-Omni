import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

# def extract_audio(video_path, output_path):
#     """
#     使用 ffmpeg 提取音频
#     -vn: 禁用视频记录
#     -ar 16000: 设置采样率为 16000Hz
#     -ac 1: 设置为单声道（如果需要双声道可移除此项）
#     -y: 覆盖已存在的文件
#     """
#     command = [
#         'ffmpeg',
#         '-i', video_path,
#         '-vn',
#         '-ar', '16000',
#         '-y',
#         output_path
#     ]
#     try:
#         # 执行命令并捕获错误
#         subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         print(f"成功处理: {os.path.basename(video_path)}")
#     except subprocess.CalledProcessError as e:
#         print(f"处理失败: {os.path.basename(video_path)}, 错误原因: {e}")

def extract_audio(video_path, output_path):
    """
    优化后的音频提取函数
    -af "aresample=async=1": 强制音频时间戳同步，解决末尾截断问题
    -map 0:a:0: 明确指定提取第一个音频流
    """
    command = [
        'ffmpeg',
        '-i', video_path,
        '-map', '0:a:0',           # 明确映射音频流
        '-af', 'aresample=async=1', # 核心修复：解决同步和截断问题
        '-ar', '16000',            # 采样率
        '-ac', '1',                # 单声道
        '-y',                      # 覆盖输出
        output_path
    ]
    try:
        # 使用 stderr 捕获可能的警告信息
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ 成功处理: {os.path.basename(video_path)}")
    except subprocess.CalledProcessError as e:
        print(f"❌ 处理失败: {os.path.basename(video_path)}")
        print(f"错误信息: {e.stderr}")
        
def batch_process(path1, path2, max_workers=4):
    # 如果输出目录不存在则创建
    if not os.path.exists(path2):
        os.makedirs(path2)

    # 定义支持的视频后缀
    video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv')
    
    # 筛选 path1 下的所有视频文件
    tasks = []
    for filename in os.listdir(path1):
        if filename.lower().endswith(video_extensions):
            video_path = os.path.join(path1, filename)
            # 构造输出文件名：原名.wav
            name_without_ext = os.path.splitext(filename)[0]
            output_path = os.path.join(path2, f"{name_without_ext}.wav")
            tasks.append((video_path, output_path))

    # 使用线程池进行多线程处理
    print(f"开始处理，总计任务数: {len(tasks)}")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for video_path, output_path in tasks:
            executor.submit(extract_audio, video_path, output_path)

if __name__ == "__main__":
    # 配置路径
    path1 = "/dfs/data/BAH/data_testset/data/crop_along_time_5/Videos"  # 视频源路径
    path2 = "/dfs/data/BAH/data_testset/data/crop_along_time_5/Audios"  # 音频保存路径
    
    # 执行批处理（max_workers 为线程数，建议根据 CPU 核心数设置）
    batch_process(path1, path2, max_workers=16)
