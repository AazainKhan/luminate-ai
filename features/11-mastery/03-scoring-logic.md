# Feature 11: Student Mastery Tracking - Scoring Logic

## Goal
Implement mastery score calculation with decay factor and proof-of-work protocol

## Tasks Completed
- [x] Create mastery calculation function
- [x] Implement decay factor (forgetting curve)
- [x] Create mastery API endpoints
- [x] Add update_mastery endpoint
- [x] Add get_mastery endpoint
- [x] Add get_weak_topics endpoint

## Files Created
- `backend/app/api/routes/mastery.py` - Mastery API routes
- Updated `backend/main.py` - Include mastery router

## Features Implemented
1. **Mastery Calculation**
   - Weighted average: previous_score * decay + new_score * (1 - decay)
   - Decay factor: 0.95 (5% decay per interaction)
   - Score normalization: clamped to [0, 1]

2. **API Endpoints**
   - GET /api/mastery - Get all mastery scores
   - POST /api/mastery/update - Update mastery score
   - GET /api/mastery/weak-topics - Get concepts below threshold

3. **Proof-of-Work Protocol**
   - 3-step verification (Passive, Active, Outcome)
   - Evaluator Node provides confidence scores
   - Mastery updated based on evaluation

## Decay Factor
- Default: 0.95
- Implements forgetting curve (Ebbinghaus)
- Mastery decreases over time without practice

## Next Steps
- Feature 11: Build progress visualization UI

