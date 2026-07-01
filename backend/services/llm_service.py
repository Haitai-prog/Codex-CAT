import time, os, logging
import httpx

logger = logging.getLogger("llm")

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEFAULT_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


async def translate_text(
    source_text: str,
    source_lang: str,
    target_lang: str,
    glossary: dict[str, str] | None = None,
    api_key: str | None = None,
) -> tuple[str, int, int, int]:
    """Translate text using DeepSeek API. Returns (translation, input_tokens, output_tokens, duration_ms)."""
    key = api_key or DEEPSEEK_API_KEY
    if not key:
        raise ValueError("DeepSeek API key not set. Set DEEPSEEK_API_KEY environment variable.")

    system_prompt = (
        f"You are a professional translator. Translate the following text from {source_lang} to {target_lang}. "
        "Output ONLY the translated text, without any explanations, notes, or quotation marks."
    )

    if glossary:
        glossary_str = ", ".join(f'"{k}" -> "{v}"' for k, v in glossary.items())
        system_prompt += f" Follow these term translations: {glossary_str}."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": source_text},
    ]

    start = time.time()
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{DEEPSEEK_BASE}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEFAULT_MODEL,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 4096,
            },
        )
    duration_ms = int((time.time() - start) * 1000)

    if resp.status_code != 200:
        logger.error("DeepSeek API error: %s %s", resp.status_code, resp.text[:500])
        raise RuntimeError(f"DeepSeek API returned {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    choice = data["choices"][0]
    translation = choice["message"]["content"].strip()

    usage = data.get("usage", {})
    in_tokens = usage.get("prompt_tokens", 0)
    out_tokens = usage.get("completion_tokens", 0)

    return translation, in_tokens, out_tokens, duration_ms
