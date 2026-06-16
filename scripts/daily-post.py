#!/usr/bin/env python3
import os
import re
import sys
import json
import logging
import random
from datetime import datetime, timezone
from urllib.request import Request, urlopen

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("daily-post")

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(REPO_DIR, "_posts")
QUEUE_FILE = os.path.join(REPO_DIR, "_data", "post-queue.json")

GH_TOKEN = os.environ.get("GH_MODELS_TOKEN")
GH_MODELS_ENDPOINT = "https://models.inference.ai.azure.com/chat/completions"
GH_MODEL = "gpt-4o-mini"

AMAZON_LINK = "https://www.amazon.com/dp/B0CTXCQ9HM"
SITE_BASE = "/the-king-in-yellow-resources"

SUPTOPICS = {
    "character_analysis": [
        "Hildred Castaigne — The Repairer of Reputations",
        "Tessie Reardon — The Yellow Sign",
        "Jack Scott — The Yellow Sign",
        "Boris Yvain — The Mask",
        "Geneviève — The Mask",
        "Mr. Wilde — The Repairer of Reputations",
        "The Watchman — The Yellow Sign",
        "Cassilda — the play within the book",
        "Camilla — the play within the book",
        "The Stranger — the play within the book",
        "The Phantom of Truth — the play within the book",
        "Hastur — from name to mythos",
        "The King in Yellow — the entity",
        "Constance — The Demoiselle d'Ys",
        "Philip — The Demoiselle d'Ys",
        "Seigneur Raoul — The Demoiselle d'Ys",
        "Hastings — The Street of Our Lady of the Fields",
        "Selby — Rue Barrée",
        "Jack Trent — The Street of the First Shell",
        "The Clown — The Prophets' Paradise / The Green Room",
        "Sylvia Elven — The Street of the First Shell",
    ],
    "carcosa_lore": [
        "Carcosa — the lost city described in the play",
        "The Lake of Hali — the boundary between worlds",
        "The twin suns of Carcosa",
        "Black stars in the sky of Carcosa",
        "The Hyades star cluster connection",
        "Aldebaran and its role in the mythos",
        "Yhtill — the sister city",
        "The geography of the play's world",
        "Carcosa as a state of mind",
        "How later writers expanded Carcosa",
        "Carcosa in popular imagination",
    ],
    "yellow_sign_meaning": [
        "What is the Yellow Sign? Physical description",
        "The Yellow Sign as a symbol of forbidden knowledge",
        "The Yellow Sign in The Repairer of Reputations",
        "The Yellow Sign in The Yellow Sign story",
        "The Hyades and the shape of the Yellow Sign",
        "The Yellow Sign as a memetic hazard",
        "The Yellow Sign in occult traditions",
        "How the Yellow Sign differs from Lovecraft's symbols",
        "The Yellow Sign in True Detective's spiral",
        "The Yellow Sign in Call of Cthulhu RPG",
    ],
    "story_analysis": [
        "The Repairer of Reputations — plot and themes",
        "The Repairer of Reputations — symbolism",
        "The Repairer of Reputations — character study",
        "The Mask — plot and themes",
        "The Mask — science and the supernatural",
        "The Court of the Dragon — plot and themes",
        "The Court of the Dragon — psychological horror",
        "The Yellow Sign — a close reading",
        "The Yellow Sign — tragedy and fate",
        "The Demoiselle d'Ys — time and romance",
        "The Demoiselle d'Ys — Breton folklore",
        "The Prophets' Paradise — experimental structure",
        "The Street of the Four Winds — art and poverty",
        "The Street of the First Shell — war and love",
        "The Street of Our Lady of the Fields — Parisian bohemia",
        "Rue Barrée — social barriers",
        "The play within the book — meta-narrative structure",
    ],
    "quote_exploration": [
        "Strange is the night where black stars rise",
        "The King in Yellow — Act 1, Scene 2 excerpt",
        "Have you found the Yellow Sign?",
        "I am the King in Yellow — the phantom's claim",
        "The Pallid Mask — the Phantom of Truth",
        "Cassilda's Song in full",
        "Along the shore the cloud waves break",
        "Ne raillons pas les fous — epigraph to The Repairer",
        "Let the red dawn surmise — epigraph to The Yellow Sign",
        "The song of the Hyades",
        "The music of Carcosa descriptions",
        "The madhouse scenes dialogue",
        "The final lines of The Yellow Sign",
        "The opening of The Court of the Dragon",
        "The closing of The Repairer of Reputations",
    ],
    "adaptation_spotlight": [
        "True Detective Season 1 — the Yellow King",
        "True Detective — Carcosa in Louisiana",
        "True Detective — the spiral vs the Yellow Sign",
        "Call of Cthulhu — The King in Yellow campaign",
        "Call of Cthulhu — The Yellow Sign as artifact",
        "Delta Green — the King in Yellow",
        "The Yellow King RPG by Robin D. Laws",
        "Bloodborne — echoes of the King in Yellow",
        "The King in Yellow in comic books",
        "The King in Yellow in music and albums",
        "Stage adaptations of the play",
        "The King in Yellow in video games",
    ],
    "chambers_life": [
        "Robert W. Chambers — early life and art studies",
        "Chambers in Paris — the Académie Julian years",
        "From illustrator to writer — Chambers' career shift",
        "The success of The King in Yellow in 1895",
        "Why Chambers abandoned weird fiction",
        "Chambers as a bestselling romance novelist",
        "Chambers and H.P. Lovecraft — the connection",
        "Chambers' legacy and rediscovery",
        "Chambers' other supernatural works",
        "Chambers' place in American literature",
    ],
    "weird_fiction_history": [
        "The King in Yellow as proto-weird fiction",
        "Precursors — Poe and the psychological tale",
        "Precursors — Ambrose Bierce and the supernatural",
        "Contemporary — M.R. James and the ghost story",
        "The King in Yellow and the decadent movement",
        "How The King in Yellow influenced Lovecraft",
        "The King in Yellow in the Cthulhu Mythos",
        "The King in Yellow and the New Wave of horror",
        "Modern weird fiction and Chambers' revival",
        "The King in Yellow and the French symbolist tradition",
    ],
    "thematic_analysis": [
        "Madness as a consequence of forbidden knowledge",
        "The role of art in driving obsession",
        "Identity and the dissolution of self",
        "Reality versus illusion in Chambers' stories",
        "Fate and free will in The King in Yellow",
        "The bohemian artist as tragic figure",
        "Love and death intertwined",
        "Decadence and decay as themes",
        "The unreliable narrator in Chambers",
        "Memory and the past's grip on the present",
        "Class and society in the Paris stories",
    ],
    "reading_guide": [
        "How to approach The King in Yellow for the first time",
        "Reading order — the four play-linked stories first",
        "Understanding the connection between all ten stories",
        "What to look for in The Repairer of Reputations",
        "Enjoying the romance stories on their own terms",
        "The Paris stories — context and appreciation",
        "How the play functions as a narrative device",
        "Key symbols to track through the collection",
        "What makes Chambers different from Lovecraft",
        "A companion guide for rereading",
    ],
    "symbolism_deep_dive": [
        "Masks as symbols of hidden identity",
        "Mirrors and reflections in Chambers",
        "The play within the book as meta-symbol",
        "Black stars and inverted cosmology",
        "Twin suns and duality",
        "The color yellow — meaning and mood",
        "The love-death motif",
        "Cats and animal symbolism",
        "Religious imagery and the Catholic background",
        "Artistic tools and paint as symbols",
        "Doors and thresholds between worlds",
        "The church as a setting for horror",
    ],
    "comparison_essay": [
        "Chambers and Poe — psychological horror compared",
        "Chambers and Lovecraft — cosmic horror compared",
        "Chambers and M.R. James — dread compared",
        "Chambers and Arthur Machen — the hidden world",
        "Chambers and Oscar Wilde — decadence compared",
        "Chambers and Algernon Blackwood — nature and horror",
        "Chambers and Robert E. Howard — weird adventure",
        "Chambers and Ramsey Campbell — urban horror",
        "The King in Yellow and House of Leaves — ergodic horror",
        "The King in Yellow and Annihilation — cosmic dread",
    ],
    "behind_the_story": [
        "The Repairer of Reputations — future New York inspiration",
        "The Mask — the science of the soul",
        "The Court of the Dragon — a nightmare vision",
        "The Yellow Sign — Chambers' masterpiece",
        "The Demoiselle d'Ys — Brittany and folklore",
        "The Prophets' Paradise — autobiographical roots",
        "The Street of the Four Winds — the Latin Quarter",
        "The Street of the First Shell — the Siege of Paris",
        "The Street of Our Lady of the Fields — Chambers in love",
        "Rue Barrée — American in Paris",
        "The real Paris locations in Chambers' stories",
    ],
    "mythos_exploration": [
        "How Lovecraft adopted Hastur from Chambers",
        "August Derleth and the expansion of the mythos",
        "The Yellow Sign in the Cthulhu Mythos",
        "Hastur — from place name to Great Old One",
        "The King in Yellow in the Expanded Mythos",
        "Chaosium's interpretation of the mythos",
        "Modern cosmic horror authors on Chambers",
        "The King in Yellow in the SCP Foundation",
        "Fan interpretations and online lore",
        "The mythos as collaborative storytelling",
    ],
    "language_and_vocabulary": [
        "Chambers' descriptive prose style",
        "The use of French in the Paris stories",
        "Chambers' vocabulary of decay and beauty",
        "The poetic structure of Cassilda's Song",
        "Archaic language in The Demoiselle d'Ys",
        "Chambers' dialogue — natural or stylized?",
        "The rhythm of Chambers' sentences",
        "Military terminology in The Street of the First Shell",
        "Art terminology in the studio stories",
        "How Chambers creates atmosphere through language",
    ],
}

CONTENT_TITLES = {k: k.replace("_", " ").title() for k in SUPTOPICS}
CONTENT_TITLES["yellow_sign_meaning"] = "The Yellow Sign"
CONTENT_TITLES["carcosa_lore"] = "Carcosa Lore"
CONTENT_TITLES["character_analysis"] = "Character Analysis"

INTERNAL_LINKS = {
    "character_analysis": [
        ("analysis/carcosa-glossary/", "Carcosa Glossary \u2014 Characters & Places"),
    ],
    "carcosa_lore": [
        ("analysis/carcosa-glossary/", "Carcosa Glossary \u2014 Complete Guide"),
    ],
    "yellow_sign_meaning": [
        ("analysis/yellow-sign-symbolism/", "The Yellow Sign \u2014 Symbolism and Meaning"),
        ("analysis/carcosa-glossary/", "Carcosa Glossary \u2014 Places, Characters & Concepts"),
    ],
    "story_analysis": [
        ("analysis/story-guide/", "Story-by-Story Guide to The King in Yellow"),
        ("full-text/the-repairer-of-reputations/", "Full Text: The Repairer of Reputations"),
        ("full-text/the-yellow-sign/", "Full Text: The Yellow Sign"),
        ("full-text/the-mask/", "Full Text: The Mask"),
        ("full-text/the-court-of-the-dragon/", "Full Text: The Court of the Dragon"),
    ],
    "quote_exploration": [
        ("analysis/carcosa-glossary/", "Carcosa Glossary \u2014 Places, Characters & Concepts"),
    ],
    "adaptation_spotlight": [
        ("adaptations/true-detective/", "True Detective Season 1 \u2014 Analysis"),
        ("adaptations/roleplaying-games/", "The King in Yellow in TTRPGs"),
    ],
    "chambers_life": [
        ("analysis/chambers-biography/", "Robert W. Chambers \u2014 Full Biography"),
    ],
    "weird_fiction_history": [
        ("analysis/chambers-biography/", "Robert W. Chambers \u2014 Biography"),
    ],
    "thematic_analysis": [
        ("analysis/story-guide/", "Story-by-Story Guide"),
        ("analysis/carcosa-glossary/", "Carcosa Glossary"),
    ],
    "reading_guide": [
        ("analysis/story-guide/", "Story-by-Story Guide"),
        ("full-text/", "Complete Full Text Index"),
    ],
    "symbolism_deep_dive": [
        ("analysis/yellow-sign-symbolism/", "The Yellow Sign \u2014 Symbolism and Meaning"),
    ],
    "comparison_essay": [
        ("analysis/chambers-biography/", "Robert W. Chambers \u2014 Biography"),
    ],
    "behind_the_story": [
        ("analysis/story-guide/", "Story-by-Story Guide"),
        ("full-text/", "Complete Full Text Index"),
    ],
    "mythos_exploration": [
        ("analysis/carcosa-glossary/", "Carcosa Glossary"),
        ("analysis/yellow-sign-symbolism/", "The Yellow Sign \u2014 Symbolism"),
    ],
    "language_and_vocabulary": [
        ("full-text/", "Complete Full Text Index"),
    ],
}


def slugify(text):
    text = text.lower()
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'[\u2014\u2013]', '', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text[:100]


def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_queue(queue):
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)


def pick_content_type_and_topic(queue):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    candidates = []
    for ctype, topics in SUPTOPICS.items():
        used = set(queue.get(ctype, {}).get("used", []))
        unused = [t for t in topics if t not in used]
        if unused:
            candidates.append(ctype)

    if not candidates:
        queue = {k: {"used": []} for k in SUPTOPICS}
        save_queue(queue)
        candidates = list(SUPTOPICS.keys())
        log.info("All subtopics exhausted — resetting queue")

    ctype = random.choice(candidates)
    topics = SUPTOPICS[ctype]
    used = set(queue.get(ctype, {}).get("used", []))
    unused = [t for t in topics if t not in used]
    topic = random.choice(unused)

    if ctype not in queue:
        queue[ctype] = {"used": [], "last_date": None}
    queue[ctype]["used"].append(topic)
    queue[ctype]["last_date"] = today
    save_queue(queue)

    log.info("Picked: %s → %s", ctype, topic[:50])
    return ctype, topic


def build_explore_more(content_type):
    links = INTERNAL_LINKS.get(content_type, [])
    if not links:
        links = [
            ("analysis/carcosa-glossary/", "Carcosa Glossary"),
            ("analysis/story-guide/", "Story-by-Story Guide"),
        ]

    section = "\n\n---\n\n### Explore More\n\n"
    for path, label in links:
        section += f"- [{label}]({SITE_BASE}/{path})\n"

    section += f"\n*For a more interactive experience, there is a coloring book and nightmare journal inspired by The King in Yellow: [{AMAZON_LINK.replace('https://www.amazon.com/dp/', '')}]({AMAZON_LINK})*"
    # ^ simpler: just the ASIN as text
    return section


def build_prompt(content_type, topic):
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    return f"""You are a literary analysis writer specializing in weird fiction and The King in Yellow by Robert W. Chambers (1895).

Write a blog post for today ({today}) with the following specifications:

TOPIC: {topic}
CONTENT TYPE: {CONTENT_TITLES.get(content_type, content_type)}

REQUIREMENTS:
- Title should be engaging and descriptive (not just the topic name)
- Write 300-500 words in clear, accessible English
- Use literary analysis, not plot summary only
- Include specific references to the text where possible
- No markdown code blocks in the body (plain markdown only)

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


def generate_title(content, topic):
    t = datetime.now(timezone.utc)
    short = topic.split(" — ")[-1].split(" - ")[-1].strip()
    return f"{short} — {t.strftime('%B %d, %Y')}"


def find_related_posts(content_type, current_slug):
    if not os.path.exists(POSTS_DIR):
        return []

    related = []
    for fname in os.listdir(POSTS_DIR):
        if not fname.endswith(".md"):
            continue
        if current_slug and current_slug in fname:
            continue

        fpath = os.path.join(POSTS_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            text = f.read()

        lines = text.split("\n")
        other_type = None
        rtitle = ""
        rdate = ""
        for line in lines:
            if line.startswith("content_type:"):
                other_type = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("title:"):
                rtitle = line.split(":", 1)[1].strip().strip('"').strip("'")

        if other_type == content_type:
            slug = fname.replace(".md", "")
            related.append((slug, rtitle))

    return related


def save_post(content, content_type, topic):
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    title = generate_title(content, topic)
    slug = slugify(topic)

    explore = build_explore_more(content_type)

    related = find_related_posts(content_type, slug)
    if related:
        explore += "\n\n### Previous Posts on This Topic\n\n"
        for slug_url, rtitle in related:
            explore += f"- [{rtitle}]({SITE_BASE}/{date_str[:4]}/{date_str[5:7]}/{slug_url}.html)\n"

    frontmatter = f"""---
layout: post
title: "{title}"
date: {date_str} 12:00:00 +0000
categories: blog
content_type: {content_type}
tags: [{content_type.replace('_', ' ')} the-king-in-yellow chambers analysis]
---
"""
    full_content = frontmatter + content.strip() + explore

    os.makedirs(POSTS_DIR, exist_ok=True)
    filepath = os.path.join(POSTS_DIR, f"{date_str}-{slug}.md")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    log.info("Post saved: %s", filepath)
    return filepath


def main():
    if not GH_TOKEN:
        log.error("GH_MODELS_TOKEN not set")
        sys.exit(1)

    log.info("=" * 50)
    log.info("DAILY POST GENERATOR — The King in Yellow")
    log.info("=" * 50)

    queue = load_queue()
    content_type, topic = pick_content_type_and_topic(queue)
    log.info("Topic: %s", topic)

    log.info("Generating content with %s...", GH_MODEL)
    prompt = build_prompt(content_type, topic)
    content = call_github_models(prompt)

    if not content:
        log.error("Failed to generate content")
        sys.exit(1)

    log.info("Content generated (%d chars)", len(content))

    filepath = save_post(content, content_type, topic)
    log.info("Done: %s", filepath)


if __name__ == "__main__":
    main()
