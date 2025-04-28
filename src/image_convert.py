import requests
import os
import subprocess
import shutil
from PIL import Image
from io import BytesIO

class ImageConvert:
    def __init__(self):
        self.ffmpeg_path = os.path.join("bin", "ffmpeg")
        self.cache = {}

    def convert_to_png(self, input_path):
        output_path = os.path.splitext(input_path)[0] + ".png"
        cmd = [
            self.ffmpeg_path,
            "-y",  # Ghi đè nếu file đã tồn tại
            "-i", input_path,
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"🖼️ Đã chuyển sang PNG: {output_path}")

   
    def download_image_and_convert(self , index, url, save_dir):
        try:
            if url in self.cache:
                ext = os.path.splitext(self.cache[url])[1]  # lấy đuôi từ file cũ
                filename = f"image{index}{ext}"
                save_path = os.path.join(save_dir, filename)
                shutil.copyfile(self.cache[url], save_path)
                print(f"🔁 Dùng lại ảnh: {os.path.basename(self.cache[url])} → {filename}")
                return save_path
            

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Referer": "https://www.cnn.com/",  # Quan trọng với server như CNN
                "Accept-Language": "en-US,en;q=0.9",
                "DNT": "1",  # Do Not Track
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            img = Image.open(BytesIO(response.content))
            img_format = img.format.upper()  # ví dụ: 'JPEG', 'PNG'
            ext = f".{img_format.lower()}"   # lưu theo .jpg, .png

            filename = f"image{index}{ext}"
            save_path = os.path.join(save_dir, filename)

            img.save(save_path, format=img_format)
            self.cache[url] = save_path  # lưu lại đường dẫn để copy về sau

            print(f"✅ Đã lưu ảnh {filename}")
            return save_path

        except Exception as e:
            print(f"❌ Lỗi tải ảnh {url}: {e}")
            return None
        
        
