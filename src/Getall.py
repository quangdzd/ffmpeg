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


# 🔑 Set API key OpenAI (bạn cần set đúng key)
client = OpenAI()
# 🔗 URL bài báo CNN
url = "https://edition.cnn.com/2025/04/10/politics/trump-xi-china-tariffs/index.html"

# 📰 Tải & phân tích bài báo
article = Article(url)
article.download()
article.parse()

images = list(article.images)
title = article.title

with open("test.txt" , "w") as a:
    a.write(article.text)