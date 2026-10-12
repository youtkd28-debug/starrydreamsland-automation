
import os
import json
import urllib.request
import urllib.error

key = os.environ["GEMINI_API_KEY"]

url = "https://generativelanguage.googleapis.com/v1beta/models"

request = urllib.request.Request(
    url,
    headers={"x-goog-api-key": key}
)

models = []
while url:
    request = urllib.request.Request(
        url, headers={"x-goog-api-key": key}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        print("API error:", e.code)
        print(e.read().decode())
        raise SystemExit(1)

    models.extend(data.get("models", []))
    token = data.get("nextPageToken")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        + "?pageToken=" + token
        if token else None
    )

veo = [m for m in models if "veo" in m["name"].lower()]

if veo:
    print("Veo models listed for this API key:")
    for model in veo:
        print(model["name"])
else:
    print("No Veo models listed.")

print("No video generation requested. No Veo generation charge.")
