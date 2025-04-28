import subprocess
import os
import json
import random
import re
import src.audio_convert as audio_convert
from src.gpt_app import RenContent
from src.audio_convert import AudioConvert
from src.image_convert import ImageConvert
from src.effect import transition , effect
from PIL import Image



class VideoRender:
    def __init__(self):
        print("bo may dang dc goi")
        self.ffmpeg_path = os.path.join("bin", "ffmpeg")
        self.ffprobe_path = os.path.join("bin", "ffprobe")
        self.font_path =  "/System/Library/Fonts/Supplemental/Arial.ttf"

        self.image_urls = []
        self.image_input = []
        self.audio_text = []
        self.audio_input = []
        self.transition = transition
        self.effect = effect

        self.video_secment =  []

        self.video_fps = 60

       
        self.rencontent =RenContent()
        self.audio_convert = AudioConvert()
        self.imageConvert = ImageConvert()
        

    def getData(self , url):
        self.rencontent.get_content(url)

        with open('data/content.txt', 'r', encoding='utf-8') as file:
            data = json.load(file)
            for key, value in data.items():
                self.audio_text.append(value["content"])
                self.image_urls.append(value["url"])
            
            for i in range(len(self.audio_text)):
                audiopath = f"data/audios/audio{i}.mp3"
                # print(self.audio_text[i])
                self.audio_convert.creat_audio(text= self.audio_text[i] , out_path= audiopath)
                self.audio_input.append(audiopath)

            for i in range(len(self.image_urls)):
                path = "data/images"
                imagepath = self.imageConvert.download_image_and_convert( i , self.image_urls[i] , path)
                self.image_input.append(imagepath)
                # print(self.image_urls[i])

    

    def get_audio(self , text , audio_path):
        return self.audio_convert.creat_audio(text= text , out_path= audio_path)
    
    def set_offset(self , video_path , offset):
        duration = self.get_video_duration(video_path)

        while(offset > duration):
            offset /= 2

        return float(duration - offset)
    
    def set_xfade(self , type , duration , offset , video_path):

        ros = self.set_offset(video_path , offset)
        return f"xfade=transition={type}:duration={duration}:offset={ros}"
        


    def get_audio_duration(self, audio_path):
        result = subprocess.run([
            self.ffprobe_path,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout.decode().strip())
    

    def get_video_duration(self,video_path):
        result = subprocess.run([
            self.ffprobe_path, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return float(result.stdout.decode().strip())
    
    def get_video_fps(self, video_path):
        result = subprocess.run([
            self.ffprobe_path,
            "-v", "0",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "default=nokey=1:noprint_wrappers=1",
            video_path
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        fps_str = result.stdout.decode().strip()  # ví dụ: "30/1"
        num, denom = map(int, fps_str.split('/'))
        return num / denom
    def escape_drawtext(self , text):
        return (
            text.replace("'", "’")          # tránh lỗi nháy đơn
                .replace('"', '”')          # tránh lỗi nháy kép nếu có
                .replace(':', '\\:')        # escape `:` cho filter parser
                .replace('\n', ' ')         # bỏ dòng nếu có
    )
    def extract_number(self,path):
        name = os.path.basename(path)
        match = re.search(r'\d+', name)
        return int(match.group()) if match else -1
    
    def resize_image(self , image , ratio):
        folder = os.path.dirname(image)
        basename  = os.path.basename(image)
        name, ext = os.path.splitext(basename)
        tmp_path = os.path.join(folder , f"tmp_{name}{ext}")

        scale_expr = (
        f"scale='trunc(iw*{ratio}/2)*2':'trunc(ih*{ratio}/2)*2'"
    )
        cmd = [
            self.ffmpeg_path , 
            "-i" , image ,
            "-vf" , scale_expr,
            "-frames:v", "1",  
            tmp_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            print("❌ Resize failed")
            print(result.stderr.decode())
            return

        if not os.path.exists(tmp_path):
            print("❌ Temp file not created")
            return

        print(f"✅ Resized: {tmp_path}")
        os.replace(tmp_path, image)
    
    def create_back(self , image):
        filter_complex = (
            "scale=-1:1920,crop=1080:1920:(iw-1080)/2:0,boxblur=10"
        )    

        out = "blur.jpeg"
        cmd = [
            self.ffmpeg_path , "-y" ,
            "-i" , image ,
            "-filter_complex" , filter_complex, 
            "-frames:v" ,  "1" ,
            out
        ]
        subprocess.run(cmd)
        return out
        
        

    def get_image_resolution(self ,image_path):
        with Image.open(image_path) as img:
            return img.width, img.height
        
    def build_drawtext(self , text , audio_path):
        duration = self.get_audio_duration(audio_path)
        text_filter_complex = []

        letters = text.split(" ")
        i = 0 
        count = 0 
        str = ""
        time = 0
        while(i < len(letters)):
            escaped_text = letters[i].replace(":", '\\:').replace("'", "\\'")
            str += escaped_text + " "
            i += 1
            count+= 1

            if(i%5 == 0 or i == len(letters)) :
                time_life = duration*(count / len(letters))
                count  = 0
                drawtext = (
                    f"[vtxt]drawtext=text='{str.strip()}':"
                    f"fontfile='{self.font_path}':"
                    f"fontcolor=white:fontsize=60:borderw=4:bordercolor=black:"
                    f"x=(w-text_w)/2:y=h-500:"
                    f"enable='between(t,{time},{time + time_life})'"
                )
                if i != len(letters):
                    drawtext += "[vtxt];"
                else:
                    drawtext += "[out]"

                time += time_life
                str = ""
                text_filter_complex.append(drawtext)
        return "".join(text_filter_complex)

        

            


    def creat_video(self , index, audiopath, imagepath ):
        # frame_count = int(duration * self.video_fps)
        img_w , img_h = self.get_image_resolution(imagepath)
        ratio = (1920*1/2)/img_h

        self.resize_image(imagepath , ratio)
        img_w , img_h = self.get_image_resolution(imagepath)
        duration = self.get_audio_duration(audiopath)
        
        output_file = f"data/videos/segment_{index}.mp4"

        # Zoom nhẹ + caption
        safe_text= self.escape_drawtext(self.audio_text[index])
        draw_text = self.build_drawtext(safe_text , audiopath)
        print(draw_text)
        filter_complex = (
            f"[0:v]scale=-1:2500,zoompan=z='min(max(zoom,pzoom)+0.0015,1.5)':d=600:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={img_w}x{img_h}[z];"
            "[1:v][z]overlay=(W-w)/2:'(H-h)/2-100'[vtxt]" +";" + draw_text 
        )    
        
        background = self.create_back(imagepath)

        return output_file , [
            self.ffmpeg_path, "-y",
            "-loop", "1",
            "-i", imagepath,
            "-i" , background,
            "-t", str(duration),
            "-filter_complex", filter_complex,
            "-map" , "[out]" ,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            output_file
        ]
    
    def create_segment_videos(self):
        
        for i in range(len(self.image_input)):
            out , cmd = self.creat_video(i, self.audio_input[i], self.image_input[i])
            (subprocess.run(cmd))
            self.video_secment.append(out)

    def merge_video(self):

        
        filter_complex_parts = []
        input_cmds = []
        xfade_steps = []
        audio_inputs = []


        duration = 2
        offset = 0
        outpath = "data/outputvideos"
        i = len(os.listdir(outpath) ) + 1
        final_output = f"data/outputvideos/final_output{i}.mp4"


        # 1. Thêm input và định dạng từng video
        for i, video in enumerate(self.video_secment):
            input_cmds.extend(["-i", video])
            input_cmds.extend(["-i", self.audio_input[i]])
             
            filter_complex_parts.append(f"[{i*2}:v]format=yuva420p[v{i}]")
            audio_inputs.append(f"[{i*2+1}:a]")

        # 2. Tạo chuỗi xfade
        last_output = "[v0]"
        for i in range(1, len(self.video_secment)):
            fade = random.choice(self.transition)
            prev_video = self.video_secment[i - 1]
            offset += self.get_video_duration(prev_video) - duration
            tag_out = f"[vxf{i}]"
            xfade = f"{last_output}[v{i}]xfade=transition={fade}:duration={duration}:offset={round(offset, 3)}{tag_out}"
            xfade_steps.append(xfade)
            last_output = tag_out  # dùng làm input cho bước tiếp theo

        # 3. Gộp filter_complex
        audio_concat = "".join(audio_inputs) + f"concat=n={len(self.video_secment)}:v=0:a=1[aout]"

        filter_complex = ";".join(filter_complex_parts + xfade_steps + [audio_concat] )

        # 4. Tạo lệnh ffmpeg
        cmd = [
            self.ffmpeg_path, "-y",
            *input_cmds,
            "-filter_complex", filter_complex,
            "-map", last_output,
            "-map", "[aout]",
            "-c:v", "libx264",
            "-b:a", "192k",
            "-crf", "18",
            "-preset", "veryfast",
            "-movflags", "+faststart", 
            "-pix_fmt", "yuv420p",
            final_output
        ]

        print("🎬 filter_complex:\n", filter_complex)
        subprocess.run(cmd)
        return final_output
    
    def clear_data(self):
        self.audio_input = sorted(
            [f"data/audios/{f}" for f in os.listdir("data/audios") if f.lower().endswith(".mp3")],
            key=self.extract_number
        )

        self.image_input = sorted(
            [f"data/images/{f}" for f in os.listdir("data/images") if f.lower().endswith(".jpeg")],
            key=self.extract_number
        )
        self.video_secment = sorted(
            [f"data/videos/{f}" for f in os.listdir("data/videos") if f.lower().endswith(".mp4")],
            key=self.extract_number
        )
        all_files = self.image_input + self.audio_input + self.video_secment

        for path in all_files:
            if os.path.exists(path):
                os.remove(path)
                print(f"✅ Deleted: {path}")
            else:
                print(f"⚠️ Not found: {path}")

        self.audio_text = []
        self.image_urls = []
    
    def creat_final_video(self , url):
        try:
            self.getData(url)
        except Exception as e:
            print(e)

        try:
            self.create_segment_videos()
        except Exception as e:
            print(e)

        try:
            self.merge_video()
        except Exception as e:
            print(e)

        
        self.clear_data()




