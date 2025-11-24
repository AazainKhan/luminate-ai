# Luminate AI Course Marshal - Setup Guide

## Quick Start

### 1. Environment Variables

Environment files have been created:
- `backend/.env` - Backend configuration
- `extension/.env.local` - Extension configuration

**Important**: These files contain sensitive keys. Do NOT commit them to git.

### 2. Database Setup

Database tables have been created in Supabase:
- `concepts` - Course concept hierarchy
- `student_mastery` - Student mastery tracking
- `interactions` - Interaction logging

Row Level Security (RLS) policies are enabled.

### 3. Install Dependencies

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Extension:**
```bash
cd extension
npm install
```

### 4. Start Docker Containers

```bash
docker-compose up -d
```

This starts:
- FastAPI backend (port 8000)
- ChromaDB (port 8001)
- Redis (port 6379)
- Langfuse (port 3000)
- PostgreSQL for Langfuse

### 5. Start Backend (if not using Docker)

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### 6. Build Extension

```bash
cd extension
npm run dev
```

### 7. Load Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension` directory
5. The extension will appear in your extensions list

### 8. Access the Extension

- **Student Chat**: Click the extension icon, then open the side panel
- **Admin Dashboard**: Sign in with @centennialcollege.ca email, then access admin panel

## Configuration Checklist

- [x] Supabase project created
- [x] Database tables created
- [x] Environment variables configured
- [ ] Docker containers running
- [ ] Backend dependencies installed
- [ ] Extension dependencies installed
- [ ] Extension loaded in Chrome

## Testing

1. **Test Authentication:**
   - Try signing in with @my.centennialcollege.ca email (student)
   - Try signing in with @centennialcollege.ca email (admin)

2. **Test Chat:**
   - Send a message in the student chat
   - Verify streaming response

3. **Test Admin Panel:**
   - Upload a Blackboard export ZIP
   - Check ETL status

4. **Test Code Execution:**
   - Ask a coding question
   - Click "Run" on a code block

## Troubleshooting

- **Extension not loading**: Check browser console for errors
- **Backend not connecting**: Verify Docker containers are running
- **Auth errors**: Check Supabase credentials in .env files
- **ChromaDB errors**: Ensure ChromaDB container is running

## Next Steps

1. Pre-load COMP 237 course data:
   ```python
   from app.etl.pipeline import run_etl_pipeline
   from pathlib import Path
   
   run_etl_pipeline(
       Path("/path/to/raw_data"),
       course_id="COMP237"
   )
   ```

2. Test the full flow:
   - Student asks question
   - Agent retrieves context
   - Response streams back
   - Mastery updates



## Quick Start

### 1. Environment Variables

Environment files have been created:
- `backend/.env` - Backend configuration
- `extension/.env.local` - Extension configuration

**Important**: These files contain sensitive keys. Do NOT commit them to git.

### 2. Database Setup

Database tables have been created in Supabase:
- `concepts` - Course concept hierarchy
- `student_mastery` - Student mastery tracking
- `interactions` - Interaction logging

Row Level Security (RLS) policies are enabled.

### 3. Install Dependencies

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Extension:**
```bash
cd extension
npm install
```

### 4. Start Docker Containers

```bash
docker-compose up -d
```

This starts:
- FastAPI backend (port 8000)
- ChromaDB (port 8001)
- Redis (port 6379)
- Langfuse (port 3000)
- PostgreSQL for Langfuse

### 5. Start Backend (if not using Docker)

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### 6. Build Extension

```bash
cd extension
npm run dev
```

### 7. Load Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension` directory
5. The extension will appear in your extensions list

### 8. Access the Extension

- **Student Chat**: Click the extension icon, then open the side panel
- **Admin Dashboard**: Sign in with @centennialcollege.ca email, then access admin panel

## Configuration Checklist

- [x] Supabase project created
- [x] Database tables created
- [x] Environment variables configured
- [ ] Docker containers running
- [ ] Backend dependencies installed
- [ ] Extension dependencies installed
- [ ] Extension loaded in Chrome

## Testing

1. **Test Authentication:**
   - Try signing in with @my.centennialcollege.ca email (student)
   - Try signing in with @centennialcollege.ca email (admin)

2. **Test Chat:**
   - Send a message in the student chat
   - Verify streaming response

3. **Test Admin Panel:**
   - Upload a Blackboard export ZIP
   - Check ETL status

4. **Test Code Execution:**
   - Ask a coding question
   - Click "Run" on a code block

## Troubleshooting

- **Extension not loading**: Check browser console for errors
- **Backend not connecting**: Verify Docker containers are running
- **Auth errors**: Check Supabase credentials in .env files
- **ChromaDB errors**: Ensure ChromaDB container is running

## Next Steps

1. Pre-load COMP 237 course data:
   ```python
   from app.etl.pipeline import run_etl_pipeline
   from pathlib import Path
   
   run_etl_pipeline(
       Path("/path/to/raw_data"),
       course_id="COMP237"
   )
   ```

2. Test the full flow:
   - Student asks question
   - Agent retrieves context
   - Response streams back
   - Mastery updates


