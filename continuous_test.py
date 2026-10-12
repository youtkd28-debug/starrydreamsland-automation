import mimetypes
import os
import subprocess
import time
from pathlib import Path
from google import genai
from google.genai import types

MODEL = 'veo-3.1-lite-generate-preview'
OUT = Path('continuous_test_output')
OUT.mkdir(exist_ok=True)
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])


def run(*args):
    subprocess.run(args, check=True)


def generate(image_path, prompt, output_path):
    mime = mimetypes.guess_type(str(image_path))[0] or 'image/png'
    print(f'PAID Veo request: {output_path.name}', flush=True)
    op = client.models.generate_videos(
        model=MODEL,
        prompt=prompt,
        image=types.Image(image_bytes=image_path.read_bytes(), mime_type=mime),
        config=types.GenerateVideosConfig(
            aspect_ratio='9:16', duration_seconds=4,
            resolution='720p', number_of_videos=1,
        ),
    )
    print(f'Operation: {op.name}', flush=True)
    deadline = time.monotonic() + 1200
    while not op.done:
        if time.monotonic() > deadline:
            raise TimeoutError(f'Veo timed out: {op.name}. Check billing before retrying.')
        time.sleep(10)
        op = client.operations.get(op)
    if op.error:
        raise RuntimeError(f'Veo failed: {op.error}')
    if not op.response or not op.response.generated_videos:
        raise RuntimeError('Veo returned no generated video')
    client.files.download(file=op.response.generated_videos[0].video, destination=str(output_path))
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f'Missing video: {output_path}')


# Reuse the previously generated character image. No image generation charge.
source = next((p for p in (Path('scenes/scene_01.png'), Path('scenes/scene_01.jpg')) if p.exists()), None)
if source is None:
    raise FileNotFoundError('scenes/scene_01.png or scenes/scene_01.jpg is required')

prompt1 = '''One continuous cinematic tracking shot, family-friendly polished 3D animated children's film. Felix, a cute orange fox wearing a GREEN scarf, and Bella, a cute WHITE bunny wearing a YELLOW bow tie, walk together through the same magical grassy meadow at twilight. The camera smoothly follows them at a steady height. They notice a small glowing golden star ahead in the grass and gradually approach it. Consistent faces, costumes, anatomy, lighting, and environment. Natural walking animation, gentle breeze and subtle tail and ear movement. NO cuts, transitions, scene changes, montages, title cards, subtitles, or dialogue. Keep both characters visible.'''

prompt2 = '''CONTINUE the exact same single unbroken camera take from this frame. Same Felix orange fox with GREEN scarf and Bella white bunny with YELLOW bow tie; same grassy magical meadow, same twilight lighting, same camera direction, height and speed. Continue their forward walking motion naturally without resetting their poses or changing positions. They arrive at the tiny glowing golden star in the grass, pause, and Bella gently reaches toward it while Felix watches. Keep consistent character designs and geometry. Camera tracks gently and continuously. NO cuts, no scene transitions, no new locations, no sudden jump in time, no text, no voiceover.'''

clip1 = OUT / 'continuous_clip_01.mp4'
clip2 = OUT / 'continuous_clip_02.mp4'
last = OUT / 'clip_01_last_frame.png'
generate(source, prompt1, clip1)
# Use the actual last frame as the reference image for the next paid generation.
run('ffmpeg', '-y', '-sseof', '-0.05', '-i', str(clip1), '-frames:v', '1', str(last))
generate(last, prompt2, clip2)
# Trim the first frame of clip 2 to reduce duplicated boundary frames.
# Re-encode to common frame rate and join, keeping original generated ambient audio if present.
filtergraph = '[0:v]fps=24,scale=720:1280,setsar=1,format=yuv420p[v0];[1:v]trim=start=0.041667,setpts=PTS-STARTPTS,fps=24,scale=720:1280,setsar=1,format=yuv420p[v1];[v0][v1]concat=n=2:v=1:a=0[outv]'
run('ffmpeg', '-y', '-i', str(clip1), '-i', str(clip2), '-filter_complex', filtergraph, '-map', '[outv]', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(OUT / 'continuous_8s_test.mp4'))
print('Ready: continuous_test_output/continuous_8s_test.mp4')
