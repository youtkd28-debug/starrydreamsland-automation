import json
import mimetypes
import os
import time
from pathlib import Path
from google import genai
from google.genai import types

MODEL = 'veo-3.1-lite-generate-preview'
DURATION = 4
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
story = json.loads(Path('story.json').read_text(encoding='utf-8'))
scenes = story['scenes']
if len(scenes) != 6:
    raise ValueError('Expected exactly six scenes')
output_dir = Path('animated_scenes')
output_dir.mkdir(exist_ok=True)

for index, scene in enumerate(scenes, start=1):
    candidates = [p for p in [Path(f'scenes/scene_{index:02d}.png'), Path(f'scenes/scene_{index:02d}.jpg')] if p.exists()]
    if len(candidates) != 1:
        raise FileNotFoundError(f'Expected one image for scene {index}: {candidates}')
    image_path = candidates[0]
    output_path = output_dir / f'clip_{index:02d}.mp4'
    description = scene['image_prompt']
    prompt = f'''Animate this exact reference frame for a gentle, cheerful children's fantasy story.
Scene {index} of 6 in "{story['title']}": {description}
Make the described action happen visibly: expressive body movement, subtle character reactions, natural ears/tail movement, animated environment and a smooth cinematic camera move. Preserve the exact design and clothing of Felix, the orange fox with green scarf, and Bella, the white bunny with yellow bow tie, whenever they appear. Do not introduce new characters unless described. Preserve continuity and the starting frame composition. Family-friendly, polished 3D storybook animation. No captions, words, logos, voiceover or dialogue. Only subtle ambient sound.'''
    print(f'Starting paid Veo generation {index}/6', flush=True)
    operation = client.models.generate_videos(
        model=MODEL,
        prompt=prompt,
        image=types.Image(image_bytes=image_path.read_bytes(), mime_type=mimetypes.guess_type(image_path.name)[0] or 'image/png'),
        config=types.GenerateVideosConfig(aspect_ratio='9:16', duration_seconds=DURATION, resolution='720p', number_of_videos=1),
    )
    print('Operation:', operation.name, flush=True)
    deadline = time.monotonic() + 1200
    while not operation.done:
        if time.monotonic() > deadline:
            raise TimeoutError(f'Veo did not finish; operation {operation.name}')
        time.sleep(10)
        operation = client.operations.get(operation)
    if operation.error:
        raise RuntimeError(f'Veo error for scene {index}: {operation.error}')
    if not operation.response or not operation.response.generated_videos:
        raise RuntimeError(f'Veo returned no video for scene {index}')
    client.files.download(file=operation.response.generated_videos[0].video, destination=str(output_path))
    print(f'Saved {output_path} ({output_path.stat().st_size} bytes)', flush=True)
print('Six animated clips generated.')
