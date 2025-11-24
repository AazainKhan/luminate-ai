# Feature 02: Authentication System - Backend Auth

## Goal
Create FastAPI middleware to validate Supabase JWT tokens and enforce role-based access

## Tasks Completed
- [x] Create auth middleware module
- [x] Implement JWT verification using Supabase JWKS
- [x] Create role extraction from email domain
- [x] Create require_auth, require_admin, require_student decorators
- [x] Add /api/auth/me endpoint
- [x] Update CORS to allow localhost for development

## Files Created
- `backend/app/api/middleware.py` - Authentication middleware
- Updated `backend/main.py` - Added auth endpoint

## Features Implemented
1. **JWT Verification**
   - Fetches JWKS from Supabase
   - Verifies token signature and expiration
   - Validates audience

2. **Role-Based Access Control**
   - `require_auth()` - Requires any authenticated user
   - `require_admin()` - Requires admin role
   - `require_student()` - Requires student role

3. **Email Domain Validation**
   - Extracts role from email domain
   - Returns 403 for invalid domains

## Dependencies Added
- PyJWT==2.8.0
- cryptography==42.0

## Usage Example
```python
from app.api.middleware import require_auth, require_admin

@app.get("/api/protected")
async def protected_route(user_info: dict = require_auth):
    return {"user_id": user_info["user_id"], "role": user_info["role"]}

@app.post("/api/admin-only")
async def admin_route(user_info: dict = require_admin):
    # Only admins can access
    return {"message": "Admin access granted"}
```

## Next Steps
- Test authentication flow
- Move to Feature 03: Student Chat Interface

