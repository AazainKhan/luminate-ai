# Feature 07: LangGraph Agent Architecture - Model Routing

## Goal
Implement Router node for model selection

## Tasks Completed
- [x] Create Supervisor class
- [x] Initialize model instances (Gemini Flash, Claude Sonnet, Gemini Pro)
- [x] Implement intent detection
- [x] Route to appropriate model
- [x] Configure Google AI safety settings (BLOCK_NONE)
- [x] Create supervisor_node for LangGraph

## Files Created
- `backend/app/agents/supervisor.py` - Router implementation

## Model Selection Logic
1. **Coder Mode** → Claude 3.5 Sonnet (or Gemini Pro fallback)
   - Keywords: code, python, function, script, debug, algorithm

2. **Reasoning Mode** → Gemini 1.5 Pro
   - Keywords: calculate, derivative, formula, proof, backpropagation

3. **Syllabus Query** → Gemini 1.5 Flash
   - Keywords: when, due date, schedule, syllabus, overview

4. **Fast Mode** → Gemini 1.5 Flash (default)
   - All other queries

## Safety Settings
- All Google AI models configured with BLOCK_NONE
- Allows academic content without restrictions

## Next Steps
- Feature 07: Implement sub-agents (RAG, Syllabus)
- Feature 07: Connect to chat endpoint

