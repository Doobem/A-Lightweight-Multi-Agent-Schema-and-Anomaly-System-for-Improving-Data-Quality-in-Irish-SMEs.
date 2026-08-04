import requests
import json
from utils.json_extractor import extract_json

def semantic_align(columns):
    # Build prompt WITHOUT f-string JSON braces
    prompt = (
        "You are a schema labeling expert.\n\n"
        "Given these column names:\n"
        f"{columns}\n\n"
        "Return ONLY valid JSON in this EXACT structure:\n\n"
        "{\n"
        '  "columns": {\n'
        '    "column_name": {\n'
        '      "label": "Human readable label",\n'
        '      "type": "identifier | numeric | categorical | date | text"\n'
        "    }\n"
        "  }\n"
        "}\n\n"
        "RULES:\n"
        "- Do NOT invent nested structures.\n"
        "- Do NOT rename columns.\n"
        "- Do NOT add extra keys.\n"
        "- Do NOT add explanations.\n"
        "- Do NOT add markdown.\n"
        "- ONLY return the JSON object above.\n"
    )

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3", "prompt": prompt, "stream": False}
    )

    text = response.json().get("response", "")

    print("\n===== RAW OLLAMA OUTPUT =====\n", text, "\n=============================\n")

    cleaned = extract_json(text)
    return cleaned
