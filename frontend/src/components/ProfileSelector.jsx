import React, { useState } from 'react';

const API_URL = 'http://localhost:8000/api';

function ProfileSelector({ profiles, selectedProfileId, onProfileChange, onProfilesUpdate, userId }) {
  const [newProfileName, setNewProfileName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateProfile = async () => {
    if (!newProfileName.trim()) return;

    try {
      const response = await fetch(`${API_URL}/profiles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, profile_name: newProfileName })
      });

      if (response.ok) {
        setNewProfileName('');
        setIsCreating(false);
        onProfilesUpdate();
      }
    } catch (error) {
      console.error('Error creating profile:', error);
    }
  };


  return (
    <div className="sidebar-section">
      <label>Profiles</label>

      <div className="profile-list">
        {profiles.map((profile) => (
          <div
            key={profile.profile_id}
            className={`profile-item ${profile.profile_id === selectedProfileId ? 'active' : ''}`}
            onClick={() => onProfileChange(profile.profile_id)}
          >
            <span className="profile-name">{profile.profile_name}</span>
            <span className="profile-likes">{profile.like_count || 0} movies</span>
          </div>
        ))}
      </div>

      {isCreating ? (
        <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
          <input
            type="text"
            value={newProfileName}
            onChange={(e) => setNewProfileName(e.target.value)}
            placeholder="Profile name"
            style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
          />
          <button
            onClick={handleCreateProfile}
            style={{ padding: '8px 12px' }}
          >
            Add
          </button>
          <button
            onClick={() => setIsCreating(false)}
            className="button-secondary"
            style={{ padding: '8px 12px' }}
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          onClick={() => setIsCreating(true)}
          className="button-secondary"
          style={{ width: '100%', marginTop: '8px' }}
        >
          + New Profile
        </button>
      )}
    </div>
  );
}

export default ProfileSelector;
