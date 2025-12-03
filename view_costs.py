#!/usr/bin/env python3
"""
View cost logs from evaluations.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def view_costs(log_file="data/cost_log.jsonl"):
    """Display cost logs in a readable format."""

    if not Path(log_file).exists():
        print(f"No cost log found at {log_file}")
        print("Costs will be logged as evaluations run.")
        return

    # Read all log entries
    entries = []
    with open(log_file, "r") as f:
        for line in f:
            entries.append(json.loads(line))

    if not entries:
        print("Cost log is empty.")
        return

    # Calculate totals
    total_cost = sum(e["cost"] for e in entries)
    total_input_tokens = sum(e["input_tokens"] for e in entries)
    total_output_tokens = sum(e["output_tokens"] for e in entries)

    # Group by model
    by_model = defaultdict(lambda: {"cost": 0, "count": 0, "input": 0, "output": 0})
    for entry in entries:
        model = entry["model"]
        by_model[model]["cost"] += entry["cost"]
        by_model[model]["count"] += 1
        by_model[model]["input"] += entry["input_tokens"]
        by_model[model]["output"] += entry["output_tokens"]

    # Group by video
    by_video = defaultdict(lambda: {"cost": 0, "evaluations": []})
    for entry in entries:
        vid = entry["video_id"]
        by_video[vid]["cost"] += entry["cost"]
        by_video[vid]["evaluations"].append(entry)

    # Print summary
    print("=" * 80)
    print("COST SUMMARY")
    print("=" * 80)
    print(f"\nTotal Evaluations: {len(entries)}")
    print(f"Total Cost: ${total_cost:.4f}")
    print(f"Total Tokens: {total_input_tokens:,} input / {total_output_tokens:,} output")

    print("\n" + "-" * 80)
    print("BY MODEL")
    print("-" * 80)
    for model, stats in sorted(by_model.items()):
        print(f"\n{model}:")
        print(f"  Evaluations: {stats['count']}")
        print(f"  Cost: ${stats['cost']:.4f}")
        print(f"  Tokens: {stats['input']:,} in / {stats['output']:,} out")

    print("\n" + "-" * 80)
    print("BY VIDEO")
    print("-" * 80)
    for video_id, stats in sorted(by_video.items(), key=lambda x: x[1]["cost"], reverse=True):
        print(f"\n{video_id}:")
        print(f"  Evaluations: {len(stats['evaluations'])}")
        print(f"  Cost: ${stats['cost']:.4f}")
        for eval in stats['evaluations']:
            print(f"    - {eval['rubric']} ({eval['model'].split('/')[-1]}): ${eval['cost']:.4f}")

    print("\n" + "-" * 80)
    print("RECENT EVALUATIONS (Last 10)")
    print("-" * 80)
    for entry in entries[-10:]:
        timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        model_short = entry['model'].split('/')[-1]
        print(f"{timestamp} | {entry['video_id'][:30]:30} | {entry['rubric']:20} | "
              f"{model_short:20} | ${entry['cost']:.4f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    log_file = sys.argv[1] if len(sys.argv) > 1 else "data/cost_log.jsonl"
    view_costs(log_file)
