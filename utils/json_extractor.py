import json
import re

def extract_json(text):
    """
    Extract JSON from messy LLM output.
    Ensures the result is ALWAYS a list of row dictionaries.
    """

    # Remove JS-style comments
    text = re.sub(r"//.*", "", text)

    # Try fenced JSON first
    fenced = re.findall(r"```json(.*?)```", text, re.DOTALL)
    if fenced:
        try:
            data = json.loads(fenced[0].strip())
            return _normalize(data)
        except:
            pass

    # Try to extract the largest {...} block
    braces = re.findall(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text, re.DOTALL)
    if braces:
        for block in braces:
            try:
                data = json.loads(block)
                return _normalize(data)
            except:
                continue

    # Try direct JSON
    try:
        data = json.loads(text)
        return _normalize(data)
    except:
        raise ValueError("Could not extract valid JSON from LLM output.")


def _normalize(data):
    """
    Normalize JSON into a list of row dictionaries.
    """

    # Case 1: Already a list
    if isinstance(data, list):
        return data

    # Case 2: Dict of dicts → convert to list
    if isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
        return list(data.values())

    # Case 3: Single dict → wrap in list
    if isinstance(data, dict):
        return [data]

    # Otherwise error
    raise ValueError("Extracted JSON is not a valid row or list of rows.")
