# Ollama Setup Guide

Complete guide to setting up Ollama for local video evaluation.

## Installation

### 1. Install Ollama

```bash
# Install via Homebrew
brew install ollama
```

### 2. Start Ollama Server

Ollama needs to run as a background service:

```bash
# Start the server (runs in background)
ollama serve
```

**Note**: Keep this terminal open, or run in background. You can also set it up to start automatically on system boot.

### 3. Download Models

You need to download models before you can use them. Start with llava:34b:

```bash
# Primary vision model (required) - ~20GB download
ollama pull llava:34b

# Synthesis model (required) - ~4.7GB download
ollama pull llama3.1:8b-instruct
```

**Other models you can try:**

```bash
# Alternative vision models
ollama pull llava:13b           # Smaller, faster (~8GB)
ollama pull phi3.5-vision       # Very fast, lighter (~4GB)
ollama pull qwen2.5-vl:7b       # Good balance (~5GB)

# Alternative synthesis models
ollama pull llama3.1:70b-instruct  # More capable but slower (~40GB)
```

### 4. Verify Installation

```bash
# List installed models
ollama list

# Test the vision model
ollama run llava:34b "Hello, can you see images?"

# Exit with /bye
```

You should see both models listed:
- `llava:34b`
- `llama3.1:8b-instruct`

## Using Ollama with the Evaluator

### Via Streamlit UI

```bash
cd video-evaluator
python3 -m streamlit run evaluate_ui.py
```

Then:
1. Select **Ollama (Local)** as evaluator
2. Choose vision model: `llava:34b`
3. Choose synthesis model: `llama3.1:8b-instruct`
4. Set batch size: 8 frames (recommended)
5. Set max frames: 50+ (you want many frames)
6. Click "Run Evaluation"

### Expected Performance

For a 3-minute video on Mac Studio M4:

| Configuration | Estimated Time |
|---------------|----------------|
| 30 frames, batch=8 | ~5-8 minutes |
| 50 frames, batch=8 | ~8-12 minutes |
| 100 frames, batch=8 | ~15-25 minutes |

**Much slower than Claude API**, but:
- ✅ Free (no API costs)
- ✅ Runs offline
- ✅ Complete privacy (no data sent to cloud)
- ✅ Unlimited usage

## How Ollama Evaluation Works

### Batch-then-Synthesize Approach

Unlike Claude which can analyze 30+ frames at once, Ollama uses a multi-step process:

**Step 1: Batch Analysis** (~70% of time)
- Split 50 frames into batches of 8
- For each batch: Send to llava:34b for analysis
- Get partial findings from each batch

**Step 2: Synthesis** (~30% of time)
- Combine all batch analyses
- Add transcript
- Send to llama3.1:8b-instruct
- Generate final rubric-compliant report

**Example for 50 frames:**
```
50 frames ÷ 8 frames/batch = 7 batches

Batch 1: frames 1-8   → llava:34b → "No violence, bright colors..."
Batch 2: frames 9-16  → llava:34b → "Characters interacting..."
Batch 3: frames 17-24 → llava:34b → "Text on screen..."
...
Batch 7: frames 43-50 → llava:34b → "Ending sequence..."

All 7 analyses + transcript → llama3.1:8b → Final Content Rating report
```

## Troubleshooting

### "Could not connect to Ollama server"

Make sure Ollama is running:
```bash
ollama serve
```

Keep this terminal open or run in background.

### "Vision model 'llava:34b' not found locally"

Download the model:
```bash
ollama pull llava:34b
```

### "Evaluation is very slow"

This is normal! Ollama runs locally and is slower than cloud APIs. Options to speed up:
- Reduce frames (try 30 instead of 50)
- Increase batch size (10 instead of 8)
- Use faster model (llava:13b instead of 34b)
- Use smaller synthesis model (stick with 8b, not 70b)

### Out of Memory / System Sluggish

llava:34b needs significant RAM. If your Mac struggles:
- Use llava:13b instead (smaller)
- Close other applications
- Reduce batch size (6 instead of 8)
- Don't run multiple evaluations simultaneously

### Evaluation quality seems lower than Claude

This is expected. Claude is a much more capable model. Ollama is:
- Good for quick iterations
- Good for testing at no cost
- Good for offline/privacy needs
- But Claude will generally produce better, more nuanced evaluations

Use Ollama for:
- Testing your pipeline
- Rapid iteration
- Cost-free experimentation
- Privacy-sensitive content

Use Claude for:
- Final evaluations
- Highest quality analysis
- Production use

## Model Comparison

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| llava:34b | ~20GB | Slow | Best local | Production local evals |
| llava:13b | ~8GB | Moderate | Good | Balanced local option |
| phi3.5-vision | ~4GB | Fast | Decent | Quick testing |
| qwen2.5-vl:7b | ~5GB | Moderate | Good | Alternative balanced option |

## Batch Size Guidance

| Batch Size | Pros | Cons |
|------------|------|------|
| 4-6 frames | More thorough, detailed per-batch analysis | Slower, more API calls |
| 8 frames (recommended) | Good balance | - |
| 10-12 frames | Faster | May miss details, vision model has to process more |

## Configuration Recommendations

**For Content Rating (Safety-focused):**
- Vision model: `llava:34b` (most thorough)
- Batch size: 8
- Max frames: 50-70 (comprehensive coverage)

**For Quick Testing:**
- Vision model: `llava:13b` or `phi3.5-vision`
- Batch size: 10
- Max frames: 30 (faster)

**For Maximum Thoroughness:**
- Vision model: `llava:34b`
- Batch size: 6
- Max frames: 100
- Synthesis: `llama3.1:70b-instruct`
- (Warning: Very slow! ~30-45 min for 3-min video)

## Next Steps

1. Test Ollama with one video
2. Compare results to Claude evaluation of same video
3. Decide which evaluator to use for which rubrics
4. Experiment with batch sizes and frame counts
5. Find your optimal configuration
