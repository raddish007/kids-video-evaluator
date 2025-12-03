#!/usr/bin/env python3
"""
Add the academic rubric to the Supabase database.
Run this once to register the academic rubric.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import VideoEvaluatorDB


def main():
    print("Adding academic rubric to database...")

    try:
        db = VideoEvaluatorDB()

        # Check if rubric already exists
        existing = db.get_rubric("academic")
        if existing:
            print(f"Academic rubric already exists: {existing['display_name']}")
            return

        # Insert the academic rubric
        result = db.client.table("rubrics").upsert({
            "name": "academic",
            "display_name": "🎓 Academic (4-Pillar Pedagogical Quality)",
            "description": "Evidence-based pedagogical quality assessment using Mayer, Bruner, Executive Function, and Bandura frameworks",
            "category": "educational",
            "is_active": True,
            "sort_order": 0
        }).execute()

        print("✓ Academic rubric added successfully!")
        print(f"  Name: academic")
        print(f"  Display: 🎓 Academic (4-Pillar Pedagogical Quality)")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
