import subprocess
import json
import os
from Media import Media
from tqdm import tqdm

video_fileextensions = [".mp4", ".mkv", ".avi", ".webm", ".flv", ".mov", ".wmv", ".mpg", ".mpeg", ".m4v", ".3gp"]

################################
base_path = 'E:/Media'
VERBOSE = False
################################

invalid_files = []

def process_folder(folder_path):

    # get all files in the folder
    files = os.listdir(folder_path)

    # filter out only the video files
    video_files = [f for f in files if os.path.splitext(f)[1].lower() in video_fileextensions]

    for video_file in video_files:
        video_path = os.path.join(folder_path, video_file)
        print_valid(video_path)
    
    # get all subfolders in the folder
    subfolders = [f for f in files if os.path.isdir(os.path.join(folder_path, f))]

    for subfolder in subfolders:
        process_folder(os.path.join(folder_path, subfolder))

def print_valid(video_path):
    
    media = Media.from_ffprobe(video_path)

    # ignore temporary files
    if media is None:
        return

    filename = media.get_filename()
    valid = media.is_valid()
    emoji = "✅" if valid else "❌"

    print(f'{emoji} {filename}')

    if not valid:
        if VERBOSE:
            print()
            print(media)

        invalid_files.append(video_path)



if __name__ == "__main__":
    process_folder(base_path)

    print()

    if len(invalid_files) > 0:
        print(f"❌ {len(invalid_files)} invalid files found:")
        for file in invalid_files:
            print(file)
    else:
        print("✅ All files are valid!")