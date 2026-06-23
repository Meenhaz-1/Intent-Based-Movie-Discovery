# Environment Variables Setup Guide

This guide explains how to configure the Movie Recommender application using environment variables.

## Quick Start

Both `.env` files are already created with sensible defaults. You only need to customize them if you want to:
- Add TMDB API key for movie posters
- Change API URLs (for production)
- Modify server settings

## Backend Configuration

**File:** `backend/.env`

### Required Settings (Already Configured)
```bash
# Database and data paths
DATABASE_PATH=../checkpoints/user_preferences.sqlite
EMBEDDINGS_PATH=../checkpoints/embeddings.npy
FAISS_INDEX_PATH=../checkpoints/faiss_index.bin
MOVIE_IDS_PATH=../checkpoints/movie_ids.csv
MOVIELENS_DIR=../data/movielens
```

### Optional Settings (Recommend Configuring)

#### TMDB API Key (For Movie Posters)
```bash
TMDB_API_KEY=your_key_here
```
- Get free key: https://www.themoviedb.org/settings/api
- Without this: App works fine, but `poster_url` will be null
- Restart backend after adding

#### Server Settings
```bash
HOST=127.0.0.1          # localhost only
PORT=8000               # Change if port in use

# For production:
HOST=0.0.0.0            # Allow external connections
DEBUG_MODE=False         # Disable debug output
```

#### Recommendation Engine
```bash
RECENCY_HALF_LIFE_YEARS=20      # How quickly old ratings fade
RECENCY_WEIGHT=0.20              # 20% weight on recency
RELEVANCE_WEIGHT=0.80            # 80% weight on content relevance

DEFAULT_VARIANCE_PENALTY=0.3     # 0.0 = loose consensus, 1.0 = strict
```

#### Frontend CORS
```bash
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
CORS_CREDENTIALS=true
```

## Frontend Configuration

**File:** `frontend/.env`

### Required Settings (Already Configured)
```bash
REACT_APP_API_URL=http://localhost:8000/api
```

### Optional Settings

#### Feature Flags
```bash
REACT_APP_ENABLE_COLLABORATIVE=true      # Show collaborative recommendations
REACT_APP_ENABLE_YEAR_FILTER=true        # Enable year filtering in search
REACT_APP_ENABLE_SEMANTIC_SEARCH=true    # Show semantic search option
REACT_APP_ENABLE_KEYWORD_SEARCH=true     # Show keyword search option
```

#### UI Customization
```bash
REACT_APP_TITLE=Movie Search & Recommendations
REACT_APP_DESCRIPTION=Find movies you'll love

REACT_APP_DEFAULT_SEARCH_LIMIT=10        # Results per search
REACT_APP_DEFAULT_REC_LIMIT=10           # Recommendations shown
REACT_APP_RESULTS_PER_PAGE=20
```

#### Development
```bash
REACT_APP_DEBUG=false                    # Enable detailed logging
REACT_APP_API_TIMEOUT=30000              # API timeout (milliseconds)
```

## Setting Environment Variables

### Option 1: Use .env Files (Recommended)
Files are already created at:
- `backend/.env`
- `frontend/.env`

Just edit them directly. The app reads them automatically on startup.

### Option 2: Command Line (Development)

**Windows (PowerShell):**
```powershell
$env:TMDB_API_KEY = "your_key_here"
python -m uvicorn src.main:app --reload
```

**Windows (Command Prompt):**
```cmd
set TMDB_API_KEY=your_key_here
python -m uvicorn src.main:app --reload
```

**Mac/Linux:**
```bash
export TMDB_API_KEY="your_key_here"
python -m uvicorn src.main:app --reload
```

### Option 3: System Environment Variables (Persistent)

**Windows:**
1. Press `Win + X` → Select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Click "New" under "User variables"
5. Name: `TMDB_API_KEY`
6. Value: `your_key_here`
7. Click OK and restart terminal

**Mac/Linux:**
Add to `~/.bash_profile` or `~/.zshrc`:
```bash
export TMDB_API_KEY="your_key_here"
```

Then restart terminal or run:
```bash
source ~/.bash_profile
```

## Verification

### Check Backend Loads Correctly
```bash
cd backend
python -m uvicorn src.main:app --reload
```

Should show: `Artifacts loaded successfully!`

### Check Frontend Connects
1. Start frontend: `npm start` (in `frontend/` directory)
2. Open http://localhost:3000
3. Try searching for a movie
4. Should return results

### Verify TMDB (If Configured)
Search for "Avatar" and check:
- Results should have `year` field populated
- Results should have `poster_url` field (not null)
- Posters should load in browser

If `poster_url` is `null`:
- Check `TMDB_API_KEY` is set correctly
- Verify key has API read access enabled
- Restart backend after setting key

## Common Issues

### Backend won't start
```
ModuleNotFoundError: No module named 'src'
```
**Solution:** Run from `backend/` directory
```bash
cd backend
python -m uvicorn src.main:app --reload
```

### Frontend can't connect to API
```
Error: Failed to fetch http://localhost:8000/api/search/semantic
```
**Solutions:**
1. Check backend is running: `curl http://localhost:8000`
2. Check `REACT_APP_API_URL` in `frontend/.env`
3. Check CORS is not blocked (use browser DevTools)

### Posters not showing
```
poster_url: null
```
**Solution:** TMDB API key not configured
1. Get key from https://www.themoviedb.org/settings/api
2. Add to `backend/.env`: `TMDB_API_KEY=your_key`
3. Restart backend

### Tests fail with API timeout
**Solution:** Increase timeout in `backend/.env` or adjust pytest timeout in test file

## Production Deployment

For production, update:

**backend/.env:**
```bash
HOST=0.0.0.0                    # Accept external connections
DEBUG_MODE=False                # Disable debugging
PORT=8000                       # Or your production port
CORS_ORIGINS=["https://yourdomain.com"]
```

**frontend/.env:**
```bash
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_DEBUG=false
```

## File Locations

```
Movie Search Recommendations/
├── backend/
│   └── .env                    ← Backend configuration
├── frontend/
│   └── .env                    ← Frontend configuration
└── ENV_SETUP.md               ← This file
```

## Variables Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TMDB_API_KEY` | string | empty | TMDB API key for posters |
| `HOST` | string | 127.0.0.1 | Server host address |
| `PORT` | int | 8000 | Server port number |
| `DEBUG_MODE` | bool | False | Enable debug output |
| `DATABASE_PATH` | string | ../checkpoints/... | SQLite DB location |
| `REACT_APP_API_URL` | string | http://localhost:8000/api | Backend API URL |
| `REACT_APP_DEBUG` | bool | false | Frontend debug logging |
| `DEFAULT_RECOMMENDATION_LIMIT` | int | 10 | Recommendations returned |
| `DEFAULT_VARIANCE_PENALTY` | float | 0.3 | Collaborative strictness |

## Getting Help

If environment variables aren't working:

1. **Verify file exists:**
   - `backend/.env` exists in backend directory
   - `frontend/.env` exists in frontend directory

2. **Check file is readable:**
   ```bash
   cat backend/.env     # Should display contents
   ```

3. **Verify syntax:**
   - No quotes around values unless needed
   - One variable per line
   - Format: `KEY=value`

4. **Restart applications:**
   - Stop backend and frontend
   - Wait 2 seconds
   - Start backend first, then frontend

---

**Remember:** `.env` files are already created. Just edit them if you want to customize settings or add TMDB API key.
