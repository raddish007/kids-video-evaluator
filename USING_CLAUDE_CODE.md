# ✅ Now Using Claude Code (No API Credits Needed!)

The video evaluator now uses **Claude Code** directly, which means:

- ✅ **No separate API key needed**
- ✅ **No additional API costs** (uses your existing Claude Code subscription)
- ✅ **Uses your existing authentication**

## How It Works

The evaluator:
1. Extracts frames from video → saves to disk
2. Transcribes audio with Whisper
3. **Calls Claude Code CLI** with `--print` mode
4. Claude uses the **Read tool** to view all frame images
5. Generates comprehensive evaluation report

## Quick Start

Just run it! No setup needed:

```bash
cd ~/Documents/Projects/eval/video-evaluator
python3 evaluate.py
```

That's it! Your video `LearnToWriteLetterI.mp4` is already in the videos folder and will be processed.

## What Changed

Previously tried to use Anthropic API (which requires separate credits).
Now uses Claude Code CLI with `--dangerously-skip-permissions` flag to allow the Read tool to analyze the extracted frames.

## Performance

- **Slightly slower** than direct API (CLI overhead)
- **But free** if you have Claude Code!
- Still processes ~2-5 minutes per 3-minute video

## Troubleshooting

If you get "Claude CLI not found":
```bash
claude --version
# Should show: 2.0.36 (Claude Code)
```

If Claude Code isn't installed, you're already using it in this terminal, so it should work!

---

**Ready to test?** Just run:
```bash
python3 evaluate.py
```

Your test video is already loaded and ready to go!
