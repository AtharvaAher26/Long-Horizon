"""
diag_tools.py — Which (provider, model) pairs support chat + function calling?
Run:  python diag_tools.py
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

from sandbox_tools import TOOL_SCHEMAS

load_dotenv()

CANDIDATES = (
    [("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/", m)
     for m in ["gemini-2.5-flash", "gemini-3.8-flash", "gemini-2.5-flash-lite"]]
    + [("NVIDIA_API_KEY", "https://integrate.api.nvidia.com/v1", m)
       for m in ["openai/gpt-oss-20b", "deepseek-ai/deepseek-v4.1-flash",
                 "z-ai/glm-5.3-flash", "mistralai/mistral-7b-instruct-v0.3"]]
)

for key_var, base_url, model in CANDIDATES:
    key = os.getenv(key_var)
    if not key:
        print(f"SKIP {model}  (no {key_var} in .env)")
        continue
    try:
        client = OpenAI(api_key=key, base_url=base_url, timeout=30)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Call the noop tool once."}],
            tools=[TOOL_SCHEMAS[0]],          # write_file schema as the test tool
        )
        has_calls = bool(resp.choices[0].message.tool_calls)
        print(f"OK    {model}   tool_calls={has_calls}")
    except Exception as e:
        print(f"FAIL  {model}   {type(e).__name__}: {str(e)[:130]}")