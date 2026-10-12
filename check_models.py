
import os
import json
import urllib.request
import urllib.error

key = os.environ["GEMINI_API_KEY"]
url = "https://generativelanguage.googleapis.com/v1beta/models"

req = urllib.request.Request(
    url,
    headers={"x-goog-api-key": key}
)

try:
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)

    for model in data.get("models", []):
        methods = model.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            print(model["name"])

except urllib.error.HTTPError as e:
    print("HTTP error:", e.code)
    print(e.read().decode("utf-8"))
except Exception as e:
    print("Connection error:", type(e).__name__, str(e))
