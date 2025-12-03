# Database Setup Guide

This guide will help you set up Supabase for the Video Evaluator project.

## Prerequisites

- A Supabase account (free tier works great!)
- Python 3.8+

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Fill in the details:
   - **Name**: video-evaluator (or your preferred name)
   - **Database Password**: Choose a strong password (you won't need this often)
   - **Region**: Choose closest to you
   - **Pricing Plan**: Free tier is perfect for this project
4. Click "Create new project" and wait ~2 minutes for provisioning

## Step 2: Run Schema SQL

1. In your Supabase project dashboard, go to **SQL Editor** (left sidebar)
2. Click "+ New query"
3. Copy the entire contents of `schema.sql` from this directory
4. Paste into the SQL Editor
5. Click "Run" or press `Cmd/Ctrl + Enter`
6. You should see "Success. No rows returned" - this is correct!

### What this creates:

- **Tables**: `videos`, `evaluations`, `rubrics`
- **Views**: `video_status`, `rubric_completion_stats`, `recent_evaluations`
- **Indexes**: For fast queries
- **Triggers**: Auto-update timestamps
- **Seed data**: 7 rubrics pre-populated

## Step 3: Get API Credentials

1. In Supabase, go to **Project Settings** (gear icon in sidebar)
2. Click **API** in the left menu
3. You'll see two important values:

   ```
   Project URL: https://xxxxxxxxxxxxx.supabase.co

   API Keys:
   - anon (public)
   - service_role (secret)
   ```

4. **Copy the `service_role` key** (NOT the anon key)
   - The service_role key bypasses Row Level Security (needed for full access)
   - Keep this secret!

## Step 4: Configure Environment Variables

1. Copy the example env file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your credentials:
   ```bash
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your_service_role_key_here

   # Your existing API keys
   ANTHROPIC_API_KEY=...
   GEMINI_API_KEY=...
   ```

3. Save the file

## Step 5: Install Dependencies

```bash
cd video-evaluator
pip install -r requirements.txt
```

This will install:
- `supabase` - Python client for Supabase
- `python-dotenv` - For loading .env files
- All existing dependencies

## Step 6: Test Connection

```bash
python src/database.py
```

You should see:
```
✓ Database connection successful

Found 0 videos
Found 7 active rubrics

Video status overview: 0 videos

Total evaluation cost: $0.0000
```

## Step 7: Import Existing Data

If you have videos already ingested in `data/videos/`, run:

```bash
python scripts/sync_to_db.py
```

This will:
- Scan your `data/videos/` directory
- Import all video metadata
- Import all evaluation results
- Show progress and summary

## Verify in Supabase Dashboard

1. Go to **Table Editor** in Supabase
2. You should see:
   - `rubrics` table with 7 rows
   - `videos` table with your imported videos
   - `evaluations` table with your evaluation results

3. Try the views:
   - Click "video_status" to see aggregated data
   - This is what the dashboard will use!

## Troubleshooting

### "SUPABASE_URL not found"
- Make sure `.env` file exists in `video-evaluator/` directory
- Check that the file has the correct variable names (not .example)

### "relation 'videos' does not exist"
- The schema wasn't run correctly
- Go back to Step 2 and make sure SQL ran successfully
- Check for error messages in the SQL editor

### "Invalid API key"
- Make sure you copied the `service_role` key, not `anon` key
- Check for extra spaces/newlines when copying
- Generate a new key if needed (Project Settings > API > "Roll" button)

### Connection timeout
- Check your internet connection
- Verify the project URL is correct
- Make sure the project is not paused (Supabase pauses inactive projects)

## Optional: Enable Real-time Updates

For live dashboard updates when evaluations complete:

1. In Supabase SQL Editor, run:
   ```sql
   ALTER PUBLICATION supabase_realtime ADD TABLE evaluations;
   ALTER PUBLICATION supabase_realtime ADD TABLE videos;
   ```

2. This allows the dashboard to subscribe to changes and auto-refresh

## Next Steps

Once setup is complete:
- Run `python scripts/sync_to_db.py` to import existing data
- Start the dashboard with `streamlit run dashboard/app.py`
- Continue using Phase 1 and Phase 2 pipelines as normal - they'll auto-sync to the database

## Database Maintenance

### Backup
Supabase provides automatic daily backups on all plans. To download:
1. Go to Database > Backups
2. Click download on any backup

### Reset Database
To start fresh:
```sql
DROP TABLE evaluations CASCADE;
DROP TABLE videos CASCADE;
DROP TABLE rubrics CASCADE;
-- Then re-run schema.sql
```

### View Logs
Go to Database > Logs to see query performance and errors
