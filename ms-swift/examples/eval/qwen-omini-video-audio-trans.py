import torch
import soundfile as sf
from transformers import Qwen3OmniMoeForConditionalGeneration, Qwen3OmniMoeProcessor
from qwen_omni_utils import process_mm_info

MODEL_PATH = "/dfs/data/ms-swift/model/Qwen/Qwen3-Omni-30B-A3B-Instruct"
MODEL_PATH = "/dfs/data/ms-swift/examples/train/output/v11-20260306-105830/checkpoint-120"
# 加载模型（完全按你的官方写法）
model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    torch_dtype="auto",
    device_map="auto",
    attn_implementation="flash_attention_2",
)
    # 你的模型路径（保持不变）

    
processor = Qwen3OmniMoeProcessor.from_pretrained(MODEL_PATH)

# ===================== 你的任务对话（视频 + 音频 + 指令）=====================
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio": "/dfs/data/BAH/data_test/crop_audios/AH/82553_Question_4_2024-08-22_12-18-20_Video_1.wav"},
            {"type": "video", "video": "/dfs/data/BAH/data_test/crop_videos/AH/82553_Question_4_2024-08-22_12-18-20_Video_1.mp4"},
            {"type": "text", "text": "Combine the <video> and <audio> content to analyze whether this video clip exhibits Ambivalence/Hesitancy emotions. Output the answer in the format <answer></answer>, responding only with Yes or No."},
        ],
    },
]


# 官方参数：使用视频中的音频
USE_AUDIO_IN_VIDEO = False

# 推理准备（完全照搬官方写法）
text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
audios, images, videos = process_mm_info(conversation, use_audio_in_video=USE_AUDIO_IN_VIDEO)

inputs = processor(
    text=text, 
    audio=audios, 
    images=images, 
    videos=videos, 
    return_tensors="pt", 
    padding=True, 
    use_audio_in_video=USE_AUDIO_IN_VIDEO
)
inputs = inputs.to(model.device).to(model.dtype)

# ===================== 生成参数微调（关键！）=====================
# 关闭语音输出，只输出文本答案，节省显存
text_ids, audio = model.generate(
    **inputs, 
    # speaker=None,                # 不生成语音
    thinker_return_dict_in_generate=True,
    use_audio_in_video=USE_AUDIO_IN_VIDEO,
    # 生成参数（和你原来vLLM一致）
    temperature=0.3,
    top_p=0.95,
    # top_k=20,
    max_new_tokens=16384,
    do_sample=True,
)

# 解码输出（官方标准写法）
text = processor.batch_decode(
    text_ids.sequences[:, inputs["input_ids"].shape[1] :],
    skip_special_tokens=True,
    clean_up_tokenization_spaces=False
)

# 打印最终答案
print("\n模型输出：")
print(text[0])

    # 不需要输出音频，注释掉
    # if audio is not None:
    #     sf.write(
    #         "output.wav",
    #         audio.reshape(-1).detach().cpu().numpy(),
    #         samplerate=24000,
    #     ) 