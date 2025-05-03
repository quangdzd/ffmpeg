import re
import os
import json
import requests
import pandas as pd
from urllib.parse import urlparse, urldefrag
from bs4 import BeautifulSoup
import trafilatura
import multiprocessing



def run_extract(queue, html_data):
    try:
        text = trafilatura.extract(html_data, include_comments=False, include_tables=False)
        queue.put(text)
    except Exception:
            queue.put(None)

class ArticleExtractor:
    def extract(self, html):

        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=run_extract, args=(queue, html))
        p.start()
        p.join(timeout=3)
        if p.is_alive():
            print("⏰ Trafilatura timeout, kill process")
            p.terminate()
            p.join()
            return None

        text = queue.get()
        if text and len(text.split()) > 100:
            return text.strip()

        # Heuristic fallback
        try:
            soup = BeautifulSoup(html, "html.parser")
            candidates = soup.find_all(["div", "article", "section"])
            for tag in candidates:
                p_tags = tag.find_all("p")
                if len(p_tags) > 5:
                    body_text = " ".join(p.get_text(strip=True) for p in p_tags)
                    if len(body_text.split()) > 100 and not any(
                        k in body_text.lower() for k in ["contact", "advertisement", "cookies"]
                    ):
                        return body_text.strip()
        except Exception as e:
            print(f"⚠️ BeautifulSoup lỗi: {e}")
        return None


class URLClassifier:
    def __init__(self):
        self.article_urls = []
        self.non_article_urls = []

    def collect(self, urls, extractor):
        session = requests.Session()
        headers = {"User-Agent": "Mozilla/5.0"}

        for url in urls:
            print(f"🔍 Đang kiểm tra: {url}")
            try:
                response = session.get(url, timeout=(3, 5), headers=headers)
                html = response.text
                content = extractor.extract(html)
                if content:
                    print("✅ Là bài viết")
                    self.article_urls.append(url)
                else:
                    print("❌ Không phải bài viết")
                    self.non_article_urls.append(url)
            except Exception as e:
                print(f"⚠️ Lỗi khi tải {url}: {e}")
                self.non_article_urls.append(url)

    def learn_patterns(self):
        patterns = []
        for url in self.article_urls:
            path = urlparse(url).path
            if re.search(r"/\d{4}/\d{2}/", path):  # YYYY/MM
                patterns.append(r"/\d{4}/\d{2}/")
            elif "/tin-" in path:
                patterns.append("/tin-")
            elif re.search(r"/[a-z\-]+-\d+\.html", path):
                patterns.append(r"/[a-z\-]+-\d+\.html")
        return list(set(patterns))


class ProfileManager:
    def __init__(self, path='site_profiles.json'):
        self.path = path
        try:
            with open(self.path) as f:
                self.profiles = json.load(f)
        except:
            self.profiles = {}

    def save_profile(self, domain, patterns):
        self.profiles[domain] = {"article_patterns": patterns}
        with open(self.path, 'w') as f:
            json.dump(self.profiles, f, indent=2)

    def get_profile(self, domain):
        return self.profiles.get(domain, {})


def get_new_links(url_page  , csv_path):
    homepage = url_page
    print(f"🌐 Đang lấy trang chủ: {homepage}")
    html = requests.get(homepage, timeout=5).text
    soup = BeautifulSoup(html, "html.parser")

    # Lấy các link hợp lệ
    raw_links = {a["href"] for a in soup.find_all("a", href=True) if a["href"].startswith("http")}
    links = {urldefrag(link)[0] for link in raw_links}
    links = list(links)  # Giới hạn để test nhanh

    try:
        old_df = pd.read_csv(csv_path)
        old_links = set(old_df["Article URLs"].dropna().tolist() + old_df["Non-Article URLs"].dropna().tolist())
    except Exception:
        old_links = set()  # Nếu file chưa tồn tại, giả sử là rỗng

    # Lọc link mới
    tmp = list()
    for link in links:
        if link not in old_links:
            tmp.append(link)

    links = tmp[:5]
        


    # Phân tích
    extractor = ArticleExtractor()
    classifier = URLClassifier()
    classifier.collect(links, extractor)
    patterns = classifier.learn_patterns()

    # Lưu lại pattern học được
    manager = ProfileManager()
    domain = urlparse(homepage).netloc
    manager.save_profile(domain, patterns)

    # Tạo DataFrame
    article_urls = classifier.article_urls
    non_article_urls = classifier.non_article_urls
    max_len = max(len(article_urls), len(non_article_urls))
    article_urls += [""] * (max_len - len(article_urls))
    non_article_urls += [""] * (max_len - len(non_article_urls))

    df = pd.DataFrame({
        "Article URLs": article_urls,
        "Non-Article URLs": non_article_urls
    })

    print("\n✅ Learned Patterns:")
    print(patterns)
    print("\n📄 Detected URLs:")
    print(df)
    write_header = not os.path.exists(csv_path)
    df.to_csv(csv_path, mode='a', header=write_header, index=False)

    print(f"\n💾 Đã lưu kết quả vào {csv_path}")

    return article_urls

# if __name__ == "__main__":
#     multiprocessing.set_start_method("fork")  # Cần thiết trên macOS/Linux
#     main()
