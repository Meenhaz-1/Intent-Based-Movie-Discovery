import React from 'react';

function MoviesPanel({ profileId, likedMovies, onRemoveMovie }) {
  if (likedMovies.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem 2rem', color: 'var(--color-text-secondary)' }}>
        <p style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>No movies liked yet</p>
        <p style={{ fontSize: '0.95rem' }}>Go to Search tab to add movies to this profile</p>
      </div>
    );
  }

  return (
    <div className="results">
      {likedMovies.map((movie) => (
        <div key={movie.movie_id} className="movie-card">
          <div className="movie-poster">
            {movie.poster_url ? (
              <img
                src={movie.poster_url}
                alt={movie.title}
                style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '4px' }}
              />
            ) : (
              'No Image'
            )}
          </div>
          <div className="movie-info">
            <div className="movie-title">{movie.title}</div>
            <div className="movie-genres">{movie.genres || 'Unknown'}</div>
            {movie.year && <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>Year: {movie.year}</div>}
          </div>
          <div className="movie-actions">
            <button
              onClick={() => onRemoveMovie(movie.movie_id)}
              className="button-danger"
            >
              Remove
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export default MoviesPanel;
