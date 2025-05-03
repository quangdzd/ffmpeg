import tkinter as tk
from tkinter import ttk, filedialog
from src.video_render import VideoRender



class Gui:
    def __init__(self, root):
        root.title("GPT + TTS GUI")
        root.geometry("1080x720")

        # Tabs
        tab_control = ttk.Notebook(root)
        self.config_tab = ttk.Frame(tab_control)
        self.app_tab = ttk.Frame(tab_control)

        tab_control.add(self.config_tab, text='Config')
        tab_control.add(self.app_tab, text='App')
        tab_control.pack(expand=1, fill='both')

        self.create_config_tab()
        self.create_app_tab()
        self.videoRender = VideoRender()

    def create_config_tab(self):
        # GPT API Key input
        ttk.Label(self.config_tab, text="GPT API Key:").pack(pady=(20, 5))
        self.api_entry = ttk.Entry(self.config_tab, width=80)
        self.api_entry.pack(pady=(0, 20))

        # Button to load tts.json
        self.tts_path_label = ttk.Label(self.config_tab, text="Chưa chọn file tts.json")
        self.tts_path_label.pack(pady=5)
        ttk.Button(self.config_tab, text="Chọn file tts.json", command=self.choose_tts_file).pack()

    def create_app_tab(self):
        # URL input
        ttk.Label(self.app_tab, text="URL:").pack(pady=(20, 5))
        self.url_entry = ttk.Entry(self.app_tab, width=80)
        self.url_entry.pack(pady=(0, 20))

        # Render button
        ttk.Button(self.app_tab, text="Render", command=self.render).pack(pady=10)

    def choose_tts_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.tts_path_label.config(text=f"Đã chọn: {file_path}")
            self.tts_file = file_path
        else:
            self.tts_path_label.config(text="Không chọn file nào")

    def render(self):
        url = self.url_entry.get()
        # self.videoRender.creat_final_video(url)



