import json
import subprocess
from pathlib import Path

FPS = 24
CLIP_SECONDS = 4
TARGET_SECONDS = 24
WIDTH, HEIGHT = 720, 1280


def run(args):
    subprocess.run(args, check=True)

story = json.loads(Path('story.json').read_text(encoding='utf-8'))
Path('normalized_clips').mkdir(exist_ok=True)

for i in range(1, 7):
    source = Path(f'animated_scenes/clip_{i:02d}.mp4')
    if not source.is_file():
        raise FileNotFoundError(source)
    dest = Path(f'normalized_clips/clip_{i:02d}.mp4')
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
         '-vf', f'fps={FPS},scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},setsar=1,format=yuv420p',
         '-t', str(CLIP_SECONDS), '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', str(dest)])

concat_file = Path('normalized_clips/concat.txt')
concat_file.write_text(''.join(f"file 'clip_{i:02d}.mp4'\n" for i in range(1, 7)))
run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file), '-c', 'copy', 'animated_silent.mp4'])

narration = story['narration'].strip()
run(['espeak-ng', '-v', 'en-us', '-s', '165', '-w', 'narration.wav', narration])
voice_duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 'narration.wav'], text=True).strip())
filters = []
if voice_duration > TARGET_SECONDS - 1:
    rate = voice_duration / (TARGET_SECONDS - 1)
    if rate > 2:
        raise ValueError(f'Narration excessively long: {voice_duration:.1f}s')
    filters.append(f'atempo={rate:.5f}')
filters.extend(['apad', f'atrim=0:{TARGET_SECONDS}', f'afade=t=out:st={TARGET_SECONDS-1}:d=1'])
run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', 'animated_silent.mp4', '-i', 'narration.wav',
     '-filter:a', ','.join(filters), '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k',
     '-t', str(TARGET_SECONDS), '-movflags', '+faststart', 'starrydreamsland-animated-short.mp4'])
print('Created starrydreamsland-animated-short.mp4')
