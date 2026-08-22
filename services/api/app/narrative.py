import anthropic

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """You write a short, persuasive paragraph explaining why someone should
relocate to a subject location, for a location-story app.

Ground every claim ONLY in the project's stated intent and the story points provided to
you (their label, category, and notes). Do not invent amenities, distances, statistics,
addresses, or any fact not present in the input. Do not mention or infer coordinates.
If the provided points are thin, write a shorter paragraph rather than padding it with
invented detail. Output plain prose only, no headings or bullet points, 2-4 sentences."""


def generate_relocation_narrative(raw_intent: str, points: list[dict]) -> str:
    point_lines = "\n".join(
        f"- {p['label']} ({p['category']})" + (f": {p['notes']}" if p.get("notes") else "")
        for p in points
    )
    user_content = f"Project intent: {raw_intent}\n\nStory points:\n{point_lines}"

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        output_config={"effort": "low"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    return next(block.text for block in response.content if block.type == "text")
