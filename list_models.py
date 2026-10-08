import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
TARGETS = [
    ("GEMINI", "GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/"),
    ("NVIDIA", "NVIDIA_API_KEY", "https://integrate.api.nvidia.com/v1"),
]
for label, key_var, base_url in TARGETS:
    print(f"\n===== {label} ({key_var}) =====")
    key = os.getenv(key_var)
    if not key:
        print("  no key in .env — skipped")
        continue
    try:
        client = OpenAI(api_key=key, base_url=base_url)
        ids = sorted(m.id for m in client.models.list())
        for mid in ids:
            print("  " + mid)
        print(f"  ({len(ids)} models)")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {str(e)[:200]}")