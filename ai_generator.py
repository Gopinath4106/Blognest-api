"""
AI Blog Generator module.

If an OpenAI-compatible API key is configured (OPENAI_API_KEY in .env), this
module calls that API to generate a blog. If no key is available, or the API
call fails for any reason (network issue, invalid key, rate limit, etc.), it
automatically falls back to a built-in DEMO generator so the application
never crashes and always produces usable content.
"""

import json
import re
import random
import requests

from config import Config

DEMO_MODE_ACTIVE = not Config.AI_ENABLED  # informational flag used by templates


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def generate_blog(topic, category="General", tone="Professional", length="Medium"):
    """
    Generate a blog post.

    Returns a dict with keys: title, introduction, sections (list of
    {heading, content}), conclusion, tags (list), used_ai (bool).
    """
    topic = (topic or "").strip() or "Untitled Topic"

    if Config.AI_ENABLED:
        try:
            result = _generate_with_api(topic, category, tone, length)
            result["used_ai"] = True
            return result
        except Exception:
            # Any failure (bad key, network, quota, malformed response) ->
            # silently fall back to demo mode so the app never breaks.
            pass

    result = _generate_demo(topic, category, tone, length)
    result["used_ai"] = False
    return result


# ---------------------------------------------------------------------------
# Real AI generation (OpenAI-compatible Chat Completions API)
# ---------------------------------------------------------------------------
def _generate_with_api(topic, category, tone, length):
    length_guides = {
        "Short": "about 3 short sections",
        "Medium": "about 4-5 sections",
        "Long": "about 6-7 detailed sections",
    }
    length_guide = length_guides.get(length, length_guides["Medium"])

    system_prompt = (
        "You are an assistant that writes structured blog posts. "
        "Always respond with ONLY valid JSON, no markdown fences, no extra text, "
        "matching exactly this schema: "
        '{"title": string, "introduction": string, '
        '"sections": [{"heading": string, "content": string}], '
        '"conclusion": string, "tags": [string]}'
    )
    user_prompt = (
        f"Write a blog post about the topic: '{topic}'. "
        f"Category: {category}. Tone: {tone}. Length: {length} ({length_guide}). "
        "The introduction and conclusion should each be one or two paragraphs. "
        "Each section should have a clear heading and 1-2 paragraphs of content. "
        "Provide 3-6 relevant single or two-word tags."
    )

    url = f"{Config.OPENAI_API_BASE.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": Config.OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    raw_text = response.json()["choices"][0]["message"]["content"]

    # Strip accidental markdown code fences if the model adds them anyway
    raw_text = re.sub(r"^```(json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    data = json.loads(raw_text)

    return {
        "title": data.get("title") or f"A Look at {topic.title()}",
        "introduction": data.get("introduction", ""),
        "sections": data.get("sections", []),
        "conclusion": data.get("conclusion", ""),
        "tags": data.get("tags", []),
    }


# ---------------------------------------------------------------------------
# Offline / Demo generation (no API key required, always works)
# ---------------------------------------------------------------------------
_SECTION_TEMPLATES = [
    ("Understanding {topic}",
     "{Topic} is a subject that continues to gain relevance in today's fast-moving world. "
     "At its core, {topic} refers to a set of ideas, practices, and tools that help people "
     "achieve better outcomes in their personal or professional lives. Understanding the "
     "fundamentals of {topic} is the first step toward applying it effectively."),
    ("Why {Topic} Matters",
     "The importance of {topic} cannot be overstated. As industries evolve and new "
     "challenges emerge, having a solid grasp of {topic} gives individuals and "
     "organizations a meaningful advantage. It helps in making informed decisions, "
     "reducing risk, and staying ahead of the curve."),
    ("Key Aspects of {Topic}",
     "There are several important aspects to consider when exploring {topic}. These "
     "include the core principles that guide it, the common tools or techniques used "
     "in practice, and the way it interacts with related fields. Breaking {topic} down "
     "into these components makes it much easier to learn and apply."),
    ("Best Practices for {Topic}",
     "Adopting the right approach to {topic} can make a significant difference. Some "
     "widely recommended practices include starting with clear goals, staying updated "
     "with the latest trends, learning from real-world examples, and continuously "
     "refining your approach based on feedback and results."),
    ("Common Challenges in {Topic}",
     "Like any meaningful subject, {topic} comes with its own set of challenges. These "
     "may include a steep learning curve, limited resources, or rapidly changing "
     "standards. Recognizing these challenges early allows learners and practitioners "
     "to plan around them more effectively."),
    ("The Future of {Topic}",
     "Looking ahead, {topic} is expected to keep evolving as new research, technology, "
     "and real-world experience shape best practices. Staying curious and continuing to "
     "learn will be key for anyone who wants to remain effective in this area."),
]

_TONE_OPENERS = {
    "Professional": "In this article, we take a structured and informative look at {topic}.",
    "Casual": "Let's take a relaxed, easy-to-follow look at {topic}.",
    "Friendly": "Hey there! Let's chat about {topic} and why it's worth knowing about.",
    "Formal": "This article presents a formal overview of {topic} and its significance.",
    "Enthusiastic": "Get ready — {topic} is an exciting subject with a lot to explore!",
}

_LENGTH_SECTION_COUNT = {"Short": 2, "Medium": 4, "Long": 6}

_TAG_POOL_EXTRA = ["guide", "overview", "tips", "beginners", "insights", "2026"]


def _generate_demo(topic, category, tone, length):
    topic_clean = topic.strip()
    topic_title = topic_clean.title()

    opener_template = _TONE_OPENERS.get(tone, _TONE_OPENERS["Professional"])
    introduction = (
        f"{opener_template.format(topic=topic_clean)} "
        f"Whether you are a beginner or already familiar with {category.lower()}-related "
        f"topics, this post breaks down {topic_clean} into simple, digestible sections "
        f"so you can quickly understand what it means and why it matters."
    )

    section_count = _LENGTH_SECTION_COUNT.get(length, 4)
    chosen = _SECTION_TEMPLATES[:section_count]

    sections = []
    for heading_tpl, content_tpl in chosen:
        heading = heading_tpl.format(topic=topic_clean, Topic=topic_title)
        content = content_tpl.format(topic=topic_clean, Topic=topic_title)
        sections.append({"heading": heading, "content": content})

    conclusion = (
        f"In summary, {topic_clean} is a valuable subject that offers real benefits when "
        f"understood and applied thoughtfully. By keeping the key points from this article "
        f"in mind, you'll be well equipped to explore {topic_clean} further and put it into "
        f"practice with confidence. (Note: this article was generated in offline demo mode "
        f"because no AI API key was configured.)"
    )

    base_tags = [w.lower() for w in re.findall(r"[A-Za-z]+", topic_clean)][:3]
    tags = list(dict.fromkeys(base_tags + [category.lower()] + random.sample(_TAG_POOL_EXTRA, 2)))

    title = f"{topic_title}: A Complete {length} Guide"

    return {
        "title": title,
        "introduction": introduction,
        "sections": sections,
        "conclusion": conclusion,
        "tags": tags,
    }


def sections_to_html(sections):
    """Convert the sections list into a single HTML content block for storage/editing."""
    parts = []
    for s in sections:
        heading = s.get("heading", "").strip()
        content = s.get("content", "").strip()
        if heading:
            parts.append(f"<h3>{heading}</h3>")
        if content:
            parts.append(f"<p>{content}</p>")
    return "\n".join(parts)


def assemble_full_content(generated):
    """Combine introduction + sections + conclusion into one HTML content string."""
    parts = [f"<p>{generated.get('introduction', '')}</p>"]
    parts.append(sections_to_html(generated.get("sections", [])))
    parts.append(f"<h3>Conclusion</h3>\n<p>{generated.get('conclusion', '')}</p>")
    return "\n".join(p for p in parts if p.strip())
