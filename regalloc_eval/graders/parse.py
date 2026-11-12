"""Answer extraction and the shared result shape: {"score": 0..1, "passed": bool, "note": str}."""
import json
import re


def extract_json(text):
    """Last ```json block, else last parsable {...} in the text. Returns a dict or None."""
    blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    for cand in reversed(blocks):
        try:
            return json.loads(cand)
        except ValueError:
            pass
    for m in reversed(list(re.finditer(r"\{", text))):
        for end in range(len(text), m.start(), -1):
            if text[end - 1] == "}":
                try:
                    return json.loads(text[m.start():end])
                except ValueError:
                    continue
    return None


def result(score, note):
    return {"score": score, "passed": score == 1, "note": note}


def is_proper(edges, color):
    return all(color[a] != color[b] for a, b in edges if a in color and b in color)
