
import os
import time
from pathlib import Path
from google import genai
from google.genai import types

image_path = Path("scene_01.png")
if not image_path.is_file():
    raise FileNotFoundError(
        "scene_01.png not found in repository root"
    )

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt = """
Animate the provided image as the opening shot of a
beautiful 3D animated children's fantasy movie.

Felix, the adorable orange fox wearing a green scarf,
looks up at the twinkling stars. His fluffy tail sways
gently and he blinks naturally.

Bella, the fluffy white bunny with a yellow bow tie,
happily makes one small hop beside Felix. Her long
ears bounce softly as she lands.

The stars shimmer and magical fireflies drift through
the night forest. The camera slowly moves closer.

Preserve the exact appearance, clothing, colors,
background, and proportions from the starting image.

Fluid natural character animation, cinematic lighting,
smooth motion, family-friendly, no text, no dialogue.
Soft magical ambience and gentle forest sounds.
"""

print("Starting ONE 4-second Veo animation...", flush=True)

operation = client.models.generate_videos(
    model="veo-3.1-lite-generate-preview",
    prompt=prompt,
    image=types.Image(
        image_bytes=image_path.read_bytes(),
        mime_type="image/png",
    ),
    config=types.GenerateVideosConfig(
        aspect_ratio="9:16",
        duration_seconds=4,
        resolution="720p",
        number_of_videos=1,
    ),
)

print("Operation:", operation.name, flush=True)

deadline = time.monotonic() + 1200

while not operation.done:
    if time.monotonic() > deadline:
        raise TimeoutError(
            "Generation is still running. Operation: "
            + operation.name
        )
    time.sleep(10)
    operation = client.operations.get(operation)
    print("Waiting for Veo...", flush=True)

if operation.error:
    raise RuntimeError(str(operation.error))

if not operation.response or not operation.response.generated_videos:
    raise RuntimeError("Veo returned no video.")

video = operation.response.generated_videos[0].video

client.files.download(
    file=video,
    destination="felix_bella_animation.mp4",
)

print("SUCCESS: felix_bella_animation.mp4", flush=True)
