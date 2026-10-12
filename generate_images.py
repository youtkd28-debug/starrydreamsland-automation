
import os
import json
import base64
import urllib.request
import urllib.error

API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-3.1-flash-image"

with open("story.json", "r", encoding="utf-8") as f:
    story = json.load(f)

scene = story["scenes"][0]

prompt = f"""
Create one beautiful vertical 9:16 illustration
for a children's animated YouTube Short.

Story: {story["title"]}
Scene: {scene["image_prompt"]}

Visual style:
- High-quality colorful 3D animated storybook
- Cute orange fox named Felix
- Cute white bunny named Bella
- Magical glowing stars
- Soft cinematic lighting
- Consistent character appearance
- Suitable for children aged 3 to 7
- No text, no watermark
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
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.load(response)

except urllib.error.HTTPError as e:
    print("Gemini API error:", e.code)
    print(e.read().decode("utf-8"))
    raise SystemExit(1)

parts = result["candidates"][0]["content"]["parts"]

for part in parts:
    if "inlineData" in part:
        image = base64.b64decode(
            part["inlineData"]["data"]
        )

        with open("scene_01.png", "wb") as f:
            f.write(image)

        print("AI image generated successfully!")
        raise SystemExit(0)

raise RuntimeError("No image returned by Gemini")
