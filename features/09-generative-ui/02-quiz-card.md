# Feature 09: Generative UI Artifacts - QuizCard

## Goal
Build QuizCard component for multiple-choice questions with visual feedback

## Tasks Completed
- [x] Create QuizCard component
- [x] Display question and options
- [x] Handle answer selection
- [x] Show correct/incorrect feedback
- [x] Visual indicators (green/red)
- [x] Disable interaction after submission

## Files Created
- `extension/src/components/chat/QuizCard.tsx` - Component

## Features Implemented
1. **Question Display**
   - Question text
   - Multiple choice options
   - Clickable buttons

2. **Answer Feedback**
   - Green highlight for correct answer
   - Red highlight for incorrect selection
   - Check/X icons
   - Success/error messages

3. **Interaction**
   - One-time selection
   - Callback on answer
   - Disabled state after submission

## Usage
```tsx
<QuizCard
  question="What is the time complexity of BFS?"
  options={[
    { id: "1", text: "O(V + E)" },
    { id: "2", text: "O(V * E)" },
  ]}
  correctAnswerId="1"
  onAnswer={(id, isCorrect) => console.log(isCorrect)}
/>
```

## Next Steps
- Feature 09: Create CodeBlock component
- Feature 09: Create Visualizer component

