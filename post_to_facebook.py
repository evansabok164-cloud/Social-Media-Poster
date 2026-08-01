#!/usr/bin/env python3
"""
AI-generated Facebook post automation — runs 4x/day on a schedule.

Flow:
  1. Ask Claude to write a short Facebook caption (sewing + personal
     development theme, matching your existing voice). The theme is
     chosen based on which of the day's 4 time slots is running, so
     the 4 posts in a day don't repeat each other.
  2. Turn the caption into an image prompt and generate an image via
     Pollinations.ai (free, no API key required).
  3. Upload the image + caption to your Facebook Page via the Graph API.

Required environment variables (set as GitHub Actions secrets, see README):
  ANTHROPIC_API_KEY     - your Anthropic API key
  FB_PAGE_ID            - your Facebook Page ID
  FB_PAGE_ACCESS_TOKEN  - a long-lived Page access token (System User token)
"""

import os
import sys
import json
import random
import textwrap
from datetime import datetime, timezone
import requests

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
FB_PAGE_ID = os.environ["FB_PAGE_ID"]
FB_PAGE_ACCESS_TOKEN = os.environ["FB_PAGE_ACCESS_TOKEN"]

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
GRAPH_API_VERSION = "v20.0"

# One theme per daily time slot (must match the 4 cron times in the
# workflow file, in order). This keeps each day's 4 posts distinct
# instead of relying on chance.
THEMES_BY_SLOT = [
    "a sewing tip or technique, tied to a life lesson about patience or craft",
    "a personal development reflection, using a sewing metaphor (thread, seams, patterns, mending)",
    "an encouraging message for someone learning to sew, with a growth-mindset angle",
    "behind-the-scenes thoughts on the creative process of making something by hand",
]

# Extra themes used as a random fallback (e.g. for manual/test runs
# that don't line up with a scheduled slot).
FALLBACK_THEMES = THEMES_BY_SLOT + [
    "a short story or observation connecting fabric/sewing to personal growth",
]

# UTC hours the workflow is scheduled to run at (must match daily-post.yml).
SLOT_HOURS_UTC = [3, 8, 12, 16]


def pick_theme() -> str:
    """Pick today's theme based on the current UTC hour's slot, so the
    4 runs in a day each get a different theme. Falls back to random
    if the run doesn't match a known slot (e.g. manual trigger)."""
    current_hour = datetime.now(timezone.utc).hour
    if current_hour in SLOT_HOURS_UTC:
        slot_index = SLOT_HOURS_UTC.index(current_hour)
        return THEMES_BY_SLOT[slot_index]
    return random.choice(FALLBACK_THEMES)


def generate_caption() -> str:
    theme = pick_theme()
    system_prompt = textwrap.dedent(f"""
        You write Facebook captions for a personal page that blends sewing
        and personal development. Voice: warm, encouraging, a little
        reflective, not salesy. No hashtags spam (max 3 relevant hashtags
        at the end). Keep it to 2-4 short paragraphs, mobile-friendly
        (short lines/paragraphs). Today's theme: {theme}.
        Return ONLY the caption text, nothing else.
    """).strip()

    resp = requests.post(
        ANTHROPIC_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 400,
            "messages": [{"role": "user", "content": system_prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return "".join(
        block["text"] for block in data["content"] if block["type"] == "text"
    ).strip()


def generate_image_prompt(caption: str) -> str:
    """Ask Claude for a short visual prompt describing an image to match the caption."""
    resp = requests.post(
        ANTHROPIC_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 100,
            "messages": [{
                "role": "user",
                "content": (
                    "Write a short (under 25 words) visual image-generation prompt "
                    "for a warm, aesthetic photo to accompany this Facebook caption. "
                    "Think: sewing supplies, fabric, hands at work, cozy craft-room "
                    "scenes, soft natural light. No text/words in the image. "
                    f"Caption:\n\n{caption}"
                ),
            }],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return "".join(
        block["text"] for block in data["content"] if block["type"] == "text"
    ).strip()


def generate_image(prompt: str) -> bytes:
    """Generate an image via Pollinations.ai (free, no key needed)."""
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    resp = requests.get(url, params={"width": 1080, "height": 1080, "nologo": "true"}, timeout=90)
    resp.raise_for_status()
    return resp.content


def post_to_facebook(caption: str, image_bytes: bytes) -> dict:
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{FB_PAGE_ID}/photos"
    resp = requests.post(
        url,
        params={"access_token": FB_PAGE_ACCESS_TOKEN},
        data={"caption": caption},
        files={"source": ("post.jpg", image_bytes, "image/jpeg")},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    print("Generating caption...")
    caption = generate_caption()
    print(f"Caption:\n{caption}\n")

    print("Generating image prompt...")
    image_prompt = generate_image_prompt(caption)
    print(f"Image prompt: {image_prompt}")

    print("Generating image...")
    image_bytes = generate_image(image_prompt)

    print("Posting to Facebook...")
    result = post_to_facebook(caption, image_bytes)
    print(f"Posted successfully: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print(f"HTTP error: {e.response.status_code} {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
