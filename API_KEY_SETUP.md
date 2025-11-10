# Setting Up Your Anthropic API Key

The video evaluator now uses the Anthropic Python SDK directly, which requires an API key.

## Quick Setup (2 minutes)

### Step 1: Get Your API Key

1. Go to: https://console.anthropic.com/settings/keys
2. Click "Create Key"
3. Give it a name (e.g., "Video Evaluator")
4. Copy the API key (starts with `sk-ant-...`)

### Step 2: Set Environment Variable

**Option A: For this session only (temporary)**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

**Option B: Permanent (recommended)**

Add to your shell profile (choose based on your shell):

**For zsh (default on modern macOS):**
```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**For bash:**
```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bash_profile
source ~/.bash_profile
```

### Step 3: Verify Setup

```bash
# Check that the key is set
echo $ANTHROPIC_API_KEY
# Should print your API key

# Run the evaluator
cd ~/Documents/Projects/eval/video-evaluator
python3 evaluate.py
```

---

## Alternative: Pass API Key Directly (Less Secure)

You can also pass the API key when running the evaluator, but this is less secure as it may be stored in your shell history:

```bash
ANTHROPIC_API_KEY='your-key-here' python3 evaluate.py
```

---

## Pricing

Anthropic Claude API pricing (as of Nov 2024):
- **Claude Sonnet 4**: ~$3 per million input tokens, ~$15 per million output tokens

**Estimated cost per video:**
- ~$0.10-0.30 per 3-minute video (depending on number of frames and transcript length)
- Most of the cost comes from the image inputs

---

## Troubleshooting

### "Anthropic API key not found"
Make sure you've set the environment variable:
```bash
echo $ANTHROPIC_API_KEY
```

If it's empty, follow Step 2 above.

### "API key is invalid"
- Make sure you copied the entire key (starts with `sk-ant-`)
- Check for extra spaces or quotes
- Try creating a new API key

### After setting the key, it's still not working
- Close and reopen your terminal
- Or run: `source ~/.zshrc` (or `source ~/.bash_profile` for bash)

---

## Security Note

⚠️ **Keep your API key secure:**
- Never commit it to git
- Don't share it publicly
- The .gitignore file already excludes any .env files

The project `.gitignore` already protects against accidentally committing keys.
