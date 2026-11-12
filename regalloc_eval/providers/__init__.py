"""Model providers: complete(provider, model, prompt, ...) -> (text, finish_reason, usage). SDKs import lazily."""
import time

from . import anthropic, gemini

PROVIDERS = {"gemini": gemini.complete, "anthropic": anthropic.complete}


def complete(provider, model, prompt, max_tokens, temperature, tries=6):
    fn = PROVIDERS[provider]
    for i in range(tries):
        try:
            return fn(model, prompt, max_tokens, temperature)
        except Exception as e:  # rate limits / transient errors
            if i == tries - 1 or "PerDay" in str(e):  # daily quota: retrying is pointless
                raise
            wait = min(60, 5 * 2 ** i)
            print(f"  retry in {wait}s ({type(e).__name__}: {str(e)[:80]})", flush=True)
            time.sleep(wait)
