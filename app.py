import os
import subprocess
import re
import math
from flask import Flask, request, render_template, send_file

app = Flask(__name__)
VIDEOS_DIR = "videos"


def compress_video(input_file, codec, rc, bitrate, extra_flag):
    # Define the output file path
    output_file = os.path.join(VIDEOS_DIR, "compressed.mp4")
    
    # Construct the ffmpeg command based on the extra_flag value
    if extra_flag != '':
        cmd = [
            "ffmpeg", "-i", input_file, "-c:v", codec, "-rc", rc, "-b:v", bitrate, extra_flag, "-y", output_file
        ]
    else:
        cmd = [
            "ffmpeg", "-i", input_file, "-c:v", codec, "-b:v", bitrate, "-y", output_file
        ]
    
    # Execute the ffmpeg command
    subprocess.run(cmd, check=True)
    
    # Return the ffmpeg command as a string
    return ' '.join(cmd)

def compress_video_cqp(input_file, codec, rc,qp,bitrate,extra_flag):
    output_file = os.path.join(VIDEOS_DIR, "compressed.mp4")
    print(output_file)
    if extra_flag != '':
        if codec == 'libx265':
            cmd = [
                "ffmpeg", "-i", input_file, "-c:v", codec, "-qp", qp , extra_flag, "-y", output_file
            ]
        else:
            cmd = [
                "ffmpeg", "-i", input_file, "-c:v", codec, "-rc", rc , "-qp", qp , extra_flag, "-y", output_file
            ]            
    else :
        if codec == 'libx265':
            cmd = [
                "ffmpeg", "-i", input_file, "-c:v", codec, "-qp", qp , "-y", output_file
            ]
        else:
            cmd = [
                "ffmpeg", "-i", input_file, "-c:v", codec, "-rc", rc , "-qp", qp, "-y", output_file
            ]          

    if codec != 'libx265':
        cmd_global = 'ffmpeg -i ' + "input.mp4" + ' -c:v ' + codec + ' -rc ' + rc + ' -qp ' + qp  + extra_flag + ' -y '  + ' ' + "output.mp4" 
    else:
        cmd_global = 'ffmpeg -i ' + "input.mp4" + ' -c:v ' + codec + ' -qp ' + qp  + extra_flag + ' -y '  + ' ' + "output.mp4" 
    subprocess.run(cmd, check=True)
    return cmd_global

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
    psnr_avg_total = psnr_sum / psnr_count
    psnr_avg_total = round(psnr_avg_total, 2)
    return psnr_avg_total

def get_comp_ratio(input_file, output_file):
    input_file_size = os.path.getsize(input_file)
    output_file_size = os.path.getsize(output_file)
    compression_ratio = input_file_size / output_file_size
    
    returnval = round(compression_ratio, 2)
    return returnval,input_file_size,output_file_size


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/compress_video", methods=[ "POST"])
def compress_video_handler():

    coutput_file =os.path.join(VIDEOS_DIR, "original.mp4")
    cin_file =os.path.join(VIDEOS_DIR, "compressed.mp4")
    if os.path.exists(coutput_file):
        os.remove(coutput_file)
    if os.path.exists(cin_file):
        os.remove(cin_file)



    if request.method == "POST":
        if "video" not in request.files:
            return "No video file selected", 400
        video_file = request.files["video"]
        if video_file.filename == "":
            return "No video file selected", 400
        video_file.save(os.path.join(VIDEOS_DIR, "original.mp4"))

        #form input
        codec = request.form.get("codec")
        bitrate = request.form.get("bitrate")
        extra_flag = request.form.get("extra_flag")
        input_file = os.path.join(VIDEOS_DIR, "original.mp4")
        rc = request.form.get("RC")
        if rc != 'cbr':
            qp = request.form.get("qp")
            cmd = compress_video_cqp(input_file, codec,rc,qp,bitrate,extra_flag)
        else:
            cmd = compress_video(input_file, codec,rc,bitrate,extra_flag)
        
        output_file = os.path.join(VIDEOS_DIR, "compressed.mp4")

        psnr= get_video_stats(input_file, output_file)
        ratio,in_size,out_size = get_comp_ratio(input_file, output_file)
        cmd_string = cmd

        return render_template("compressed.html", psnr=psnr, ratio=ratio, cmd=cmd_string,insize=in_size,outsize=out_size)
    return render_template("index.html")

@app.route('/<path:filename>')
def original_video(filename):
    return send_file(os.path.join(VIDEOS_DIR, filename), as_attachment=True)

@app.route('/<path:filename>')
def compressed_video(filename):
    return send_file(os.path.join(VIDEOS_DIR, filename), as_attachment=True)

if __name__ == "__main__":
    app.run()
