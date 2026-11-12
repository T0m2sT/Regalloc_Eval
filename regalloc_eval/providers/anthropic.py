def complete(model, prompt, max_tokens, temperature):
    """One fresh, history-free request. `temperature` is ignored: this SDK/model family exposes no sampling
    parameters, so default sampling is used (documented in the README)."""
    import anthropic
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    with client.messages.stream(
        model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}],
    ) as s:
        text = "".join(s.text_stream)
        m = s.get_final_message()
    return text, str(m.stop_reason), dict(input=m.usage.input_tokens, output=m.usage.output_tokens)
