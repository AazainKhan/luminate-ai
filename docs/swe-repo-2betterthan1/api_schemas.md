# API Schemas
**Format:** JSON Schema / Pydantic

## 1. Chat Request
```json
{
  "messages": [
    {
      "role": "user",
      "content": "string",
      "parts": []
    }
  ],
  "stream": true
}
```

## 2. Chat Response (SSE Event Data)
The stream yields JSON objects prefixed with `data: `.

### Text Delta
```json
{
  "type": "text-delta",
  "textDelta": "The course syllabus covers..."
}
```

### Reasoning Delta (Optional)
```json
{
  "type": "reasoning-delta",
  "reasoningDelta": "Thinking: User is asking about dates..."
}
```

### Sources Event
```json
{
  "type": "sources",
  "sources": [
    {
      "source_filename": "Week1_Intro.pdf",
      "page_number": 5
    }
  ]
}
```

## 3. Governor Policy Check (Internal)
```python
{
    "approved": bool,
    "reason": str,
    "law_violated": Optional[str] # "scope", "integrity", "mastery"
}
```


