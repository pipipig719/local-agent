import os
import re
from f5_tts.api import F5TTS


class TTS:
    def __init__(self):
        vocab_path = os.path.join(os.path.dirname(__file__), "vocab.txt")
        model_path = os.path.join(os.path.dirname(__file__), "model_1200000.safetensors")
        self.tts = F5TTS(
            vocab_file=vocab_path,
            ckpt_file=model_path
        )

    def generate(self, text: str):
        """
        根据输入文本生成语音，返回采样率和语音数据
        """
        wav_path = os.path.join(os.path.dirname(__file__), "basic_ref_zh.wav")
        wav, sr, spect = self.tts.infer(
            ref_file=wav_path,
            ref_text="对，这就是我，万人敬仰的太乙真人。",
            gen_text=text,
            seed=-1,
            speed=1.5
        )
        return sr, wav
