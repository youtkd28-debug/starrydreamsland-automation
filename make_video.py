
import glob
import json
import os
import subprocess

WIDTH = 720
HEIGHT = 1280
FPS = 24
SCENE_SECONDS = 5

with open("story.json", encoding="utf-8") as f:
    story = json.load(f)

assert len(story["scenes"]) == 6

os.makedirs("video_parts", exist_ok=True)

def run(command):
    subprocess.run(command, check=True)

# Create six animated scenes
for i in range(1, 7):
    files = sorted(glob.glob(f"scenes/scene_{i:02d}.*"))
    if not files:
        raise FileNotFoundError(f"Missing scene {i}")

    image = files[0]
    output = f"video_parts/part_{i:02d}.mp4"

    print(f"Animating scene {i}/6", flush=True)

    zoom = (
        "zoompan="
        "z='min(zoom+0.0006,1.12)':"
        "d=1:"
        f"s={WIDTH}x{HEIGHT}:"
        f"fps={FPS}"
    )

    video_filter = (
        "scale=800:1424:"
        "force_original_aspect_ratio=increase,"
        "crop=800:1424,"
        + zoom +
        ",format=yuv420p"
    )

    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-framerate", str(FPS),
        "-i", image,
        "-vf", video_filter,
        "-frames:v", str(FPS * SCENE_SECONDS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "24",
        "-pix_fmt", "yuv420p",
        "-an",
        output
    ])

# Join all six scenes
with open("video_parts/list.txt", "w") as f:
    for i in range(1, 7):
        f.write(f"file 'part_{i:02d}.mp4'\n")

run([
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", "video_parts/list.txt",
    "-c", "copy",
    "silent_video.mp4"
])

# Generate English narration
narration = story["narration"]

run([
    "espeak-ng",
    "-v", "en-us",
    "-s", "140",
    "-w", "narration.wav",
    narration
])

# Measure narration duration
duration = float(subprocess.check_output([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1",
    "narration.wav"
]).decode().strip())

# Speed up narration only if it exceeds 29 seconds
audio_filter = []

if duration > 29:
    audio_filter.append(f"atempo={duration / 29:.5f}")

audio_filter += [
    "apad",
    "atrim=0:30",
    "afade=t=out:st=29:d=1"
]

# Export final 30-second MP4
run([
    "ffmpeg", "-y",
    "-i", "silent_video.mp4",
    "-i", "narration.wav",
    "-filter:a", ",".join(audio_filter),
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "160k",
    "-t", "30",
    "-movflags", "+faststart",
    "starrydreamsland-final.mp4"
])

print("VIDEO CREATED SUCCESSFULLY!")
print("Title:", story["title"])
print("Output: starrydreamsland-final.mp4")
