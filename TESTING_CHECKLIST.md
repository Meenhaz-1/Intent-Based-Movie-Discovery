# User Flow Testing Checklist

## Before committing to GitHub, test all 5 core user flows:

### 1. **Search & Add to Likes**
- [ ] Navigate to "Search" tab
- [ ] Enter a movie query (e.g., "interstellar", "action", "2020 sci-fi")
- [ ] Verify search results appear with:
  - [ ] Movie title
  - [ ] Year displayed
  - [ ] Genres shown
  - [ ] Movie poster/thumbnail visible (or "No Image" placeholder)
  - [ ] Exact matches appear at the top
- [ ] Click "+ Like" button on a movie
- [ ] Verify movie is added (no error messages)

### 2. **View My Likes Tab**
- [ ] Navigate to "My Likes" tab
- [ ] Verify all liked movies display with:
  - [ ] Full title with year
  - [ ] Genres listed
  - [ ] Poster thumbnail visible
  - [ ] Year clearly shown
- [ ] Verify at least 3+ movies are displayed (from previous searches)
- [ ] Click remove button (X) and verify movie is removed

### 3. **Get Single Profile Recommendations**
- [ ] Navigate to "Recommendations" tab
- [ ] Ensure "Single Profile" mode is selected
- [ ] Select a profile from the dropdown
- [ ] Click "Load Recommendations" or wait for auto-load
- [ ] Verify recommendations appear with:
  - [ ] Movie title
  - [ ] Year displayed
  - [ ] Genres shown
  - [ ] Poster thumbnail visible
  - [ ] At least 5+ recommendations shown
- [ ] Click "+ Like" on a recommendation to verify it works

### 4. **Create New Profile & Use It**
- [ ] Click "Create Profile" button
- [ ] Enter profile name (e.g., "Test Profile 2")
- [ ] Verify new profile appears in profile list
- [ ] Switch to new profile
- [ ] Search for a movie and add it to likes
- [ ] Go to "My Likes" and verify movie is there for this profile only
- [ ] Switch back to original profile and verify different likes are shown

### 5. **Collaborative Recommendations**
- [ ] Navigate to "Recommendations" tab
- [ ] Switch to "Collaborative (Multiple Profiles)" mode
- [ ] Select 2+ profiles using checkboxes
- [ ] Adjust "Consensus Strictness" slider (0.0 to 1.0)
- [ ] Wait for recommendations to load
- [ ] Verify recommendations appear with:
  - [ ] Movie title and year
  - [ ] Per-profile appeal scores visible
  - [ ] At least 3+ recommendations shown
- [ ] Adjust slider and verify recommendations update

---

## Quick Test Checklist

Run through this **before every commit**:

```
☐ Search works and returns results with year/poster
☐ My Likes shows full movie data (title, year, genres, poster)
☐ Single profile recommendations load and display correctly
☐ New profile can be created and selected
☐ New profile has independent likes from other profiles
☐ Collaborative mode loads with 2+ profiles
☐ No console errors (check browser DevTools)
☐ No API errors (check network tab)
☐ App loads fresh without errors when starting npm start
```

## Testing Environment

**Frontend:** http://localhost:3000
**Backend:** http://localhost:8000/api
**Browser:** Chrome/Firefox DevTools Console (check for errors)

## How to Start

```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn src.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm start
```

## When Something Breaks

1. Check browser console (F12 → Console tab)
2. Check network requests (F12 → Network tab) 
3. Check backend terminal for errors
4. Verify API responds: `curl http://localhost:8000/api/search/semantic -X POST -H "Content-Type: application/json" -d '{"query":"test"}'`

## Test Data

- **Default User:** "demo_user"
- **Default Profile:** "demo_user_default" 
- **Test Movies:** Interstellar, Avatar, The Matrix, Inception, Titanic

---

## Commit Message Template

If all 5 flows pass, include in your commit:

```
[Feature/Fix]: Brief description

- Flow 1: ✓ Tested
- Flow 2: ✓ Tested  
- Flow 3: ✓ Tested
- Flow 4: ✓ Tested
- Flow 5: ✓ Tested

No breaking changes.
```

Example:
```
Add year and poster_url to all API responses

- Flow 1: Search & Add to Likes ✓ Tested
- Flow 2: View My Likes Tab ✓ Tested
- Flow 3: Single Profile Recommendations ✓ Tested
- Flow 4: Create New Profile ✓ Tested
- Flow 5: Collaborative Recommendations ✓ Tested
```
