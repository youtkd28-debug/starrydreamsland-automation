import json
import subprocess
from pathlib import Path


def run(*args):
    subprocess.run(args, check=True)

clips = [Path(f'animated_scenes/clip_{i:02d}.mp4') for i in range(1, 7)]
for clip in clips:
    if not clip.is_file():
        raise FileNotFoundError(f'Missing {clip}')

# Normalize video frame rate, geometry, timestamps and audio handling.
Path('smooth_parts').mkdir(exist_ok=True)
for i, clip in enumerate(clips, 1):
    run('ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(clip),
        '-vf', 'fps=24,scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,format=yuv420p',
        '-an', '-t', '4', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
        f'smooth_parts/{i:02d}.mp4')

# Crossfade each clip by 0.4 seconds; 6*4 - 5*0.4 = 22 sec.
inputs = []
for i in range(1, 7):
    inputs.extend(['-i', f'smooth_parts/{i:02d}.mp4'])
filters = []
for i in range(6):
    filters.append(f'[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[v{i}]')
last = 'v0'
for i in range(1, 6):
    out = f'x{i}'
    offset = 4*i - 0.4*i
    filters.append(f'[{last}][v{i}]xfade=transition=fade:duration=0.4:offset={offset:.1f}[{out}]')
    last = out
run('ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', *inputs,
    '-filter_complex', ';'.join(filters), '-map', f'[{last}]',
    '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
    '-pix_fmt', 'yuv420p', 'smooth_silent.mp4')

story = json.loads(Path('story.json').read_text(encoding='utf-8'))
run('espeak-ng', '-v', 'en-us', '-s', '165', '-w', 'narration.wav', story['narration'])
voice_duration = float(subprocess.check_output([
    'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
    '-of', 'default=noprint_wrappers=1:nokey=1', 'narration.wav'
], text=True).strip())
filters = []
if voice_duration > 21:
    speed = voice_duration / 21
    if speed > 2:
        raise ValueError('Narration too long')
    filters.append(f'atempo={speed:.5f}')
filters += ['apad', 'atrim=0:22', 'afade=t=out:st=21:d=1']
run('ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
    '-i', 'smooth_silent.mp4', '-i', 'narration.wav',
    '-filter:a', ','.join(filters), '-map', '0:v:0', '-map', '1:a:0',
    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k',
    '-t', '22', '-movflags', '+faststart', 'starrydreamsland-smooth.mp4')
print('Created starrydreamsland-smooth.mp4')
