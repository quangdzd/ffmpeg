import os
import re
from collections import Counter
from io import BytesIO


# Bên thứ ba
import requests
import imagehash
from PIL import Image
from newspaper import Article
from openai import OpenAI


class RenContent:
    def __init__(self):
        self.url = ""

    # 📰 Tải & phân tích bài báo
    def get_newspaper(self):
        article = Article(self.url)
        article.download()
        article.parse()

        return article.title , article.text , article.images
    
    #Tạo bộ lọc ảnh
    def is_image_large_enough(self ,url, min_width=200, min_height=200):
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            return img.width >= min_width and img.height >= min_height
        except:
            return False

    def get_image_hash(self , url):
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content)).convert("RGB")
            return str(imagehash.phash(img))  # hoặc dhash/average_hash nếu muốn
        except:
            return None

    def filter_images(self , images):
        filtered = []
        exclude_keywords = [
            "logo",         # loại ảnh có từ logo
            "icon",         # loại icon nhỏ
            "sprite",       # ảnh nhỏ gộp nhiều thành phần
            "thumb",        # ảnh thumbnail
            "ads",          # ảnh quảng cáo
            "facebook", "twitter", "instagram",  # mạng xã hội
            "tracking",     # ảnh theo dõi, analytic
            "pixel",        # ảnh nhỏ 1x1 dùng để track
            "small",        # ảnh quá nhỏ
            "footer", "header",  # ảnh giao diện web
            "branding", "badge", "button",
            ".svg", ".gif"  
        ]
        hashes = set()
        for url in images:
            if any(kw in url.lower() for kw in exclude_keywords):
                continue
            if not self.is_image_large_enough(url):
                continue
            img_hash = self.get_image_hash(url)
            if img_hash and img_hash not in hashes:
                hashes.add(img_hash)
                filtered.append(url)
        return filtered



    # 🧠 Tóm tắt nội dung bằng GPT

    # ---------------- STEP 1: GỬI ẢNH CHO GPT-4o ---------------- #
    def analyze_images_with_gpt4o(self , title, images):
        url_list_text = "\n".join([f"{i+1}. {url}" for i, url in enumerate(images)])
        prompt = f"""
        Tiêu đề bài báo: "{title}"

        Bạn sẽ được cung cấp một loạt ảnh dưới đây.
        {url_list_text}

        👉 Yêu cầu:
        - Mô tả nội dung tổng quát của từng ảnh (bối cảnh, hoạt động, vật thể nổi bật...).
        - Không cần mô tả người cụ thể, không nhận dạng khuôn mặt hoặc cảm xúc.
        - Kết quả trả về theo đúng định dạng:

        url: 'URL ảnh đúng như tôi gửi'
        mô tả: 'mô tả ảnh'
        """

    # Gộp nội dung prompt + từng ảnh
        content = [{"type": "text", "text": prompt}] + [
            {"type": "image_url", "image_url": {"url": url}} for url in images
        ]

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là một trợ lý AI chuyên mô tả ảnh minh hoạ trong bài báo, chỉ mô tả tổng thể, không phân tích con người."
                },
                {
                    "role": "user",
                    "content": content
                }
            ]
        )
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens
        cost = (input_tokens * 0.0025 / 1000) + (output_tokens * 0.01 / 1000)
        print(f"\n[BƯỚC 1 - GPT-4o]")
        print(f"Input tokens: {input_tokens}")
        print(f"Output tokens: {output_tokens}")
        print(f"Total tokens: {total_tokens}")
        print(f"Ước tính chi phí: ${cost:.5f}")
        return response.choices[0].message.content

    # ---------------- STEP 2: GỬI VĂN BẢN CHO GPT-4o MINI ---------------- #
    def summarize_and_map_with_gpt4o_mini(self , title ,text, image_descriptions):
        prompt = f"""
                Tiêu đề bài báo: {title}

                Dưới đây là toàn bộ nội dung bài báo:
                \"\"\"
                {text}
                \"\"\"

                Dưới đây là mô tả chi tiết của các ảnh minh hoạ:
                \"\"\"
                {image_descriptions}
                \"\"\"

                👉 Nhiệm vụ của bạn:
                - Tóm tắt nội dung bài về khoảng 150 - 200 từ nhưng vẫn đầy đủ nội dung
                - Chia nội dung thành nhiều đoạn , mội đoạn 20 - 30 từ
                - Với nội dung mỗi đoạn gán với 1 hình ảnh được mô tả ở trên , không cần chính xác , đại khái về nội dung là được
                - 2 đoạn nội dung liền kề nhau thì không dùng chung ảnh nếu có nhiều hơn url ảnh 
                -- Ngôn ngữ của bài viết là **tiếng Anh**, vì vậy phần `"content"` trong kết quả **phải được viết bằng tiếng Anh**, không dịch sang tiếng Việt.
                - Hãy xuất kết quả **duy nhất** ở dạng **một dictionary JSON chuẩn**, đúng định dạng dưới đây:
                ---- Không có '''json ở đầu - gửi nội dung chỉ theo định dạng ở dưới
                
                {{
                    "1": {{
                        "des": "...",
                        "url": "...",
                        "content": "..."
                    }},
                    "2": {{
                        ...
                    }},
                    .....
                    }}
                """
                
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Cực rẻ nhưng vẫn thông minh
            messages=[
                {"role": "system", "content": "Bạn là trợ lý AI giúp chia nội dung báo thành các phần theo ảnh minh hoạ."},
                {"role": "user", "content": prompt}
            ]
        )
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens
        cost = (total_tokens * 0.00015)  # gpt-4o-mini = 0.15 USD / 1M tokens
        print(f"\n[BƯỚC 2 - GPT-4o MINI]")
        print(f"Input tokens: {input_tokens}")
        print(f"Output tokens: {output_tokens}")
        print(f"Total tokens: {total_tokens}")
        print(f"Ước tính chi phí: ${cost:.5f}")
        return response.choices[0].message.content

    # ▶️ Gọi GPT-4o mini để chia nội dung + ảnh

    def get_content(self , url):
        self.url = url
        title , text , images = self.get_newspaper()
        

        images = self.filter_images(images)

        image_analysis_result = self.analyze_images_with_gpt4o(title, images)


        
        print(image_analysis_result)

        final_summary = self.summarize_and_map_with_gpt4o_mini(title,text, image_analysis_result)
        print(final_summary)

        with open("data/content.txt" , "w") as content :
            content.write(final_summary)




