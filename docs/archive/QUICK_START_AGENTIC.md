# Quick Start: Agentic Features

This guide will help you get started with the new agentic features in Luminate AI.

## 🚀 Getting Started

### Prerequisites

1. **Backend Running**:
   ```bash
   cd /Users/aazain/Documents/GitHub/luminate-ai/development/backend
   python -m uvicorn fastapi_service.main:app --reload --host 127.0.0.1 --port 8000
   ```

2. **ChromaDB Setup**:
   Ensure ChromaDB is populated with course content (see main README).

3. **Extension Built**:
   ```bash
   cd /Users/aazain/Documents/GitHub/luminate-ai/chrome-extension
   npm install
   npm run build
   ```

4. **Extension Loaded**:
   - Open `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select `chrome-extension/dist/` folder

## 🎯 Features Overview

### 1. **Navigate & Educate Modes** (Existing)
Semantic search and deep learning explanations for COMP-237 topics.

### 2. **Dashboard** (NEW)
- View learning progress
- Track quiz performance
- Identify weak areas
- Get topic recommendations

**How to use**:
1. Click the **Dashboard** tab
2. View your learning statistics
3. Click **Refresh** to update data

### 3. **Concept Graph** (NEW)
- Visualize topic relationships
- See prerequisites for topics
- Track mastery levels
- Plan learning paths

**How to use**:
1. Click the **Graph** tab
2. Browse topics by module
3. Click a topic to see prerequisites and next steps
4. Use mastery colors to identify focus areas

### 4. **Notes** (NEW)
- Create notes while learning
- Tag notes by topic
- Search your notes
- Auto-sync to cloud

**How to use**:
1. Click the **Notes** button in the header
2. Click **+** to create a new note
3. Add topic (optional) and content
4. Notes save automatically
5. Search notes using the search bar

### 5. **Quiz System** (NEW)
- AI-generated quizzes
- Immediate feedback
- Explanations for each answer
- Performance tracking

**How to use** (Coming soon in chat interface):
The quiz feature is fully implemented on the backend and has UI components ready. Integration into chat responses is pending.

To test manually:
```bash
curl -X POST http://localhost:8000/api/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Neural Networks",
    "difficulty": "medium",
    "count": 5
  }'
```

## 🎨 UI Navigation

### Top Header Buttons
- **Theme Toggle**: Switch between light/dark mode
- **Notes**: Open notes sidebar
- **History**: View chat history
- **Settings**: Adjust preferences

### Bottom Tabs
- **Navigate**: Fast semantic search
- **Educate**: Deep conceptual learning
- **Dashboard**: Progress tracking (NEW)
- **Graph**: Concept relationships (NEW)

## 📊 Understanding the Dashboard

### Key Metrics
- **Topics Mastered**: Count of topics with 80%+ mastery
- **Current Streak**: Days of continuous learning
- **Quizzes Taken**: Total quiz attempts
- **Performance**: Trend indicator (up/down/stable)

### Status Indicators
- **🟢 On Track**: Average score ≥70% and ≥3 topics mastered
- **🟠 Keep Pushing**: Below targets, needs focus

### Recommendations
- **Weak Topics**: Areas needing improvement (red badges)
- **Recommended Next**: Suggested topics to study (blue badges)

## 🗺️ Using the Concept Graph

### Mastery Colors
- **🟢 Green**: Mastered (80-100%)
- **🟡 Yellow**: Good (50-79%)
- **🟠 Orange**: Learning (1-49%)
- **⚪ Gray**: Not Started (0%)

### Topic Details
Click any topic to see:
- **Prerequisites**: Topics to learn first
- **Next Steps**: Topics to learn after

### Planning Your Path
1. Find a topic you want to learn
2. Check its prerequisites
3. Learn prerequisites first
4. Return to the original topic
5. Follow next steps to continue

## 🔔 Notes Best Practices

### When to Take Notes
- Key concepts from lectures
- Important formulas or algorithms
- Personal insights
- Questions for later

### Using Topics
- Tag notes with relevant course topics
- Makes notes searchable
- Groups related notes together

### Context Feature
Notes can store additional context (e.g., which lecture, which page).
This is automatically added when creating notes from chat responses (coming soon).

## 🎓 Quiz Tips

### Selecting Difficulty
- **Easy**: Basic concept recall
- **Medium**: Application and understanding
- **Hard**: Complex scenarios and analysis

### After Taking a Quiz
1. Review incorrect answers
2. Read the explanations carefully
3. Make notes on concepts you missed
4. Retake quiz to reinforce learning

## 🔧 Troubleshooting

### Backend Not Responding
```bash
# Check if backend is running
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

### Extension Not Loading
1. Check Console for errors (F12 → Console)
2. Reload extension: `chrome://extensions/` → Reload
3. Check manifest.json is in dist/

### Data Not Showing
Currently using mock data for:
- Dashboard statistics
- Concept graph
- Quiz results

Real data will be available after Supabase integration (see TODO in backend code).

### Notes Not Syncing
- Notes are saved locally first
- Cloud sync happens in background
- Check for "Syncing..." indicator
- If offline, notes save locally and sync when online

## 🚀 Next Steps

### For Students
1. Complete a topic in Navigate/Educate mode
2. Take notes on key concepts
3. Generate a quiz to test yourself
4. Check Dashboard to see progress
5. Use Concept Graph to plan next topic

### For Developers
1. Integrate Supabase for real data
2. Add quiz triggers in chat responses
3. Implement streaming chat in UI
4. Add agent traces to messages
5. Create tests for new features

## 📚 Additional Resources

- **Implementation Details**: See `AGENTIC_FEATURES_IMPLEMENTED.md`
- **Full Plan**: See `plan.md`
- **API Documentation**: FastAPI auto-docs at `http://localhost:8000/docs`
- **Component Storybook**: (Coming soon)

## 💡 Pro Tips

1. **Use Dashboard** to identify weak topics before exams
2. **Check Concept Graph** before starting a new topic to see prerequisites
3. **Take notes** while using Navigate mode for quick reference
4. **Generate quizzes** regularly to reinforce learning
5. **Track your streak** to build consistent study habits

---

**Happy Learning!** 🎉

For issues or questions, check the main README or create an issue on GitHub.

