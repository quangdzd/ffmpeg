import os
import time
from google.cloud import texttospeech

class AudioConvert:
    def __init__(self):
        try:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bin/lib/tts.json"
            print("🔍 Đang tạo TTS Client...")
            self.client = texttospeech.TextToSpeechClient()
            print("✅ Tạo client thành công")
        except Exception as e:
            print("❌ Lỗi khi tạo client:", e)
        self.voice = texttospeech.VoiceSelectionParams(
                language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
        self.audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )


    def creat_audio(self , text , out_path ):
        synthesis_input = texttospeech.SynthesisInput(text = text)
        response = self.client.synthesize_speech(
        input=synthesis_input, voice=self.voice, audio_config=self.audio_config
        )
        with open(out_path , "wb") as out:
            out.write(response.audio_content)

# if __name__ == "__main__":
#     start = time.time()
#     audio = AudioConvert()
#     audio.creat_audio("This is a test audio", "test.mp3")
#     end = time.time()
#     print(f"⏱️ Tạo file âm thanh mất: {end - start:.2f} giây")