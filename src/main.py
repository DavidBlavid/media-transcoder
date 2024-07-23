import os
from misc import update_line, CMD_COLORS
from Media import Media


############### PARAMETERS ###############
# base path to your media folder
base_path = 'E:/Media'

# GPU support is only available for NVIDIA GPUs with CUDA installed
# read this first: https://docs.nvidia.com/video-technologies/video-codec-sdk/12.0/ffmpeg-with-nvidia-gpu/index.html
USE_GPU = True
##########################################

video_fileextensions = [".mp4", ".mkv", ".avi", ".webm", ".flv", ".mov", ".wmv", ".mpg", ".mpeg", ".m4v", ".3gp"]

def process_folder(folder_path):

    # get all files in the folder
    files = os.listdir(folder_path)

    # find all files with .temp.mp4 extension and delete them
    temp_files = [f for f in files if f.endswith(".temp.mp4")]

    # filter out only the video files
    video_files = [f for f in files if os.path.splitext(f)[1].lower() in video_fileextensions]

    if len(video_files) > 0:
        print(f"\nProcessing: {folder_path}")

    for temp_file in temp_files:
        temp_file_path = os.path.join(folder_path, temp_file)
        os.remove(temp_file_path)

    for video_file in video_files:
        video_path = os.path.join(folder_path, video_file)
        process_video(video_path)
    
    # recursively process subfolders
    subfolders = [f for f in files if os.path.isdir(os.path.join(folder_path, f))]

    for subfolder in subfolders:
        process_folder(os.path.join(folder_path, subfolder))


def process_video(video_path):
    
    media: Media | None = Media.from_ffprobe(video_path)

    # we skip temporary files
    if media is None:
        return

    if not media.is_valid():
        print(f"🔄 {CMD_COLORS["blue"]} Converting: {CMD_COLORS["reset"]} {media.get_filename()}")

        # here we actually convert the video
        media.convert(use_gpu=USE_GPU)

        update_line(f"✅ {CMD_COLORS["green"]} Valid: {CMD_COLORS["reset"]} {media.get_filename()}")
    
    else:
        print(f"✅ {CMD_COLORS["green"]} Valid: {CMD_COLORS["reset"]} {media.get_filename()}")

if __name__ == "__main__":
    process_folder(base_path)

    print("\n✅ Done!")