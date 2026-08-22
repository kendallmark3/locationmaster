import anthropic

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """You write a persuasive paragraph explaining why someone should
relocate to a subject location, for a location-story app.

Every sentence must cite a specific fact from the input: an actual place name,
category, or note you were given, or a specific phrase from the project intent. Do
not invent amenities, distances, statistics, addresses, or any fact not present in the
input. Do not mention or infer coordinates.

Never fill gaps with vague, generic, or purely emotional claims that aren't tied to a
specific input detail — phrases like "people who live here love it", "it has a special
character", or "hard to put into words" are exactly the kind of unsupported filler to
avoid. If a sentence doesn't reference a concrete label, category, note, or intent
phrase, cut it rather than write it.

Output plain prose only, no headings or bullet points, 2-5 sentences, scaled to how
much concrete material you were actually given."""


def has_enough_detail(raw_intent: str, points: list[dict]) -> bool:
    if len(raw_intent.strip()) >= 40:
        return True
    if any((p.get("notes") or "").strip() for p in points):
        return True
    return len(points) >= 2


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
