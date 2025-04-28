import os
import json
import tkinter as tk
import pandas as pd
from src.video_render import VideoRender
from src.gui_app import Gui
from src.ArticleExtractor import get_new_links
from urllib.parse import urlparse




def main():

    sites = "sites.csv"
    df = pd.read_csv("sites.csv", sep=';', encoding='utf-8-sig')
    pages = df["link_page"]
    csv_paths = df["csv_path"]

    for i, (page, csv_path) in enumerate(zip(pages, csv_paths)):
        if csv_path == "":
            domain = urlparse(page).netloc.replace('.', '_')
            csv_path = f"{domain}_page_{i}.csv"
            # Cập nhật lại vào DataFrame
            df.at[i, "csv_path"] = csv_path

        print(f"🔹 Đang xử lý dòng {i}: {page} -> {csv_path}")
        links = get_new_links(page, csv_path)
        print(links)

    # Ghi lại file sites.csv sau khi đã cập nhật
    df.to_csv(sites, sep=';', index=False, encoding='utf-8-sig')




    # root = tk.Tk()
    # app = Gui(root)
    # root.mainloop()



if __name__ == "__main__":
    main()