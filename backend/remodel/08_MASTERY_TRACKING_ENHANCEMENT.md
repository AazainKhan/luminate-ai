# Multi-User Mastery Tracking Enhancement

## Overview

This document describes the enhanced mastery tracking system for per-user, per-concept progress tracking with proper Supabase integration.

---

## Current State Analysis

### Existing Tables

```sql
-- student_mastery: Per-user, per-concept mastery scores
CREATE TABLE student_mastery (
  user_id UUID REFERENCES auth.users(id),
  concept_tag TEXT NOT NULL,
  mastery_score FLOAT CHECK (0 <= mastery_score <= 1),
  decay_factor FLOAT DEFAULT 0.95,
  last_assessed_at TIMESTAMP,
  PRIMARY KEY (user_id, concept_tag)
);

-- interactions: Logs all student interactions
CREATE TABLE interactions (
  id UUID PRIMARY KEY,
  student_id UUID REFERENCES auth.users(id),
  type TEXT,
  concept_focus TEXT,
  outcome TEXT,
  intent TEXT,
  agent_used TEXT,
  scaffolding_level TEXT,
  metadata JSONB,
  created_at TIMESTAMP
);
```

### Current Issues

1. **No Mastery History**: Only stores current score, not progression over time
2. **No Session Tracking**: Can't see mastery changes within a session
3. **Limited Analytics**: Hard to analyze learning patterns
4. **No Decay Implementation**: `decay_factor` exists but isn't applied automatically

---

## Enhanced Schema

### New Tables

```sql
-- Mastery history for analytics and visualization
CREATE TABLE IF NOT EXISTS mastery_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  concept_tag TEXT NOT NULL,
  mastery_score FLOAT CHECK (mastery_score >= 0 AND mastery_score <= 1),
  delta FLOAT,  -- Change from previous score
  trigger_type TEXT CHECK (trigger_type IN ('quiz', 'question', 'explanation', 'decay', 'reset')),
  session_id TEXT,  -- Group interactions by session
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for analytics queries
CREATE INDEX idx_mastery_history_user ON mastery_history(user_id);
CREATE INDEX idx_mastery_history_concept ON mastery_history(concept_tag);
CREATE INDEX idx_mastery_history_time ON mastery_history(created_at);
CREATE INDEX idx_mastery_history_session ON mastery_history(session_id);

-- Learning sessions for grouping interactions
CREATE TABLE IF NOT EXISTS learning_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  started_at TIMESTAMP DEFAULT NOW(),
  ended_at TIMESTAMP,
  concepts_touched TEXT[],
  total_interactions INTEGER DEFAULT 0,
  mastery_gained JSONB,  -- {concept: delta} for session summary
  metadata JSONB
);

CREATE INDEX idx_sessions_user ON learning_sessions(user_id);
CREATE INDEX idx_sessions_time ON learning_sessions(started_at);

-- RLS Policies
ALTER TABLE mastery_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own mastery history" ON mastery_history FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own mastery history" ON mastery_history FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can manage own sessions" ON learning_sessions FOR ALL USING (auth.uid() = user_id);
```

---

## Python Implementation

### Enhanced Mastery Service

```python
# backend/app/services/mastery_service.py

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from supabase import Client
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class MasteryUpdate:
    """Result of a mastery update operation."""
    user_id: str
    concept_tag: str
    old_score: float
    new_score: float
    delta: float
    trigger_type: str
    session_id: Optional[str] = None


@dataclass
class ConceptMastery:
    """Current mastery state for a concept."""
    concept_tag: str
    mastery_score: float
    last_assessed_at: datetime
    decay_factor: float
    trend: str  # "improving", "declining", "stable"
    recent_delta: float  # Change in last 7 days


class MasteryService:
    """
    Enhanced mastery tracking service with history and analytics.
    
    Features:
    - Per-user, per-concept tracking
    - Mastery history for visualization
    - Time-based decay
    - Session grouping
    - Learning pattern analytics
    """
    
    # Mastery calculation constants
    CORRECT_ANSWER_BOOST = 0.10
    INCORRECT_ANSWER_PENALTY = 0.05
    EXPLANATION_VIEWED_BOOST = 0.02
    CONFUSION_DETECTED_PENALTY = 0.03
    
    # Decay settings
    DECAY_HALF_LIFE_DAYS = 14  # Score decays by 50% if not practiced for 14 days
    MIN_MASTERY_SCORE = 0.0
    MAX_MASTERY_SCORE = 1.0
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def get_user_mastery(
        self,
        user_id: str,
        concepts: Optional[List[str]] = None,
        apply_decay: bool = True
    ) -> Dict[str, ConceptMastery]:
        """
        Get current mastery for all or specified concepts.
        
        Args:
            user_id: User's UUID
            concepts: Optional list of concepts to fetch
            apply_decay: Whether to apply time-based decay
            
        Returns:
            Dict mapping concept_tag to ConceptMastery
        """
        query = self.supabase.table("student_mastery").select("*").eq("user_id", user_id)
        
        if concepts:
            query = query.in_("concept_tag", concepts)
        
        result = query.execute()
        
        mastery_map = {}
        now = datetime.utcnow()
        
        for row in result.data or []:
            concept = row["concept_tag"]
            raw_score = row["mastery_score"]
            last_assessed = datetime.fromisoformat(row["last_assessed_at"].replace("Z", ""))
            decay_factor = row.get("decay_factor", 0.95)
            
            # Apply time decay if enabled
            if apply_decay:
                days_since = (now - last_assessed).days
                if days_since > 0:
                    decay_multiplier = decay_factor ** (days_since / self.DECAY_HALF_LIFE_DAYS)
                    decayed_score = raw_score * decay_multiplier
                else:
                    decayed_score = raw_score
            else:
                decayed_score = raw_score
            
            # Get trend from history
            trend, recent_delta = await self._calculate_trend(user_id, concept)
            
            mastery_map[concept] = ConceptMastery(
                concept_tag=concept,
                mastery_score=decayed_score,
                last_assessed_at=last_assessed,
                decay_factor=decay_factor,
                trend=trend,
                recent_delta=recent_delta
            )
        
        return mastery_map
    
    async def update_mastery(
        self,
        user_id: str,
        concept_tag: str,
        outcome: str,
        session_id: Optional[str] = None,
        custom_delta: Optional[float] = None
    ) -> MasteryUpdate:
        """
        Update mastery score based on interaction outcome.
        
        Args:
            user_id: User's UUID
            concept_tag: Concept identifier
            outcome: One of 'correct', 'incorrect', 'confusion_detected', 'passive_read'
            session_id: Optional session ID for grouping
            custom_delta: Optional override for score change
            
        Returns:
            MasteryUpdate with old and new scores
        """
        # Get current mastery
        current = await self.get_user_mastery(user_id, [concept_tag], apply_decay=True)
        old_score = current.get(concept_tag, ConceptMastery(
            concept_tag=concept_tag,
            mastery_score=0.5,  # Default starting mastery
            last_assessed_at=datetime.utcnow(),
            decay_factor=0.95,
            trend="stable",
            recent_delta=0.0
        )).mastery_score
        
        # Calculate delta based on outcome
        if custom_delta is not None:
            delta = custom_delta
        else:
            delta = self._calculate_delta(outcome)
        
        # Apply delta with bounds
        new_score = max(self.MIN_MASTERY_SCORE, min(self.MAX_MASTERY_SCORE, old_score + delta))
        
        # Determine trigger type
        trigger_type = self._outcome_to_trigger(outcome)
        
        # Update student_mastery table
        self.supabase.table("student_mastery").upsert({
            "user_id": user_id,
            "concept_tag": concept_tag,
            "mastery_score": new_score,
            "last_assessed_at": datetime.utcnow().isoformat(),
        }).execute()
        
        # Log to mastery_history
        self.supabase.table("mastery_history").insert({
            "user_id": user_id,
            "concept_tag": concept_tag,
            "mastery_score": new_score,
            "delta": new_score - old_score,
            "trigger_type": trigger_type,
            "session_id": session_id,
        }).execute()
        
        logger.info(f"📈 Mastery updated: {concept_tag} {old_score:.2f} → {new_score:.2f} ({delta:+.2f})")
        
        return MasteryUpdate(
            user_id=user_id,
            concept_tag=concept_tag,
            old_score=old_score,
            new_score=new_score,
            delta=delta,
            trigger_type=trigger_type,
            session_id=session_id
        )
    
    async def get_weak_concepts(
        self,
        user_id: str,
        threshold: float = 0.5,
        limit: int = 5
    ) -> List[ConceptMastery]:
        """Get concepts where mastery is below threshold."""
        all_mastery = await self.get_user_mastery(user_id, apply_decay=True)
        weak = [m for m in all_mastery.values() if m.mastery_score < threshold]
        weak.sort(key=lambda x: x.mastery_score)
        return weak[:limit]
    
    async def get_mastery_history(
        self,
        user_id: str,
        concept_tag: Optional[str] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict]:
        """Get mastery change history for visualization."""
        query = self.supabase.table("mastery_history").select("*").eq(
            "user_id", user_id
        ).gte(
            "created_at", (datetime.utcnow() - timedelta(days=days)).isoformat()
        ).order("created_at", desc=True).limit(limit)
        
        if concept_tag:
            query = query.eq("concept_tag", concept_tag)
        
        result = query.execute()
        return result.data or []
    
    async def start_session(self, user_id: str) -> str:
        """Start a new learning session."""
        result = self.supabase.table("learning_sessions").insert({
            "user_id": user_id,
        }).execute()
        
        session_id = result.data[0]["id"] if result.data else None
        logger.info(f"🎓 Started learning session: {session_id}")
        return session_id
    
    async def end_session(self, session_id: str) -> Dict:
        """End a learning session and calculate summary."""
        # Get session interactions
        history = await self._get_session_history(session_id)
        
        # Calculate mastery gained per concept
        mastery_gained = {}
        concepts_touched = set()
        
        for entry in history:
            concept = entry["concept_tag"]
            concepts_touched.add(concept)
            mastery_gained[concept] = mastery_gained.get(concept, 0) + entry.get("delta", 0)
        
        # Update session record
        self.supabase.table("learning_sessions").update({
            "ended_at": datetime.utcnow().isoformat(),
            "concepts_touched": list(concepts_touched),
            "total_interactions": len(history),
            "mastery_gained": mastery_gained,
        }).eq("id", session_id).execute()
        
        logger.info(f"🎓 Ended session {session_id}: {len(history)} interactions, {len(concepts_touched)} concepts")
        
        return {
            "session_id": session_id,
            "concepts_touched": list(concepts_touched),
            "total_interactions": len(history),
            "mastery_gained": mastery_gained,
        }
    
    async def get_learning_insights(self, user_id: str, days: int = 30) -> Dict:
        """Get learning insights and analytics."""
        history = await self.get_mastery_history(user_id, days=days, limit=500)
        
        if not history:
            return {"message": "No learning history found"}
        
        # Calculate insights
        total_interactions = len(history)
        concepts_practiced = list(set(h["concept_tag"] for h in history))
        
        # Find strongest and weakest concepts
        current_mastery = await self.get_user_mastery(user_id)
        sorted_concepts = sorted(
            current_mastery.items(),
            key=lambda x: x[1].mastery_score,
            reverse=True
        )
        
        strongest = sorted_concepts[:3] if sorted_concepts else []
        weakest = sorted_concepts[-3:] if len(sorted_concepts) >= 3 else sorted_concepts
        
        # Calculate learning velocity (mastery gained per day)
        total_delta = sum(h.get("delta", 0) for h in history)
        velocity = total_delta / max(days, 1)
        
        return {
            "total_interactions": total_interactions,
            "concepts_practiced": len(concepts_practiced),
            "strongest_concepts": [(c, m.mastery_score) for c, m in strongest],
            "weakest_concepts": [(c, m.mastery_score) for c, m in weakest],
            "learning_velocity": velocity,
            "days_analyzed": days,
        }
    
    def _calculate_delta(self, outcome: str) -> float:
        """Calculate mastery delta based on outcome."""
        deltas = {
            "correct": self.CORRECT_ANSWER_BOOST,
            "incorrect": -self.INCORRECT_ANSWER_PENALTY,
            "confusion_detected": -self.CONFUSION_DETECTED_PENALTY,
            "passive_read": self.EXPLANATION_VIEWED_BOOST,
        }
        return deltas.get(outcome, 0.0)
    
    def _outcome_to_trigger(self, outcome: str) -> str:
        """Map outcome to trigger type."""
        mapping = {
            "correct": "quiz",
            "incorrect": "quiz",
            "confusion_detected": "question",
            "passive_read": "explanation",
        }
        return mapping.get(outcome, "question")
    
    async def _calculate_trend(self, user_id: str, concept_tag: str) -> Tuple[str, float]:
        """Calculate trend for a concept based on recent history."""
        history = await self.get_mastery_history(user_id, concept_tag, days=7, limit=10)
        
        if len(history) < 2:
            return "stable", 0.0
        
        total_delta = sum(h.get("delta", 0) for h in history)
        
        if total_delta > 0.05:
            return "improving", total_delta
        elif total_delta < -0.05:
            return "declining", total_delta
        else:
            return "stable", total_delta
    
    async def _get_session_history(self, session_id: str) -> List[Dict]:
        """Get mastery history for a specific session."""
        result = self.supabase.table("mastery_history").select("*").eq(
            "session_id", session_id
        ).execute()
        return result.data or []
```

---

## API Endpoints

### Enhanced Routes

```python
# Add to backend/app/api/routes/mastery.py

@router.get("/history")
async def get_mastery_history(
    concept: Optional[str] = None,
    days: int = 30,
    user_info: dict = Depends(require_student),
):
    """Get mastery change history for visualization."""
    service = MasteryService(get_supabase_client())
    history = await service.get_mastery_history(
        user_info["user_id"],
        concept_tag=concept,
        days=days
    )
    return {"history": history}


@router.get("/insights")
async def get_learning_insights(
    days: int = 30,
    user_info: dict = Depends(require_student),
):
    """Get learning analytics and insights."""
    service = MasteryService(get_supabase_client())
    insights = await service.get_learning_insights(
        user_info["user_id"],
        days=days
    )
    return insights


@router.post("/session/start")
async def start_session(user_info: dict = Depends(require_student)):
    """Start a new learning session."""
    service = MasteryService(get_supabase_client())
    session_id = await service.start_session(user_info["user_id"])
    return {"session_id": session_id}


@router.post("/session/{session_id}/end")
async def end_session(session_id: str, user_info: dict = Depends(require_student)):
    """End a learning session and get summary."""
    service = MasteryService(get_supabase_client())
    summary = await service.end_session(session_id)
    return summary
```

---

## Frontend Integration

### Mastery Dashboard Component

```typescript
// extension/src/components/mastery/MasteryDashboard.tsx

interface ConceptMastery {
  concept_tag: string;
  mastery_score: number;
  trend: 'improving' | 'declining' | 'stable';
  recent_delta: number;
}

interface LearningInsights {
  total_interactions: number;
  concepts_practiced: number;
  strongest_concepts: [string, number][];
  weakest_concepts: [string, number][];
  learning_velocity: number;
}

export function MasteryDashboard() {
  const [mastery, setMastery] = useState<Record<string, ConceptMastery>>({});
  const [insights, setInsights] = useState<LearningInsights | null>(null);
  
  // Fetch mastery data on mount
  useEffect(() => {
    fetchMastery();
    fetchInsights();
  }, []);
  
  return (
    <div className="mastery-dashboard">
      <h2>Your Learning Progress</h2>
      
      {/* Mastery Overview */}
      <div className="mastery-grid">
        {Object.values(mastery).map(concept => (
          <ConceptCard key={concept.concept_tag} concept={concept} />
        ))}
      </div>
      
      {/* Insights Panel */}
      {insights && (
        <div className="insights-panel">
          <h3>Learning Insights</h3>
          <p>Total interactions: {insights.total_interactions}</p>
          <p>Concepts practiced: {insights.concepts_practiced}</p>
          <p>Learning velocity: {insights.learning_velocity.toFixed(3)}/day</p>
        </div>
      )}
    </div>
  );
}
```

---

## Migration Steps

1. **Run schema migration** (new tables):
   ```bash
   # Apply via Supabase SQL Editor
   ```

2. **Deploy updated backend**:
   ```bash
   docker-compose up -d --build api_brain
   ```

3. **Update frontend** to use new endpoints

4. **Backfill history** from existing interactions:
   ```sql
   INSERT INTO mastery_history (user_id, concept_tag, mastery_score, trigger_type, created_at)
   SELECT 
     student_id,
     concept_focus,
     0.5,  -- Default score (we don't have historical scores)
     CASE type
       WHEN 'quiz_attempt' THEN 'quiz'
       WHEN 'question_asked' THEN 'question'
       ELSE 'explanation'
     END,
     created_at
   FROM interactions
   WHERE concept_focus IS NOT NULL;
   ```
