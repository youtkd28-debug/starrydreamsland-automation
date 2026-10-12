
import os
import json
import base64
import time
import urllib.request
import urllib.error

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-3.1-flash-image"

with open("story.json", "r", encoding="utf-8") as f:
    story = json.load(f)

scenes = story["scenes"]
assert len(scenes) == 6, "Story must have exactly 6 scenes"

os.makedirs("scenes", exist_ok=True)

character_style = """
Maintain the same characters in every image:

Felix: adorable orange fox, white muzzle and chest,
large brown eyes, fluffy tail, green neck scarf.

Bella: small fluffy white bunny, blue eyes,
pink inner ears, yellow bow tie.

Visual style: colorful high-quality 3D children's
storybook animation, soft magical lighting,
friendly expressions, rich colors.

Vertical 9:16 composition.
No writing, subtitles, logos, or watermarks.
"""

for i, scene in enumerate(scenes, start=1):
    print(f"Generating scene {i}/6...", flush=True)

    prompt = f"""
    Create a single illustration for a children's story.

    Story title: {story['title']}
    Scene {i} of 6:
    {scene['image_prompt']}

    {character_style}

    Keep the appearance of recurring characters
    consistent across the entire story.

    Only include characters relevant to this scene.
    """

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{MODEL}:generateContent"
    )

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {
                "aspectRatio": "9:16",
                "imageSize": "1K"
            }
        }
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            request, timeout=180
        ) as response:
            result = json.load(response)

    except urllib.error.HTTPError as e:
        print("API error:", e.code)
        print(e.read().decode("utf-8"))
        raise SystemExit(1)

    parts = result["candidates"][0]["content"]["parts"]

    image_saved = False

    for part in parts:
        if "inlineData" in part:
            image_data = base64.b64decode(
                part["inlineData"]["data"]
            )

            mime = part["inlineData"].get(
                "mimeType", "image/png"
            )
            extension = (
                "jpg" if mime == "image/jpeg" else "png"
            )

            filename = f"scenes/scene_{i:02d}.{extension}"

            with open(filename, "wb") as f:
                f.write(image_data)

            print(f"Saved {filename}", flush=True)
            image_saved = True
            break

    if not image_saved:
        raise RuntimeError(
            f"No image returned for scene {i}"
        )

    if i < len(scenes):
        time.sleep(3)

print("All 6 AI scenes generated successfully!")
