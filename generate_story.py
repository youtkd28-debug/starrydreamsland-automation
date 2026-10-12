
import json
import os
import urllib.request

api_key = os.environ["GEMINI_API_KEY"]

prompt = """
Create an original, safe, cheerful English story for
children aged 3-7 for a 30-second YouTube Short.

Use a friendly fox, a bunny, and a magical star.

Return ONLY a JSON object with:
"title": a short catchy title
"narration": 55-65 simple English words
"scenes": exactly 6 objects, each containing:
  "image_prompt": a detailed visual description
  "duration": 5

Each scene must be a different moment in the story.
Use a consistent colorful 3D storybook animation style.
No scary content, no copyrighted characters.
"""

url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.5-flash-lite:generateContent"
)

payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {
        "responseMimeType": "application/json",
        "temperature": 0.9
    }
}

request = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    },
    method="POST"
)

with urllib.request.urlopen(request, timeout=60) as response:
    result = json.load(response)

text = result["candidates"][0]["content"]["parts"][0]["text"]
story = json.loads(text)

assert isinstance(story["title"], str)
assert isinstance(story["narration"], str)
assert len(story["scenes"]) == 6
assert all(
    isinstance(scene["image_prompt"], str)
    and scene["duration"] == 5
    for scene in story["scenes"]
)

with open("story.json", "w", encoding="utf-8") as f:
    json.dump(story, f, ensure_ascii=False, indent=2)

print("AI story generated successfully!")
print("Title:", story["title"])
print("Scenes:", len(story["scenes"]))
