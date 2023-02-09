import os
import subprocess
import re
from flask import Flask, request, render_template, send_file

app = Flask(__name__)
VIDEOS_DIR = "videos"

def compress_video(input_file, codec, bitrate,extra_flag):
    output_file = os.path.join(VIDEOS_DIR, "compressed.mp4")
    if extra_flag != '':
        cmd = [
            "ffmpeg", "-i", "input_file", "-c:v", codec, "-b:v", bitrate, extra_flag, "-y", "output_file"
        ]
    else :
        cmd = [
            "ffmpeg", "-i", input_file, "-c:v", codec, "-b:v", bitrate, "-y", output_file
        ]
    subprocess.run(cmd, check=True)

def get_video_stats(input_file, output_file):
    psnr_log_file = "psnr.log"
    if os.path.exists(psnr_log_file):
        os.remove(psnr_log_file)


    cmd = [
        "ffmpeg", "-i", output_file, "-i", input_file, 
        "-lavfi", "psnr=stats_file=psnr.log", "-f", "null", "-"
    ]
    subprocess.run(cmd, check=True) 
    psnr = None
    psnr_sum = 0
    psnr_count = 0
    
    


    with open(psnr_log_file) as f:
        for line in f:
            match = re.search(r"psnr_avg:(\d+\.\d+)", line)
            if match:
                psnr_avg = float(match.group(1))
                psnr_sum += psnr_avg
                psnr_count+=1
            else:
                print("psnr_avg not found in string")
    return psnr_sum / psnr_count

def get_comp_ratio(input_file, output_file):
    input_file_size = os.path.getsize(input_file)
    output_file_size = os.path.getsize(output_file)
    compression_ratio = input_file_size / output_file_size
    return compression_ratio


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/compress_video", methods=["GET", "POST"])
def compress_video_handler():
    if request.method == "POST":
        if "video" not in request.files:
            return "No video file selected", 400
        video_file = request.files["video"]
        if video_file.filename == "":
            return "No video file selected", 400
        video_file.save(os.path.join(VIDEOS_DIR, "original.mp4"))
        codec = request.form.get("codec")
        bitrate = request.form.get("bitrate")
        extra_flag = request.form.get("extra_flag")
        input_file = os.path.join(VIDEOS_DIR, "original.mp4")
        
        compress_video(input_file, codec,bitrate,extra_flag)
        
        output_file = os.path.join(VIDEOS_DIR, "compressed.mp4")

        psnr = get_video_stats(input_file, output_file)
        ratio = get_comp_ratio(input_file, output_file)
        cmd_string = 'ffmpeg -i ' + input_file + ' -c:v ' + codec + ' -b:v ' + bitrate + ' -y ' + extra_flag + ' ' + output_file

        return render_template("compressed.html", psnr=psnr, ratio=ratio, cmd=cmd_string)
    return render_template("index.html")

@app.route('/videos/<path:filename>')
def original_video(filename):
    return send_file(os.path.join(VIDEOS_DIR, filename), as_attachment=True)

@app.route('/compressed/<path:filename>')
def compressed_video(filename):
    return send_file(os.path.join(VIDEOS_DIR, filename), as_attachment=True)

if __name__ == "__main__":
    app.run()
