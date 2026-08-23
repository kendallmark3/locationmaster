import json

import anthropic

MODEL = "claude-opus-5"


def interpret_map_intent(intent: str, supported_categories: list[str]) -> dict:
    """Ask Claude which supported nearby-place categories the user's free-text intent
    implies, plus a short plain-language summary. AI picks *which categories matter*;
    it never sees or returns coordinates — the deterministic nearby-search endpoint
    resolves categories to real places, per ADR-001."""
    system = (
        "You choose which categories of nearby places matter for a location story, based "
        "on the user's plain-language description of what they want the map to show.\n\n"
        f"Categories must be a subset of exactly these ids: {', '.join(supported_categories)}. "
        "Only include a category if the intent genuinely implies it — do not include "
        "categories just because they exist. If the intent implies nothing specific, "
        "return an empty list.\n\n"
        "Respond with ONLY a JSON object, no other text: "
        '{"summary": "short plain-language phrase, <=8 words, for an end user — no '
        'mention of AI/models/categories as technical terms", "categories": ["..."]}'
    )
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        output_config={"effort": "low"},
        system=system,
        messages=[{"role": "user", "content": intent}],
    )
    text = next(block.text for block in response.content if block.type == "text")
    return _parse(text, supported_categories)


def _parse(text: str, supported_categories: list[str]) -> dict:
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            data = json.loads(text[start:end])
            categories = [c for c in data.get("categories", []) if c in supported_categories]
            summary = str(data.get("summary") or "").strip()[:120]
            return {"summary": summary, "categories": categories}
        except json.JSONDecodeError:
            pass
    return {"summary": "", "categories": []}
