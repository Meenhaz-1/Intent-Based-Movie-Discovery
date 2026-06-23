"""TMDB API helper for fetching movie details and posters."""
import json
from pathlib import Path
from datetime import datetime, timedelta

import requests

TMDB_API_KEY = None  # Will be set from env or user input
TMDB_BASE_URL = "https://api.themoviedb.org/3"
CACHE_FILE = Path('checkpoints/tmdb_cache.json')
CACHE_EXPIRY_DAYS = 30

def set_api_key(api_key):
    """Set the TMDB API key."""
    global TMDB_API_KEY
    TMDB_API_KEY = api_key

def load_cache():
    """Load cached TMDB data."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
    return {}

def save_cache(cache):
    """Save TMDB data to cache."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)

def search_tmdb(title, year=None):
    """Search for a movie on TMDB by title."""
    if not TMDB_API_KEY:
        return None

    try:
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            'api_key': TMDB_API_KEY,
            'query': title,
            'page': 1
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()

        results = response.json().get('results', [])
        if results:
            # Return first match (or year-filtered match if available)
            if year:
                for r in results:
                    if r.get('release_date', '')[:4] == str(year):
                        return r
            return results[0]
        return None
    except Exception:
        # Silently fail - TMDB is optional
        return None

def get_movie_details(tmdb_id):
    """Get full details for a movie by TMDB ID."""
    if not TMDB_API_KEY:
        return None

    try:
        url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
        params = {
            'api_key': TMDB_API_KEY,
            'append_to_response': 'credits,reviews'
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        # Silently fail - TMDB is optional
        return None

def fetch_movie_info(movie_title, release_year=None):
    """
    Fetch movie info from TMDB, with caching.
    Returns: {'poster', 'plot', 'rating', 'release_date', 'cast', 'tmdb_id'}
    """
    cache = load_cache()

    # Check cache
    cache_key = f"{movie_title}_{release_year}"
    if cache_key in cache:
        cached = cache[cache_key]
        if cached.get('cached_at'):
            cached_date = datetime.fromisoformat(cached['cached_at'])
            if datetime.now() - cached_date < timedelta(days=CACHE_EXPIRY_DAYS):
                return cached['data']

    # Search TMDB
    search_result = search_tmdb(movie_title, release_year)
    if not search_result:
        return None

    tmdb_id = search_result.get('id')
    details = get_movie_details(tmdb_id)

    if not details:
        return None

    # Extract useful info
    info = {
        'tmdb_id': tmdb_id,
        'poster_path': details.get('poster_path'),
        'poster_url': f"https://image.tmdb.org/t/p/w342{details.get('poster_path')}" if details.get('poster_path') else None,
        'plot': details.get('overview', 'No plot available'),
        'rating': details.get('vote_average', 0),
        'vote_count': details.get('vote_count', 0),
        'release_date': details.get('release_date', 'Unknown'),
        'runtime': details.get('runtime', 0),
        'genres': [g['name'] for g in details.get('genres', [])],
        'cast': [c['name'] for c in details.get('credits', {}).get('cast', [])[:5]],  # Top 5
        'director': next((c['name'] for c in details.get('credits', {}).get('crew', []) if c['job'] == 'Director'), 'Unknown'),
        'reviews': [r['content'] for r in details.get('reviews', {}).get('results', [])[:2]],  # Top 2 reviews
    }

    # Cache it
    cache[cache_key] = {
        'data': info,
        'cached_at': datetime.now().isoformat()
    }
    save_cache(cache)

    return info

def get_poster_html(movie_info):
    """Generate HTML to display movie poster and details."""
    if not movie_info or not movie_info.get('poster_url'):
        return None

    html = f"""
    <div style="text-align: center;">
        <img src="{movie_info['poster_url']}" style="max-width: 200px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
        <p style="margin-top: 10px; font-weight: bold;">Rating: {movie_info.get('rating', 0):.1f} ({movie_info.get('vote_count', 0)} votes)</p>
    </div>
    """
    return html
