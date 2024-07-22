# Media Transcoder

This Python program allows you to convert video files into a format that is compatible with Plex streaming. By transcoding your videos locally, you can ensure that they are in the optimal format before moving them to your Plex server. This is useful for users whose plex servers are not powerful enough to transcode videos on-the-fly.

## Format
- Container: MP4
- File Extension: .mp4
- Video Codec: H.264 (level 4.0)
- Audio Codec: AAC (2.0 audio)
- Audio Channels: 2

## Dependencies
- [FFmpeg](https://ffmpeg.org/) in your PATH


## Usage
1. Set your base folder in main.py
2. Run the program (`python main.py`)

The program will recursively convert all video files in the base folder and its subfolders. Original files will be **replaced** with the transcoded files.

To check which files are in the correct format, run `python scanner.py`.

## GPU Support
This program supports GPU conversion for NVIDIA GPUs. To enable GPU support, set the `use_gpu` variable to `True` in main.py. GPU Support requires a specially built version of FFmpeg with NVIDIA GPU support. Read more here: https://docs.nvidia.com/video-technologies/video-codec-sdk/12.0/ffmpeg-with-nvidia-gpu/index.html