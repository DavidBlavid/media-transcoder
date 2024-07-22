import subprocess
import json
import os
from Media import Media


############### PARAMETERS ###############
# base path to your media folder
base_path = 'E:/Media/'

# GPU support is only available for NVIDIA GPUs with CUDA installed
# read this first: https://docs.nvidia.com/video-technologies/video-codec-sdk/12.0/ffmpeg-with-nvidia-gpu/index.html
USE_GPU = False
##########################################



video_fileextensions = [".mp4", ".mkv", ".avi", ".webm", ".flv", ".mov", ".wmv", ".mpg", ".mpeg", ".m4v", ".3gp"]
incorrect_files = []

def process_folder(folder_path):

    print(f"Processing: {folder_path}")

    # get all files in the folder
    files = os.listdir(folder_path)

    # find all files with .temp.mp4 extension and delete them
    temp_files = [f for f in files if f.endswith(".temp.mp4")]

    for temp_file in temp_files:
        temp_file_path = os.path.join(folder_path, temp_file)
        os.remove(temp_file_path)

    # filter out only the video files
    video_files = [f for f in files if os.path.splitext(f)[1].lower() in video_fileextensions]

    for video_file in video_files:
        video_path = os.path.join(folder_path, video_file)
        process_video(video_path)
    
    # get all subfolders in the folder
    subfolders = [f for f in files if os.path.isdir(os.path.join(folder_path, f))]

    for subfolder in subfolders:
        process_folder(os.path.join(folder_path, subfolder))


def process_video(video_path):
    
    media: Media | None = Media.from_ffprobe(video_path)

    if media is None:
        print(f"Skipping ⏭️: {media.filepath}")
        return

    if not media.is_valid():
        print(f"Converting 🔄: {media.filepath}")
        media.convert(use_gpu=USE_GPU)

        # re-check if conversion was successful
        media = Media.from_ffprobe(media.filepath)
        
        if media.is_valid():
            print(f"Converted ✅: {media.filepath}")
        else:
            print(f"Failed! ❌: {media.filepath}")
            incorrect_files.append(media.filepath)
    
    else:
        print(f"Valid ✅: {media.filepath}")

if __name__ == "__main__":
    process_folder(base_path)

    print("Incorrect files:")
    for file in incorrect_files:
        print(file)