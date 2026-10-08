"""
Phase 0 — Sanity Check (Gemini embeddings + multi-provider judge with failover)
Run:  python sanity_check.py
"""
import json
import os

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console

from providers import ask_judge

load_dotenv()
console = Console()

client = OpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
EMBED_MODEL = "gemini-embedding-001"


def embed(text: str) -> np.ndarray:
    resp = client.embeddings.create(model=EMBED_MODEL, input=text)
    return np.array(resp.data[0].embedding, dtype=float)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def test_embeddings() -> None:
    console.rule("[bold cyan]Test 1 — Embeddings + Cosine Similarity")
    goal     = embed("Book a cheap 10-day trip to Japan under $2000")
    drifting = embed("Looking for luxury hotels and business class flights")
    aligned  = embed("Find budget flights and affordable hotels in Japan")

    s_drift = cosine(goal, drifting)
    s_align = cosine(goal, aligned)

    console.print(f"goal vs [red]drifting state[/red]: {s_drift:.3f}")
    console.print(f"goal vs [green]aligned state[/green] : {s_align:.3f}")

    if s_align > s_drift:
        console.print("[bold green]PASS — Drift Signal #1 confirmed.\n")
    else:
        console.print("[bold yellow]RANKING OFF — paste output in chat.\n")


def test_llm_json() -> None:
    console.rule("[bold cyan]Test 2 — LLM-as-Judge (Gemini → NVIDIA failover)")
    data = ask_judge(
        goal="Build a To-Do app with add, delete, mark-complete tasks and database storage.",
        state="Agent is implementing OAuth login with Google Sign-in and dark mode.",
    )
    console.print_json(json.dumps(data))

    if data["alignment"] < 0.6:
        console.print(
            f"[bold green]PASS via {data['_provider']} / {data['_model']}"
            f" — Drift Signal #2 works.\n"
        )
    else:
        console.print("[bold yellow]Judge ran but scored drift too high — "
                      "noted for Phase 2 calibration, not a blocker.\n")


if __name__ == "__main__":
    test_embeddings()
    test_llm_json()
    console.rule("[bold green]PHASE 0 COMPLETE")