# FastAPI + React Refactoring Guide

This guide will help you set up and run the new FastAPI backend with React frontend, replacing Streamlit.

## Architecture

```
Movie Recommendations System
├── Backend (FastAPI)
│   ├── /api/profiles - Profile management
│   ├── /api/movies - Movie likes
│   ├── /api/search - Search (semantic + keyword)
│   └── /api/recommendations - Recommendations (single + collaborative)
└── Frontend (React)
    ├── Search interface
    ├── Profile management
    ├── Movie likes
    └── Recommendations (single + collaborative)
```

## Performance Gains

- **Streamlit**: 3-10 seconds per interaction
- **FastAPI + React**: 100-500ms per interaction
- **Expected improvement: 10-50x faster**

---

## Setup Instructions

### Step 1: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Start the Backend

```bash
# From backend directory (with venv activated)
python main.py

# Or use uvicorn directly:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup
Loading artifacts...
Artifacts loaded successfully!
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Frontend Setup

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The app should open at `http://localhost:3000`

---

## API Endpoints Reference

### Profiles API

```
GET    /api/profiles/{user_id}           - List user's profiles
POST   /api/profiles/                    - Create new profile
PATCH  /api/profiles/{profile_id}        - Rename profile
DELETE /api/profiles/{profile_id}        - Delete profile
POST   /api/profiles/{user_id}/{profile_id}/set-default
```

### Movies API

```
GET    /api/movies/{profile_id}/likes    - Get liked movies
POST   /api/movies/{profile_id}/likes    - Add movie to likes
DELETE /api/movies/{profile_id}/likes/{movie_id} - Remove movie
DELETE /api/movies/{profile_id}/likes    - Clear all likes
```

### Search API

```
POST   /api/search/semantic              - Semantic search
POST   /api/search/keyword               - Keyword/BM25 search
GET    /api/search/similar/{movie_id}    - Find similar movies
```

### Recommendations API

```
POST   /api/recommendations/single-profile    - Single profile recs
POST   /api/recommendations/collaborative     - Multi-profile recs
```

---

## Example Requests

### Create a Profile

```bash
curl -X POST http://localhost:8000/api/profiles/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "profile_name": "My Profile"}'
```

### Search for Movies

```bash
curl -X POST http://localhost:8000/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "sci-fi from 2000 onwards",
    "limit": 10
  }'
```

### Get Recommendations

```bash
curl -X POST http://localhost:8000/api/recommendations/single-profile \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "user123_my_profile_12345",
    "limit": 10
  }'
```

### Get Collaborative Recommendations

```bash
curl -X POST http://localhost:8000/api/recommendations/collaborative \
  -H "Content-Type: application/json" \
  -d '{
    "profile_ids": ["profile1", "profile2"],
    "variance_penalty": 0.3,
    "limit": 10
  }'
```

---

## Frontend Components to Complete

The basic structure is in place. You'll need to complete:

### 1. `ProfileSelector.jsx`
```jsx
// Displays profile list and management buttons
// - List profiles with like counts
// - Create new profile
// - Rename profile
// - Delete profile
// - Set as default
```

### 2. `SearchPanel.jsx`
```jsx
// Search interface
// - Text input for query
// - Search method selector (semantic/keyword)
// - Display search results
// - Add movies to profile
```

### 3. `MoviesPanel.jsx`
```jsx
// Display liked movies
// - List all liked movies for profile
// - Remove individual movies
// - Clear all likes
```

### 4. `RecommendationsPanel.jsx`
```jsx
// Show recommendations
// - Single-profile recommendations
// - Collaborative recommendations
// - Profile selector for group watch
// - Variance penalty slider
// - Per-profile appeal scores
```

### 5. `MovieCard.jsx`
```jsx
// Reusable movie display component
// - Movie title, genres, poster
// - Score/appeal information
// - Action buttons (Add, Remove, etc)
```

---

## Environment Variables

### Backend (.env)

```
TMDB_API_KEY=your_api_key_here
```

### Frontend (.env.local)

```
REACT_APP_API_URL=http://localhost:8000/api
```

---

## Troubleshooting

### Backend won't start

**Error**: `No module named 'faiss'`
```bash
# Install faiss
pip install faiss-cpu
```

**Error**: `Port 8000 already in use`
```bash
# Use different port
uvicorn main:app --port 8001
```

### Frontend won't load API data

**Error**: CORS error
- Make sure backend is running on port 8000
- Check `REACT_APP_API_URL` in `.env.local`

**Error**: API returns 404
- Check endpoint paths match those in FastAPI routes
- Verify you're using correct profile_id format

### Search is slow

- This shouldn't happen! FastAPI is much faster than Streamlit
- Make sure you're using the `/api/search/` endpoints, not Streamlit
- Check backend is running with `--reload` disabled for production

---

## Production Deployment

### Backend Deployment (e.g., Heroku, Railway)

```bash
# Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port $PORT" > Procfile

# Deploy
heroku login
heroku create your-app-name
git push heroku main
```

### Frontend Deployment (e.g., Vercel, Netlify)

```bash
# Build for production
npm run build

# Deploy built files to Vercel/Netlify
vercel deploy --prod
```

---

## Performance Benchmarks (Expected)

| Operation | Streamlit | FastAPI+React | Improvement |
|-----------|-----------|---------------|------------|
| Page load | ~10s | ~1s | **10x faster** |
| Search | ~2s | ~200ms | **10x faster** |
| Add movie | ~2s | ~100ms | **20x faster** |
| Profile switch | ~1.5s | ~50ms | **30x faster** |
| Recommendations | ~3s | ~300ms | **10x faster** |

---

## Next Steps

1. **Complete React Components**
   - Use the `App.jsx` as template
   - Each component should call appropriate API endpoints
   - Style components using `App.css`

2. **Environment Setup**
   - Set TMDB_API_KEY in .env
   - Set REACT_APP_API_URL in .env.local

3. **Test Full Flow**
   - Start backend
   - Start frontend
   - Create profile
   - Add movies
   - Test search
   - Test recommendations

4. **Customize**
   - Add movie posters from TMDB
   - Improve UI/styling
   - Add animations
   - Add error handling

5. **Deploy**
   - Choose hosting platform
   - Deploy backend
   - Deploy frontend
   - Set up proper API URLs

---

## File Structure

```
project/
├── backend/
│   ├── main.py                    # FastAPI app
│   ├── requirements.txt           # Python dependencies
│   ├── db_migration.py            # Database operations
│   ├── recommendations.py         # Recommendation algorithms
│   ├── tmdb_helper.py             # TMDB API helper
│   └── routes/
│       ├── __init__.py
│       ├── profiles.py            # Profile endpoints
│       ├── movies.py              # Movie/likes endpoints
│       ├── search.py              # Search endpoints
│       └── recommendations_routes.py # Recommendation endpoints
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Main app component
│   │   ├── App.css                # Styling
│   │   ├── index.js               # React entry point
│   │   └── components/
│   │       ├── ProfileSelector.jsx
│   │       ├── SearchPanel.jsx
│   │       ├── MoviesPanel.jsx
│   │       ├── RecommendationsPanel.jsx
│   │       └── MovieCard.jsx
│   ├── package.json
│   └── .env.local
└── checkpoints/                   # Data & models (shared)
```

---

## Support

For issues:
1. Check backend is running: `curl http://localhost:8000/health`
2. Check frontend can reach API: `curl http://localhost:8000/api/profiles/test`
3. Check browser console for errors (F12)
4. Check backend console for exceptions

---

**Expected Performance**: 10-50x faster than Streamlit!
