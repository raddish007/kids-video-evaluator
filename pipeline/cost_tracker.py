"""
Cost tracking for video evaluations.
Logs token usage and costs for each evaluation run.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Pricing per 1M tokens (as of 2025)
PRICING = {
    "claude-sonnet-4-20250514": {
        "input": 3.00,   # $3 per 1M input tokens
        "output": 15.00  # $15 per 1M output tokens
    },
    "claude-opus-4-5-20251101": {
        "input": 15.00,  # $15 per 1M input tokens
        "output": 75.00  # $75 per 1M output tokens
    },
    "claude-3-5-sonnet-20241022": {
        "input": 3.00,   # $3 per 1M input tokens
        "output": 15.00  # $15 per 1M output tokens
    },
    "claude-3-haiku-20240307": {
        "input": 0.25,   # $0.25 per 1M input tokens
        "output": 1.25   # $1.25 per 1M output tokens
    },
    "models/gemini-2.5-flash": {
        "input": 0.075,   # $0.075 per 1M input tokens (after free tier)
        "output": 0.30    # $0.30 per 1M output tokens (after free tier)
    },
    "models/gemini-2.5-pro": {
        "input": 1.25,    # $1.25 per 1M input tokens
        "output": 5.00    # $5.00 per 1M output tokens
    },
    "ollama": {
        "input": 0.00,    # Free (local)
        "output": 0.00
    }
}


def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost for a model run.

    Args:
        model_name: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    if model_name not in PRICING:
        # Try to match partial names
        for key in PRICING:
            if key in model_name or model_name in key:
                model_name = key
                break
        else:
            # Default to unknown - return 0
            return 0.0

    pricing = PRICING[model_name]
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]

    return input_cost + output_cost


def log_evaluation_cost(
    model: str,
    video_id: str,
    rubric: str,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    timestamp: Optional[str] = None,
    log_file: str = "data/cost_log.jsonl"
):
    """
    Log evaluation cost to JSONL file.

    Args:
        model: Model name
        video_id: Video identifier
        rubric: Rubric name
        input_tokens: Input token count
        output_tokens: Output token count
        cost: Cost in USD
        timestamp: ISO timestamp (default: now)
        log_file: Path to log file (default: data/cost_log.jsonl)
    """
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    log_entry = {
        "model": model,
        "video_id": video_id,
        "rubric": rubric,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": round(cost, 4),
        "timestamp": timestamp
    }

    # Ensure directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Append to JSONL file
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def get_total_cost(log_file: str = "data/cost_log.jsonl") -> Dict:
    """
    Calculate total costs from log file.

    Returns:
        Dictionary with total cost and breakdown by model
    """
    if not os.path.exists(log_file):
        return {"total": 0.0, "by_model": {}}

    total = 0.0
    by_model = {}

    with open(log_file, "r") as f:
        for line in f:
            entry = json.loads(line)
            cost = entry["cost"]
            model = entry["model"]

            total += cost
            by_model[model] = by_model.get(model, 0.0) + cost

    return {
        "total": round(total, 4),
        "by_model": {k: round(v, 4) for k, v in by_model.items()}
    }
