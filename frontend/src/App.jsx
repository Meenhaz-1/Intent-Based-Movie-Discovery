import React, { useState, useEffect } from 'react';
import './App.css';
import ProfileSelector from './components/ProfileSelector';
import SearchPanel from './components/SearchPanel';
import MoviesPanel from './components/MoviesPanel';
import RecommendationsPanel from './components/RecommendationsPanel';

const API_URL = 'http://localhost:8000/api';

function App() {
  const [userId, setUserId] = useState('demo_user');
  const [profiles, setProfiles] = useState([]);
  const [selectedProfileId, setSelectedProfileId] = useState(null);
  const [likes, setLikes] = useState([]);
  const [activeTab, setActiveTab] = useState('search');
  const [loading, setLoading] = useState(false);

  // Load profiles on user change
  useEffect(() => {
    loadProfiles();
  }, [userId]);

  const loadProfiles = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/profiles/${userId}`);
      const data = await response.json();
      setProfiles(data);
      if (data.length > 0) {
        setSelectedProfileId(data[0].profile_id);
        loadProfileLikes(data[0].profile_id);
      }
    } catch (error) {
      console.error('Error loading profiles:', error);
    }
    setLoading(false);
  };

  const loadProfileLikes = async (profileId) => {
    try {
      const response = await fetch(`${API_URL}/movies/${profileId}/likes`);
      const data = await response.json();
      setLikes(data);
    } catch (error) {
      console.error('Error loading likes:', error);
    }
  };

  const handleProfileChange = (profileId) => {
    setSelectedProfileId(profileId);
    loadProfileLikes(profileId);
  };

  const handleAddMovie = async (movieId) => {
    try {
      await fetch(`${API_URL}/movies/${selectedProfileId}/likes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_id: selectedProfileId, movie_id: movieId })
      });
      loadProfileLikes(selectedProfileId);
    } catch (error) {
      console.error('Error adding movie:', error);
    }
  };

  const handleRemoveMovie = async (movieId) => {
    try {
      await fetch(`${API_URL}/movies/${selectedProfileId}/likes/${movieId}`, {
        method: 'DELETE'
      });
      loadProfileLikes(selectedProfileId);
    } catch (error) {
      console.error('Error removing movie:', error);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Movie Recommendations</h1>
        <p>Multi-profile recommendations with collaborative filtering</p>
      </header>

      <div className="app-container">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-section">
            <label>User ID</label>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="Enter user ID"
            />
          </div>

          <ProfileSelector
            profiles={profiles}
            selectedProfileId={selectedProfileId}
            onProfileChange={handleProfileChange}
            onProfilesUpdate={loadProfiles}
            userId={userId}
          />

          <div className="sidebar-section">
            <div className="metric">
              <span>Movies Liked</span>
              <span className="metric-value">{likes.length}</span>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="main-content">
          {/* Tab Navigation */}
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'search' ? 'active' : ''}`}
              onClick={() => setActiveTab('search')}
            >
              Search
            </button>
            <button
              className={`tab ${activeTab === 'likes' ? 'active' : ''}`}
              onClick={() => setActiveTab('likes')}
            >
              My Likes ({likes.length})
            </button>
            <button
              className={`tab ${activeTab === 'recommendations' ? 'active' : ''}`}
              onClick={() => setActiveTab('recommendations')}
            >
              Recommendations
            </button>
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {activeTab === 'search' && selectedProfileId && (
              <SearchPanel
                profileId={selectedProfileId}
                onAddMovie={handleAddMovie}
                likedMovies={likes}
              />
            )}

            {activeTab === 'likes' && selectedProfileId && (
              <MoviesPanel
                profileId={selectedProfileId}
                likedMovies={likes}
                onRemoveMovie={handleRemoveMovie}
              />
            )}

            {activeTab === 'recommendations' && selectedProfileId && (
              <RecommendationsPanel
                profiles={profiles}
                selectedProfileId={selectedProfileId}
                onAddMovie={handleAddMovie}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
