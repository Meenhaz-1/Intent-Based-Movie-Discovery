import React, { useState } from 'react';

const API_URL = 'http://localhost:8000/api';

function SearchPanel({ profileId, onAddMovie, likedMovies }) {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('semantic');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const endpoint = searchType === 'semantic' ? 'search/semantic' : 'search/keyword';
      const response = await fetch(`${API_URL}/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
      });
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Search error:', error);
    }
    setLoading(false);
  };

  const isLiked = (movieId) => likedMovies.some(m => m.movie_id === movieId);

  return (
    <div>
      <form onSubmit={handleSearch} className="search-form">
        <div className="form-group">
          <label>Search Query</label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder='e.g., "action movies from 2020 onwards"'
          />
        </div>

        <div className="form-group">
          <label>Search Type</label>
          <select value={searchType} onChange={(e) => setSearchType(e.target.value)}>
            <option value="semantic">Semantic (AI-powered)</option>
            <option value="keyword">Keyword</option>
          </select>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {results.length > 0 && (
        <div className="results">
          {results.map((movie) => (
            <div key={movie.movie_id} className="movie-card">
              <div className="movie-poster">
                {movie.poster_url ? (
                  <img src={movie.poster_url} alt={movie.title} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '4px' }} />
                ) : (
                  'No Image'
                )}
              </div>
              <div className="movie-info">
                <div className="movie-title">{movie.title}</div>
                <div className="movie-genres">{movie.genres || 'Unknown'}</div>
                <div className="movie-score">Score: {(movie.score || 0).toFixed(2)}</div>
              </div>
              <div className="movie-actions">
                <button
                  onClick={() => onAddMovie(movie.movie_id)}
                  disabled={isLiked(movie.movie_id)}
                  className={isLiked(movie.movie_id) ? 'button-secondary' : ''}
                >
                  {isLiked(movie.movie_id) ? '✓ Liked' : '+ Like'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && query && results.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-secondary)' }}>
          No movies found
        </div>
      )}
    </div>
  );
}

export default SearchPanel;
