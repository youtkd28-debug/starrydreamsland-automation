import mimetypes
import os
import subprocess
import time
from pathlib import Path
from google import genai
from google.genai import types

MODEL = 'veo-3.1-lite-generate-preview'
OUT = Path('continuous_30s_output')
OUT.mkdir(exist_ok=True)
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])

PROMPTS = [
    'ONE UNBROKEN CINEMATIC TRACKING SHOT. Felix, a cute orange fox with a GREEN scarf, and Bella, a white bunny with a YELLOW bow tie, walk together in a magical grassy meadow at twilight. Camera follows at a constant height and direction. They see a tiny golden star glowing in the grass ahead. Smooth natural walking, consistent characters and lighting. No cuts, no text, no dialogue.',
    'CONTINUE EXACTLY from the provided final frame, as one unbroken camera take. Same fox Felix GREEN scarf, white bunny Bella YELLOW bow tie, same meadow and twilight, same camera movement. They approach the glowing golden star without any reset or jump; Bella bends slightly to examine it. No cuts, no scene change, no text.',
    'CONTINUE EXACTLY from this final frame, same uninterrupted camera motion and characters. Bella carefully touches the little star; it floats slowly upward between them. Felix watches in wonder. Keep positions, outfits, environment, scale and lighting identical. No cuts or time jumps.',
    'CONTINUE EXACTLY from this frame, same unbroken camera shot. The small star gently drifts forward along the meadow path; Felix and Bella follow it together at a natural walking pace. Same twilight meadow, same costumes, consistent movement. No cuts, no new location.',
    'CONTINUE EXACTLY from this frame, same continuous tracking shot. The star rises a little higher and creates a gentle trail of sparkling golden light; Felix and Bella smile and keep following it. Maintain character identities and continuous camera motion. No cuts.',
    'CONTINUE EXACTLY from this frame, same unbroken tracking shot and meadow. The floating golden star circles slowly above Felix and Bella, casting warm light over their faces. They look up naturally, remaining in the same positions. No camera jump, no cuts.',
    'CONTINUE EXACTLY from this frame, same uninterrupted camera take. The star releases a soft shower of tiny magical sparkles; Felix and Bella laugh silently and reach toward the sparkles. Preserve all character details and scenery. No cuts or location changes.',
    'CONTINUE EXACTLY from this frame, same unbroken shot. The little star settles gently between Felix and Bella and glows brightly as they smile together. Camera continues its smooth subtle tracking and ends on a warm magical moment. No cuts, no fade, no text.'
]


def run(*args):
    subprocess.run(args, check=True)


def generate(image_path, prompt, output_path):
    mime = mimetypes.guess_type(str(image_path))[0] or 'image/png'
    print(f'PAID generation: {output_path.name}', flush=True)
    op = client.models.generate_videos(
        model=MODEL,
        prompt=prompt,
        image=types.Image(image_bytes=image_path.read_bytes(), mime_type=mime),
        config=types.GenerateVideosConfig(
            aspect_ratio='9:16', duration_seconds=4,
            resolution='720p', number_of_videos=1,
        ),
    )
    deadline = time.monotonic() + 1200
    while not op.done:
        if time.monotonic() > deadline:
            raise TimeoutError(f'Operation {op.name} timed out; check billing before rerun')
        time.sleep(10)
        op = client.operations.get(op)
    if op.error:
        raise RuntimeError(f'Veo error: {op.error}')
    if not op.response or not op.response.generated_videos:
        raise RuntimeError('Veo returned no video')
    client.files.download(file=op.response.generated_videos[0].video, destination=str(output_path))
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f'Empty output: {output_path}')


source = next((p for p in (Path('scenes/scene_01.png'), Path('scenes/scene_01.jpg')) if p.exists()), None)
if source is None:
    raise FileNotFoundError('scenes/scene_01.png or scenes/scene_01.jpg is required')

clips = []
for index, prompt in enumerate(PROMPTS, 1):
    clip = OUT / f'continuous_clip_{index:02d}.mp4'
    generate(source, prompt, clip)
    clips.append(clip)
    if index < len(PROMPTS):
        source = OUT / f'clip_{index:02d}_last_frame.png'
        run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-sseof', '-0.05', '-i', str(clip), '-frames:v', '1', str(source))

# Trim one boundary frame from every subsequent clip to avoid a repeated still.
inputs = []
filters = []
for i, clip in enumerate(clips):
    inputs.extend(['-i', str(clip)])
    trim = 'trim=start=0.041667,setpts=PTS-STARTPTS,' if i else ''
    filters.append(f'[{i}:v]{trim}fps=24,scale=720:1280,setsar=1,format=yuv420p[v{i}]')
filters.append(''.join(f'[v{i}]' for i in range(len(clips))) + f'concat=n={len(clips)}:v=1:a=0[v]')
output = OUT / 'starrydreamsland_continuous_30s.mp4'
run('ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *inputs,
    '-filter_complex', ';'.join(filters), '-map', '[v]', '-t', '30',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart', str(output))
print(f'COMPLETE: {output} (30 seconds, no narration/audio track)', flush=True)
