"""
embeddings.py — shared embedding utilities (Gemini via OpenAI-compatible API).

The OpenAI client is created LAZILY on first embed() call, so importing this
module works with no GEMINI_API_KEY set (e.g. pytest collection, offline
tooling). Only an actual embed() without a key raises.
"""
import os

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

EMBED_MODEL = "gemini-embedding-001"

_client = None  # built on first use by _get_client()


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set — embeddings are unavailable. "
                "Set it in the environment or in a .env file to call embed()."
            )
        _client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    return _client


def embed(text: str) -> np.ndarray:
    resp = _get_client().embeddings.create(model=EMBED_MODEL, input=text)
    return np.array(resp.data[0].embedding, dtype=float)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
