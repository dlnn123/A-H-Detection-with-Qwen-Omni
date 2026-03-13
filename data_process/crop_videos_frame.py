import cv2
import os
import glob

def process_video(input_path, output_path, target_frames=100):
    """
    处理单个视频：均匀抽帧至指定帧数
    :param input_path: 原视频路径
    :param output_path: 输出视频路径
    :param target_frames: 目标帧数（默认100）
    """
    # 打开视频
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"❌ 无法打开视频：{input_path}")
        return

    # 获取视频基础信息
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 帧数不足100，直接关闭返回（不处理）
    if total_frames <= target_frames:
        print(f"✅ 视频帧数({total_frames}) ≤ 100，无需抽帧：{os.path.basename(input_path)}")
        cap.release()
        return

    # 计算抽帧间隔（均匀抽帧核心）
    frame_interval = total_frames / target_frames
    print(f"🎬 开始处理：{os.path.basename(input_path)} | 总帧数：{total_frames} | 抽帧间隔：{frame_interval:.2f}")

    # 定义视频编码器（MP4格式）
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # 均匀抽帧写入新视频
    frame_count = 0
    saved_count = 0
    while saved_count < target_frames:
        # 设置读取位置（均匀采样）
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_count))
        ret, frame = cap.read()
        if not ret:
            break

        # 写入帧
        out.write(frame)
        saved_count += 1
        frame_count += frame_interval

    # 释放资源
    cap.release()
    out.release()
    # cv2.destroyAllWindows()

    # 删除原文件
    try:
        os.remove(input_path)
        print(f"🗑️ 原视频已删除：{os.path.basename(input_path)}")
        print(f"✅ 抽帧完成：{os.path.basename(output_path)}\n")
    except Exception as e:
        print(f"❌ 删除原文件失败：{e}\n")

def batch_process_videos(folder_path, target_frames=100):
    """
    批量处理文件夹下所有MP4视频
    :param folder_path: 视频文件夹路径
    """
    # 获取文件夹下所有MP4文件
    video_files = glob.glob(os.path.join(folder_path, "*.mp4"))
    if not video_files:
        print("⚠️ 文件夹中未找到MP4视频文件")
        return

    print(f"📂 共找到 {len(video_files)} 个MP4视频，开始批量处理...\n")
    for video_path in video_files:
        # 生成输出文件名（原文件名_crop.mp4）
        dir_name = os.path.dirname(video_path)
        file_name = os.path.splitext(os.path.basename(video_path))[0]
        output_video = os.path.join(dir_name, f"{file_name}_crop.mp4")

        # 处理视频
        process_video(video_path, output_video, target_frames)

# ====================== 主程序配置 ======================
if __name__ == "__main__":
    # 【修改这里】替换为你的视频文件夹路径
    VIDEO_FOLDER_PATH = "/dfs/data/BAH/data_test/crop_along_frame/videos/no_AH"  # Windows示例
    # VIDEO_FOLDER_PATH = "/home/user/videos"  # Linux/Mac示例

    # 开始批量处理
    batch_process_videos(VIDEO_FOLDER_PATH, target_frames=100)