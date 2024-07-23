import subprocess
import json
import os
import time
from misc import delete_lines, update_line, CMD_COLORS

target_media_format = {
    "container": "mov,mp4,m4a,3gp,3g2,mj2",
    "video_codec": "h264",
    "video_level": 40,
    "audio_codec": "aac",
    "audio_channels": 2
}

VERBOSE = False

class Media:
    def __init__(self, filepath, container, video_codec, video_level, audio_codec, audio_channels, bit_depth, duration):
        self.filepath = filepath
        self.container = container
        self.video_codec = video_codec
        self.video_level = video_level
        self.audio_codec = audio_codec
        self.audio_channels = audio_channels
        self.bit_depth = bit_depth
        self.duration = duration
    
    @classmethod
    def from_ffprobe(self, file_path):
        """
        Create a Media object from the ffprobe output of a media file
        - file_path: the path to the media file
        """

        # check if the file is a temporary file
        # ignore them if they are
        if '.temp.mp4' in file_path:
            return None

        # normalize the file path
        # file_path = os.path.normpath(file_path)

        # run ffprobe on the file
        ffprobe = subprocess.check_output(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-print_format", "json", file_path])
        ffprobe = json.loads(ffprobe)

        # Extract bit depth if available
        video_stream = next((stream for stream in ffprobe["streams"] if stream["codec_type"] == "video"), None)
        audio_stream = next((stream for stream in ffprobe["streams"] if stream["codec_type"] == "audio"), None)

        # the bit depth is important for gpu conversion
        # if the bit depth is 10, we first need to convert it to 8-bit using CPU
        bit_depth = video_stream.get("bits_per_raw_sample", None) if video_stream else None
        duration = float(ffprobe["format"]["duration"])

        # safely get the video and audio streams
        video_container = ffprobe.get("format", {}).get("format_name", None)
        video_codec_name = video_stream.get("codec_name", None) if video_stream else None
        video_level = video_stream.get("level", None) if video_stream else None
        audio_codec = audio_stream.get("codec_name", None) if audio_stream else None
        audio_channels = audio_stream.get("channels", 2) if audio_stream else 2

        # create a new Media object
        media = Media(
            file_path,
            video_container,
            video_codec_name,
            video_level,
            audio_codec,
            audio_channels,
            bit_depth,
            duration
        )

        return media
    
    def convert(self, use_gpu=False):
        """
        Convert the media file to the target media format
        - use_gpu: convert with GPU (much faster). Only works for CUDA-enabled NVIDIA GPUs. See more here: https://docs.nvidia.com/video-technologies/video-codec-sdk/12.0/ffmpeg-with-nvidia-gpu/index.html
        """

        if use_gpu:
            # Preprocess the file if necessary
            # we need to convert 10-bit to 8-bit using CPU
            self.preprocess()

        # Change the extension to .mp4
        base_path = os.path.dirname(self.filepath)
        filepath = os.path.basename(self.filepath)
        filename, _ = os.path.splitext(filepath)

        temp_save_path = os.path.join(base_path, filename + ".temp.mp4")
        final_save_path = os.path.join(base_path, filename + ".mp4")

        # print(f"{self.filepath} -> {temp_save_path} -> {final_save_path}")

        ffmpeg_command = ["ffmpeg"]

        ffmpeg_command.extend(["-y", "-vsync", "0"])

        if use_gpu:
            ffmpeg_command.extend([
                "-hwaccel", "cuda",
                "-hwaccel_output_format", "cuda"
            ])

        ffmpeg_command.extend(["-i", self.filepath])

        # Check if the file has an audio track
        if self.audio_codec is None:
            # Add silent audio track
            silent_audio_path = self.add_silent_audio(self.duration)
            ffmpeg_command.extend(["-i", silent_audio_path, "-shortest"])

        ffmpeg_command.extend([
            "-c:a", target_media_format["audio_codec"],
            "-ac", str(target_media_format["audio_channels"]),
        ])

        if use_gpu:
            ffmpeg_command.extend([
                "-c:v", "h264_nvenc",
                "-preset", "slow"
            ])
        else:
            ffmpeg_command.extend([
                "-c:v", target_media_format["video_codec"],
                "-level:v", str(target_media_format["video_level"])
            ])

        ffmpeg_command.append(temp_save_path)

        # print(" ".join(ffmpeg_command))

        try:
            self.subprocess_verbosity(ffmpeg_command)

            # Delete the original file
            self.safe_remove_file(self.filepath)

            # Rename the temp file to the final file
            os.rename(temp_save_path, final_save_path)
            self.filepath = final_save_path

            if self.audio_codec is None and os.path.exists(silent_audio_path):
                self.safe_remove_file(silent_audio_path)
        
        except Exception as e:
            print(f"Error converting {self.filepath}: {e}")
            self.safe_remove_file(temp_save_path)
    
    def subprocess_verbosity(self, command):
        """
        Hide the output of the command if VERBOSE is False
        """
        if VERBOSE:
            subprocess.run(command, check=True)
        else:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    def safe_remove_file(self, path, retries=5, delay=5):
        """
        Retry removing a file if it fails initially due to permission errors or file in use.
        Returns True if the file is removed, False otherwise.
        """

        # Check if the file exists
        if not os.path.exists(path):
            return True

        for attempt in range(retries):
            try:
                os.remove(path)
                time.sleep(delay)
                return True
            except PermissionError:
                print(f"PermissionError: Retrying to remove {path} (Attempt {attempt + 1}/{retries})")
                time.sleep(delay)
            except Exception as e:
                print(f"Failed to remove {path}: {e}")
                time.sleep(delay)
        else:
            print(f"Failed to remove {path} after {retries} attempts!")
            return False
    
    def test_gpu_conversion(self):
        """
        Test if the file can be converted using GPU. This file tests if the first second of the video can be converted using GPU.
        """
        test_output = "test_output.mp4"
        ffmpeg_command = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i", self.filepath,
            "-t", "00:00:01",  # Only process the first second
            "-c:v", "h264_nvenc",
            "-preset", "slow",
            test_output
        ]
        try:
            self.subprocess_verbosity(ffmpeg_command)
            # if test_output.mp4 exists, delete it
            self.safe_remove_file(test_output)
            return True
        except subprocess.CalledProcessError:
            # if test_output.mp4 exists, delete it
            self.safe_remove_file(test_output)
            return False
        except Exception as e:
            self.safe_remove_file(test_output)
            return False
    
    def preprocess(self):
        """
        Preprocess the file to ensure it can be converted using GPU if possible.
        """

        gpu_enabled = False

        if self.bit_depth == "10":
            # Convert 10-bit to 8-bit using CPU
            print(f"⚠️   Video has a bit depth of 10, which is unsupported for GPU conversion")
            print(f"⚙️   Converting to 8-bit with CPU (slower)")
            self.convert_bit_depth()
        elif self.bit_depth is None:
            # Test conversion using GPU
            print(f"❔ {CMD_COLORS["magenta"]} Unknown bit depth. {CMD_COLORS["reset"]} Testing GPU conversion")
            if not self.test_gpu_conversion():
                print(f"⚠️   GPU test failed. Converting to 8-bit with CPU... (slower)")
                # If GPU conversion fails, convert bit depth using CPU
                self.convert_bit_depth()
            else:
                print(f"✅  GPU test passed. Continuing...")
        else:
            print(f"✅  Supported bit depth: {self.bit_depth} bits")
            print(f"✅  No preprocessing required. Continuing...")
        
        # delete two lines
        time.sleep(1)
        delete_lines(2)
        
        # print the cool cuda conversion message
        update_line(f"⏭️  {CMD_COLORS['yellow']} Converting (GPU): {CMD_COLORS["reset"]} {self.get_filename()}")
    
    def convert_bit_depth(self):
        """
        Convert the bit depth to 8-bit using CPU.
        """
        temp_save_path = self.get_temp_save_path()
        ffmpeg_command = [
            "ffmpeg", "-y", "-i", self.filepath,
            "-vf", "format=yuv420p",
            temp_save_path
        ]
        self.subprocess_verbosity(ffmpeg_command)

        # Delete the original file
        self.safe_remove_file(self.filepath)
        
        # Rename the temp file to the original file
        os.rename(temp_save_path, self.filepath)

        # delete the temp file
        self.safe_remove_file(temp_save_path)
    
    def add_silent_audio(self, duration):

        print(f"🔄  {CMD_COLORS['blue']} Creating silent audio track: {CMD_COLORS['reset']} {self.get_filename()}...")

        silent_audio_path = os.path.join(os.path.dirname(self.filepath), "silent.mp3")

        # delete the silent audio track if it exists
        # we need to create a new one with the correct duration
        if os.path.exists(silent_audio_path):
            self.safe_remove_file(silent_audio_path)
        
        # create a silent audio track with the same duration as the video
        ffmpeg_command = [
            "ffmpeg", "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", str(duration), "-q:a", "9", silent_audio_path
        ]
        self.subprocess_verbosity(ffmpeg_command)
        
        delete_lines(1)
        
        return silent_audio_path
    
    def get_temp_save_path(self):
        base_path = os.path.dirname(self.filepath)
        filename, _ = os.path.splitext(os.path.basename(self.filepath))
        return os.path.join(base_path, filename + ".temp.mp4")

    def get_filename(self):
        return os.path.basename(self.filepath)

    def is_valid(self):
        """
        Check if the media file has the target media format
        Returns True if the media file is valid, False otherwise
        """

        # if the file is not an mp4 file, return False
        _, file_extension = os.path.splitext(self.filepath)
        file_extension = file_extension[1:]

        if not file_extension == 'mp4':
            return False 

        # check if the media format matches the target media format
        return (
            self.container == target_media_format["container"] and
            self.video_codec == target_media_format["video_codec"] and
            self.video_level <= target_media_format["video_level"] and
            self.audio_codec == target_media_format["audio_codec"] and
            self.audio_channels <= target_media_format["audio_channels"]
        )

    def __str__(self):
        self_string = f"[{self.filepath}]\n" \
                f"Container: {self.container}\n" \
                f"Video Codec: {self.video_codec}\n" \
                f"Video Level: {self.video_level}\n" \
                f"Audio Codec: {self.audio_codec}\n" \
                f"Audio Channels: {self.audio_channels}\n" \
        
        return self_string