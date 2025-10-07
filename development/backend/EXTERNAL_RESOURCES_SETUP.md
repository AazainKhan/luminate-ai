# External Resources Setup Guide

Luminate AI can now search and display external educational resources alongside course materials. This includes:
- 📺 YouTube educational videos
- 📚 OER Commons open resources
- 🎓 Khan Academy lessons
- 🏛️ MIT OpenCourseWare

## Quick Start (Without YouTube API)

The system works **without** a YouTube API key! It will still provide:
- ✅ OER Commons search links
- ✅ Khan Academy search links  
- ✅ MIT OpenCourseWare search links

Just skip the YouTube setup and the system will gracefully handle it.

## Full Setup (With YouTube Videos)

To enable YouTube video search, you'll need a YouTube Data API key.

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Name it (e.g., "Luminate AI")
4. Click **"Create"**

### Step 2: Enable YouTube Data API v3

1. In the project dashboard, go to **"APIs & Services"** → **"Library"**
2. Search for **"YouTube Data API v3"**
3. Click on it and press **"Enable"**

### Step 3: Create API Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ Create Credentials"** → **"API Key"**
3. Copy the generated API key

### Step 4: (Optional) Restrict API Key

For security, restrict your API key:

1. Click on your API key to edit it
2. Under **"API restrictions"**, select **"Restrict key"**
3. Check only **"YouTube Data API v3"**
4. Under **"Application restrictions"**, you can add IP restrictions
5. Click **"Save"**

### Step 5: Add to Environment Variables

1. Navigate to `development/backend/`
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your YouTube API key:
   ```
   YOUTUBE_API_KEY=your_actual_api_key_here
   ```

### Step 6: Restart Backend

```bash
cd development/backend
source ../../.venv/bin/activate
python fastapi_service/main.py
```

## API Quota Information

The YouTube Data API has a daily quota limit:
- **Free tier**: 10,000 units/day
- **Search query**: ~100 units
- **This means**: ~100 searches per day for free

If you hit the quota:
- YouTube videos won't appear
- Other resources (OER, Khan Academy, MIT OCW) will still work
- Course materials are unaffected

## How It Works

When a student asks a question:

1. **Course Content Search** (ChromaDB) - runs in parallel with →
2. **External Resources Search**:
   - YouTube educational videos (if API key provided)
   - OER Commons search link
   - Khan Academy search link
   - MIT OpenCourseWare search link

3. **Combined Response**:
   ```
   [AI Answer]
   
   📚 Course Materials
   - Topic 8.2: Linear classifiers
   - Lab Tutorial: Supervised Learning
   
   🌐 Additional Learning Resources
   - [YouTube] Neural Networks Explained (3Blue1Brown)
   - [OER Commons] Search OER Commons for machine learning
   - [Khan Academy] Khan Academy: machine learning
   - [MIT OCW] MIT OpenCourseWare: machine learning
   
   💡 Related Topics
   - Backpropagation
   - Gradient Descent
   ```

## Troubleshooting

### "⚠️ YOUTUBE_API_KEY not found"
This is just a warning. The system will work without YouTube videos.

### "YouTube search error: 403"
Your API key may be restricted or quota exceeded. Check:
1. API key is correct in `.env`
2. YouTube Data API v3 is enabled
3. Daily quota not exceeded (check in Google Cloud Console)

### No YouTube videos appearing
1. Check backend logs for errors
2. Verify API key in `.env` file
3. Ensure backend was restarted after adding key
4. Check YouTube Data API quota in Google Cloud Console

## Cost Considerations

**YouTube Data API**: FREE (with quota limits)
- 10,000 units/day free tier
- ~100 units per search
- No credit card required

**Other Resources**: FREE (no API key needed)
- OER Commons, Khan Academy, MIT OCW are all free and open

## Privacy & Security

- API key is stored locally in `.env` (not committed to git)
- YouTube searches are made server-side (backend)
- No user data is sent to YouTube (only search queries)
- All external links open in new tabs with proper security attributes
