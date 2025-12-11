import requests
import json
import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EXPLANATION_MODEL = os.getenv("EXPLANATION_MODEL", "llama3.2:3b")


def call_ollama_generate(model: str, prompt: str) -> str:
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "").strip()


def build_compression_config(original_size_mb: float, user_prompt: str) -> dict:
    """
    Pure Python heuristic.
    No AI. We choose safe, good-quality defaults.
    """
    prompt_lower = user_prompt.lower()

    # Base "good quality" config
    config = {
        "target_size_mb": 10.0,
        "image_dpi": 200,
        "image_quality": 0.75,  # maps to JPEG quality ~75
        "pdf_profile": "ebook",  # Ghostscript /ebook: balanced
        "preserve_text_sharp": True,
        "note": "Standard high-quality compression for reports.",
    }

    # If user explicitly wants max compression
    if "max compress" in prompt_lower or "smallest" in prompt_lower or "as small as possible" in prompt_lower:
        config.update(
            {
                "image_dpi": 150,
                "image_quality": 0.6,
                "pdf_profile": "screen",  # stronger compression
                "note": "Aggressive compression; charts/images may soften slightly.",
            }
        )
    # If user mentions printing / print quality
    elif "print" in prompt_lower or "printing" in prompt_lower:
        config.update(
            {
                "image_dpi": 300,
                "image_quality": 0.9,
                "pdf_profile": "printer",
                "note": "Higher quality for printing; larger file size.",
            }
        )

    # If original is VERY large, we can nudge a bit stronger
    if original_size_mb > 150:
        config["image_dpi"] = min(config["image_dpi"], 180)
        config["image_quality"] = min(config["image_quality"], 0.7)

    return config


def generate_explanation(
    original_size_mb: float,
    final_size_mb: float,
    config: dict,
    threshold_mb: float,
    compressed: bool,
) -> str:
    """
    Use LLM only to explain what happened.
    If compressed=False, explanation is simple.
    """
    if not compressed:
        return (
            f"The file was {original_size_mb:.2f} MB, which is below the threshold of "
            f"{threshold_mb:.2f} MB. No compression was applied and the original file "
            "was returned unchanged."
        )

    prompt = f"""
You are explaining a PPT/PDF compression result to a non-technical user.

Original size: {original_size_mb:.2f} MB
Final size: {final_size_mb:.2f} MB
Config: {json.dumps(config)}

Explain in 3–5 short sentences:
- What was changed (image resolution, quality, etc.)
- Why text and charts should still look okay
- Roughly how much the file size was reduced (percentage)
Use simple language.
    """.strip()

    try:
        return call_ollama_generate(EXPLANATION_MODEL, prompt)
    except Exception:
        # Fallback if LLM fails
        reduction = (
            (1 - final_size_mb / original_size_mb) * 100
            if original_size_mb > 0
            else 0
        )
        return (
            f"The file was compressed from {original_size_mb:.2f} MB to "
            f"{final_size_mb:.2f} MB (about {reduction:.1f}% smaller). "
            "Images were downsampled and recompressed while keeping text and charts "
            "clear for on-screen viewing."
        )
