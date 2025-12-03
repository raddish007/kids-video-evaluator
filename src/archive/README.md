# Archived Rubrics

This directory contains deprecated rubric files that have been replaced as part of the rubric refactor (2025-11-10).

## Archived Files

### `rubric_ai_brainrot.py.bak`
**Replaced by**: `rubric_ai_quality.py`
**Initial Changes** (2025-11-10):
- Renamed for clarity ("AI Quality" vs "AI Brainrot")
- Function renamed: `get_ai_brainrot_rubric()` → `get_ai_quality_rubric()`

**Additional Refactor** (2025-11-10):
- **REMOVED**: 🟢🟡🔴 "RECOMMENDATION" section (moved to synthesis reports)
- **REMOVED**: "AI QUALITY IMPROVEMENT SUGGESTIONS" for creators (moved to creator report)
- **REMOVED**: "ACTIONABLE SUGGESTIONS" for parents/educators (moved to parent report)
- **UPDATED**: "BRAINROT SEVERITY RATING" → "AI ARTIFACT SEVERITY RATING" (more professional)
- **UPDATED**: Role clarification - now pure factual analysis, no recommendations
- **ADDED**: "OVERALL SUMMARY" section for structured output (replaced recommendations)

### `rubric_content_rating.py.bak`
**Replaced by**: `rubric_content_safety.py`
**Initial Changes** (2025-11-10):
- Renamed to focus on safety only (not overall rating)
- **REMOVED**: "Positive Content Indicators" section (educational value - moved to educational rubric)
- **REMOVED**: "Traffic-Light Safety Rating" (🟢🟡🔴 - moved to synthesis reports)
- **ADDED**: Religious/Spiritual Content descriptor with 4 levels (None/Neutral/Concerning/Inappropriate)
- Function renamed: `get_content_rating_rubric()` → `get_content_safety_rubric()`

**Additional Refactor** (2025-11-10):
- **REMOVED**: Religious/Spiritual Content section (moved to new `rubric_values_topics.py`)
- **RATIONALE**: Religious content, politics, LGBTQ+ themes are values-based topics requiring separate, carefully designed rubric
- **NEW RUBRIC**: `rubric_values_topics.py` created for hot button topics (religion, politics, LGBTQ+, other values-based content)
- **FOCUS SHIFT**: Content safety now focuses only on universal safety concerns (violence, fear, sexual content, discrimination, drugs, language)

### `rubric_creative_production.py.bak`
**Replaced by**: `rubric_production_metrics.py`
**Changes** (2025-11-10):
- Renamed to focus on pure measurement (not creative/production combined)
- **REMOVED**: Age-appropriate benchmarks for all metrics (moved to synthesis reports)
- **REMOVED**: Age appropriateness assessments
- **REMOVED**: "Overall Developmental Fit" ratings
- **REMOVED**: "Metrics-Based Recommendation" section
- **REMOVED**: "Overstimulation Risk Assessment" section (moved to synthesis reports)
- **REMOVED**: "Optimization Recommendations" section (moved to creator synthesis report)
- **REMOVED**: "Comparative Metrics" section (vs. age benchmarks and best-in-class)
- **UPDATED**: Focus is now pure factual measurement without judgments
- Function renamed: `get_creative_production_rubric()` → `get_production_metrics_rubric()`
- **RATIONALE**: Tier 1 rubrics should measure and document facts; Tier 2 synthesis reports interpret and recommend

## Why These Were Archived

Part of the rubric refactor plan to:
1. Separate specialized analysis (Tier 1) from synthesis reports (Tier 2)
2. Remove overlapping concerns between rubrics
3. Focus each rubric on a single domain
4. Prepare for multi-rubric evaluation pipeline

## Restoration

If you need to restore these files:
```bash
cp archive/rubric_ai_brainrot.py.bak ../rubric_ai_brainrot.py
cp archive/rubric_content_rating.py.bak ../rubric_content_rating.py
```

**Note**: Restoring will break compatibility with the new architecture. Only restore if reverting the entire refactor.

---

## New Rubrics Created

### `rubric_values_topics.py` (NEW - 2025-11-10)
**Purpose**: Document values-based "hot button" topics requiring family decision-making
**Covers**:
- Religious/spiritual content
- Political content
- LGBTQ+ themes
- Other values-based topics (gender roles, death, authority, etc.)

**Approach**:
- Non-judgmental documentation (not evaluation of belief validity)
- Informational disclosure for families
- Assesses age-appropriateness and presentation approach
- Helps families make values-aligned decisions

**Why separate**:
- These topics require careful, nuanced handling
- Families have diverse values - all deserve respect
- Different from universal safety concerns (violence, fear, etc.)
- Enables families to find content matching their values

### `rubric_production_metrics.py` (REFACTORED - 2025-11-10)
**Purpose**: Measure quantifiable video production characteristics
**Covers**:
- Pacing metrics (ASL, cuts/min, scene duration)
- Visual characteristics (color, complexity, movement)
- Script metrics (WPM, language characteristics, audio balance)
- Narrative structure (timing, repetition, variety)
- Audio characteristics (volume, density, layering)

**Approach**:
- Pure factual measurement without judgment
- Reports numbers and observations objectively
- No age-appropriateness assessments
- No optimization recommendations
- All interpretation moves to creator synthesis report

**Why pure measurement**:
- Tier 1 = facts, Tier 2 = interpretation
- Same metrics mean different things for different contexts
- Creator synthesis can provide optimization recommendations
- Parent synthesis can interpret appropriateness

### `rubric_media_ethics.py` (NEW - 2025-11-10)
**Purpose**: Detect manipulative tactics and commercial pressure in children's media
**Covers**:
- Marketing pressure ("like and subscribe" demands)
- Artificial urgency (FOMO, cliffhangers)
- Attention hijacking (loud sounds, retention hooks)
- Parasocial manipulation (inappropriate intimacy)
- Commercial intent (product placement, purchases)
- Platform gaming (clickbait, algorithm optimization)
- Reward loops (dopamine triggers, binge prompts)
- Emotional manipulation (guilt, shame, anxiety)
- Misleading content (bait and switch)

**Approach**:
- Pure factual documentation of tactics present
- Severity ratings (0-4 scale) for each category
- No recommendations about viewing
- All interpretation moves to synthesis reports

**Why critical**:
- Major gap in existing rubrics
- Directly impacts brain health rating
- Parents need to know about manipulation
- Commercial exploitation often hidden to children

---
**Archive Date**: 2025-11-10
**Refactor Plan**: See `/Users/carlaeng/Documents/Projects/eval/rubric-refactor-plan.md`
