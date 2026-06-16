#!/usr/bin/env python3
"""
Daily Post Generator for The King in Yellow Resource Hub.
Generates a Jekyll post using GitHub Models (GPT-4o-mini) with rotating content types.
Run via GitHub Actions on a daily cron schedule.
"""

import os
import sys
import json
import logging
import random
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("daily-post")

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(REPO_DIR, "_posts")
QUEUE_FILE = os.path.join(REPO_DIR, "_data", "post-queue.json")

GH_TOKEN = os.environ.get("GH_MODELS_TOKEN")
GH_MODELS_ENDPOINT = "https://models.inference.ai.azure.com/chat/completions"
GH_MODEL = "gpt-4o-mini"

AMAZON_LINK = "https://www.amazon.com/dp/B0CTXCQ9HM"

CONTENT_TYPES = [
    "character_analysis",
    "carcosa_lore",
    "yellow_sign_meaning",
    "story_analysis",
    "quote_exploration",
    "adaptation_spotlight",
    "chambers_life",
    "weird_fiction_history",
    "thematic_analysis",
    "reading_guide",
    "symbolism_deep_dive",
    "comparison_essay",
    "behind_the_story",
    "mythos_exploration",
    "language_and_vocabulary",
]

CONTENT_TITLES = {
    "character_analysis": "Character Analysis",
    "carcosa_lore": "Carcosa Lore",
    "yellow_sign_meaning": "The Yellow Sign: Symbolism & Meaning",
    "story_analysis": "Story Analysis",
    "quote_exploration": "Quote of the Day",
    "adaptation_spotlight": "Adaptation Spotlight",
    "chambers_life": "Chambers' Life & Times",
    "weird_fiction_history": "Weird Fiction History",
    "thematic_analysis": "Thematic Analysis",
    "reading_guide": "Reading Guide",
    "symbolism_deep_dive": "Symbolism Deep Dive",
    "comparison_essay": "Comparative Reading",
    "behind_the_story": "Behind the Story",
    "mythos_exploration": "Mythos Exploration",
    "language_and_vocabulary": "Language & Vocabulary",
}

CONTEXT_PROMPTS = {
    "character_analysis": (
        "Write a 300-500 word analysis of one specific character from The King in Yellow."
        " Include who they are, their role in the story, and what they represent thematically."
    ),
    "carcosa_lore": (
        "Write a 300-500 word exploration of Carcosa — the lost city from The King in Yellow."
        " Describe its features, its significance, and how it has been interpreted in subsequent works."
    ),
    "yellow_sign_meaning": (
        "Write a 300-500 word analysis of the Yellow Sign — its appearance in the stories,"
        " its symbolic meaning, and its influence on later fiction and occult traditions."
    ),
    "story_analysis": (
        "Write a 300-500 word analysis of one specific story from The King in Yellow collection."
        " Cover plot, themes, characters, and its place in the collection."
    ),
    "quote_exploration": (
        "Pick a notable quote from The King in Yellow and explore its meaning, context, and resonance."
        " Write 300-500 words."
    ),
    "adaptation_spotlight": (
        "Write a 300-500 word spotlight on an adaptation of The King in Yellow in media"
        " — True Detective, Call of Cthulhu, The Yellow King RPG, video games, music, or other media."
    ),
    "chambers_life": (
        "Write a 300-500 word piece about Robert W. Chambers' life — his art career,"
        " his Paris years, his transition to writing, or his place in American literature."
    ),
    "weird_fiction_history": (
        "Write a 300-500 word exploration of how The King in Yellow fits into the broader"
        " weird fiction tradition — its predecessors, contemporaries, and legacy."
    ),
    "thematic_analysis": (
        "Write a 300-500 word thematic analysis of one of the major themes in The King in Yellow"
        " — madness, forbidden knowledge, art and obsession, identity, or reality vs illusion."
    ),
    "reading_guide": (
        "Write a 300-500 word guide for readers approaching The King in Yellow for the first time."
        " Offer context, reading tips, and what to pay attention to in each story."
    ),
    "symbolism_deep_dive": (
        "Write a 300-500 word deep dive into a specific symbol or motif from The King in Yellow"
        " — masks, mirrors, the play, black stars, twin suns, or similar."
    ),
    "comparison_essay": (
        "Write a 300-500 word comparison between The King in Yellow and another work"
        " — Lovecraft, Poe, Machen, Blackwood, or a modern work influenced by Chambers."
    ),
    "behind_the_story": (
        "Write a 300-500 word piece about the background or inspirations behind a specific story"
        " in The King in Yellow collection."
    ),
    "mythos_exploration": (
        "Write a 300-500 word exploration of how the King in Yellow mythos has grown beyond Chambers"
        " — Lovecraft's additions, Derleth's expansions, and modern interpretations."
    ),
    "language_and_vocabulary": (
        "Write a 300-500 word exploration of unusual language, vocabulary, or stylistic elements"
        " in The King in Yellow."
    ),
}


def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_queue(queue):
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)


def pick_content_type(queue):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    used_order = sorted(queue.keys(), key=lambda k: queue[k])
    available = [t for t in CONTENT_TYPES if t not in queue or t not in used_order[-3:]]
    choice = random.choice(available)
    queue[choice] = today
    save_queue(queue)
    return choice


def build_prompt(content_type):
    prompt_text = CONTEXT_PROMPTS[content_type]
    title_hint = CONTENT_TITLES[content_type]
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    return f"""You are a literary analysis writer specializing in weird fiction and The King in Yellow by Robert W. Chambers (1895).

Write a blog post for today ({today}) with the following specifications:

TOPIC TYPE: {title_hint}
INSTRUCTION: {prompt_text}

REQUIREMENTS:
- Title should be engaging and descriptive (not just the topic name)
- Write 300-500 words in clear, accessible English
- Use literary analysis, not plot summary only
- Include specific references to the text where possible
- No markdown code blocks in the body (plain markdown text only)
- End with the following EXACT footer:

---

*For a more interactive experience, there is a coloring book and nightmare journal inspired by The King in Yellow: [The King in Yellow: Nightmares Diary and Coloring Book]({AMAZON_LINK})*

IMPORTANT FORMAT:
Return ONLY the post body. Do NOT include a title — the title will be added separately.
Start directly with the content.
"""


def call_github_models(prompt):
    if not GH_TOKEN:
        log.error("GH_MODELS_TOKEN not set")
        return None

    payload = json.dumps({
        "model": GH_MODEL,
        "messages": [
            {"role": "system", "content": "You are a literary analysis writer specializing in weird fiction. Write in clear, accessible English."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 2000,
    }).encode()

    req = Request(
        GH_MODELS_ENDPOINT,
        data=payload,
        headers={
            "Authorization": f"Bearer {GH_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        log.error("Error calling GitHub Models: %s", e)
        return None


def generate_title(content, content_type):
    t = datetime.now(timezone.utc)
    base = CONTENT_TITLES[content_type]
    return f"{base} — {t.strftime('%B %d, %Y')}"


def save_post(content, content_type):
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    title = generate_title(content, content_type)
    slug = f"{date_str}-{content_type}"

    frontmatter = f"""---
layout: post
title: "{title}"
date: {date_str} 12:00:00 +0000
categories: blog
tags: [{content_type.replace('_', ' ')} the-king-in-yellow chambers analysis]
---
"""
    full_content = frontmatter + content.strip()

    os.makedirs(POSTS_DIR, exist_ok=True)
    filepath = os.path.join(POSTS_DIR, f"{slug}.md")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    log.info("Post saved: %s", filepath)
    return filepath


def main():
    if not GH_TOKEN:
        log.error("GH_MODELS_TOKEN not set. Create a GitHub secret: Settings > Secrets > Actions > GH_MODELS_TOKEN")
        sys.exit(1)

    log.info("=" * 50)
    log.info("DAILY POST GENERATOR — The King in Yellow")
    log.info("=" * 50)

    queue = load_queue()
    content_type = pick_content_type(queue)
    log.info("Content type: %s", content_type)

    log.info("Generating content with %s...", GH_MODEL)
    prompt = build_prompt(content_type)
    content = call_github_models(prompt)

    if not content:
        log.error("Failed to generate content")
        sys.exit(1)

    log.info("Content generated (%d chars)", len(content))

    filepath = save_post(content, content_type)
    log.info("Done: %s", filepath)


if __name__ == "__main__":
    main()
