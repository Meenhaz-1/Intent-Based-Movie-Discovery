import React, { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000/api';

function RecommendationsPanel({ profiles, selectedProfileId, onAddMovie }) {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('single');
  const [selectedProfiles, setSelectedProfiles] = useState([selectedProfileId]);
  const [variancePenalty, setVariancePenalty] = useState(0.3);

  const loadRecommendations = async () => {
    setLoading(true);
    try {
      if (mode === 'single') {
        const response = await fetch(
          `${API_URL}/recommendations/single/${selectedProfileId}`
        );
        const data = await response.json();
        setRecommendations(data.recommendations || []);
      } else {
        const response = await fetch(
          `${API_URL}/recommendations/collaborative?profile_ids=${selectedProfiles.join(',')}&variance_penalty=${variancePenalty}`
        );
        const data = await response.json();
        setRecommendations(data.recommendations || []);
      }
    } catch (error) {
      console.error('Error loading recommendations:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadRecommendations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProfileId, mode, selectedProfiles, variancePenalty]);

  const handleProfileToggle = (profileId) => {
    setSelectedProfiles((prev) =>
      prev.includes(profileId)
        ? prev.filter((id) => id !== profileId)
        : [...prev, profileId]
    );
  };

  return (
    <div>
      {/* Mode Selector */}
      <div className="search-form">
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ marginRight: '2rem' }}>
            <input
              type="radio"
              value="single"
              checked={mode === 'single'}
              onChange={(e) => setMode(e.target.value)}
              style={{ marginRight: '0.5rem' }}
            />
            Single Profile
          </label>
          <label>
            <input
              type="radio"
              value="collaborative"
              checked={mode === 'collaborative'}
              onChange={(e) => setMode(e.target.value)}
              style={{ marginRight: '0.5rem' }}
            />
            Collaborative (Multiple Profiles)
          </label>
        </div>

        {mode === 'collaborative' && (
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem' }}>
              Select Profiles:
            </label>
            {profiles.map((profile) => (
              <label key={profile.profile_id} style={{ display: 'block', marginBottom: '0.5rem' }}>
                <input
                  type="checkbox"
                  checked={selectedProfiles.includes(profile.profile_id)}
                  onChange={() => handleProfileToggle(profile.profile_id)}
                  style={{ marginRight: '0.5rem' }}
                />
                {profile.profile_name}
              </label>
            ))}
          </div>
        )}

        {mode === 'collaborative' && (
          <div className="form-group">
            <label>
              Consensus Strictness: {variancePenalty.toFixed(1)}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={variancePenalty}
              onChange={(e) => setVariancePenalty(parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
            <small style={{ color: 'var(--color-text-secondary)' }}>
              0 = Show all movies, 1 = Only movies everyone likes
            </small>
          </div>
        )}
      </div>

      {/* Recommendations */}
      {loading ? (
        <div className="loading">Loading recommendations...</div>
      ) : recommendations.length > 0 ? (
        <div className="results">
          {recommendations.map((movie) => (
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
                {mode === 'collaborative' && movie.profiles && (
                  <div style={{ color: 'var(--color-primary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                    Appeal: {movie.appeal_scores && Object.values(movie.appeal_scores).map(s => (s * 100).toFixed(0)).join('%, ')}%
                  </div>
                )}
              </div>
              <div className="movie-actions">
                <button onClick={() => onAddMovie(movie.movie_id)}>
                  + Like
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-secondary)' }}>
          No recommendations available
        </div>
      )}
    </div>
  );
}

export default RecommendationsPanel;
