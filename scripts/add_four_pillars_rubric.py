#!/usr/bin/env python3
"""
Add the four_pillars (Brainrot Detector) rubric to the Supabase database.
Run this once to register the four_pillars rubric.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import VideoEvaluatorDB


def main():
    print("Adding four_pillars rubric to database...")

    try:
        db = VideoEvaluatorDB()

        # Check if rubric already exists
        existing = db.get_rubric("four_pillars")
        if existing:
            print(f"Four Pillars rubric already exists: {existing['display_name']}")
            return

        # Insert the four_pillars rubric
        result = db.client.table("rubrics").upsert({
            "name": "four_pillars",
            "display_name": "🧠 Four Pillars (Brainrot Detector)",
            "description": "Evaluates children's video content against four brainrot mechanisms: Attention Hijack, Arousal Hijack, Comprehension Collapse, and Zombie Mode. Based on Lillard & Peterson, Nikkelen, Mayer, and Anderson research.",
            "category": "educational",
            "is_active": True,
            "sort_order": 1
        }).execute()

        print("✓ Four Pillars rubric added successfully!")
        print(f"  Name: four_pillars")
        print(f"  Display: 🧠 Four Pillars (Brainrot Detector)")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
