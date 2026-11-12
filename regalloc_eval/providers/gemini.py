import os


def complete(model, prompt, max_tokens, temperature):
    """One fresh, history-free request. Returns (text, finish_reason, {"input": n, "output": n})."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    r = client.models.generate_content(
        model=model, contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature, max_output_tokens=max_tokens),
    )
    fin = r.candidates[0].finish_reason if r.candidates else None
    u = r.usage_metadata  # thinking tokens are billed as output
    usage = dict(input=u.prompt_token_count, output=(u.candidates_token_count or 0) + (u.thoughts_token_count or 0))
    return (r.text or ""), str(fin), usage
