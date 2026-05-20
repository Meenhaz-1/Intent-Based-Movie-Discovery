# 🎬 Movie Recommendation System

A complete end-to-end movie recommendation engine built with Python, combining **content-based** and **collaborative filtering** approaches. Learn how modern recommendation systems work with a dataset of 62K movies, 25M ratings, and 1.1M user tags.

## ✨ Features

### Phase 1: Data Sourcing & Exploration ✅
- Load 62K movies from MovieLens with 25M ratings and 1.1M tags
- Optional IMDB data integration (746K movies, 1.67M ratings)
- DuckDB for analytics, SQLite for user state persistence
- Comprehensive data profiling with null patterns and summary statistics

### Phase 2: Content-Based Similarity ✅
- **Approach A**: TF-IDF vectorization (5K features) with cosine similarity
- **Approach B**: Dense embeddings (384-dim) using `sentence-transformers` + FAISS IndexFlatIP
- Side-by-side comparison of both approaches
- Fast similarity search for 62K movies

### Phase 3: Semantic Search ✅
- **Approach A**: BM25 keyword search on genres + user tags
- **Approach B**: Semantic search using embeddings + FAISS
- Smart hybrid search: title match → thematic results
- User-selectable search modes (Movie/Theme/Title-Only)

### Phase 4: Personalized Recommendations ✅
- **Content-based**: User preference vectors from movie embeddings
- **Collaborative Filtering**: User similarity via cosine distance
- **Cold-start mitigation**: Content-only (0-10 likes) → Blended (10+ likes)
- **Configurable blending**: 70% content + 30% CF (adjustable)
- User preference persistence with SQLite
- Offline evaluation metrics (Precision@K, NDCG@K)

### Interactive Streamlit UI ✅
- 🔍 **Search**: Find movies by title or theme
- 📊 **Similar**: Discover movies like your favorites
- ❤️ **My Likes**: Track your movie profile
- 🎯 **Recommendations**: Get personalized picks
- 🎬 **Movie Details**: Posters, plots, ratings, cast (via TMDB)

## 🏗️ Project Structure

```
Movie-semantic-search-recommender/
├── app.py                        # Streamlit interactive UI
├── tmdb_helper.py                # TMDB API integration
├── phase_1.ipynb                 # Data sourcing & exploration
├── phase_2.ipynb                 # Content-based similarity
├── phase_3.ipynb                 # Semantic search
├── phase_4.ipynb                 # Personalized recommendations
├── requirements_phase4.txt        # All dependencies
├── .env.example                  # Environment template
├── .env                          # Your TMDB API key (not committed)
├── .gitignore                    # Git exclusions
├── checkpoints/                  # Saved models & embeddings
│   ├── embeddings.npy            # 62K × 384 embedding matrix
│   ├── faiss_index.bin           # FAISS vector index
│   ├── movie_ids.csv             # Movie metadata
│   ├── user_preferences.sqlite   # User like history
│   └── tmdb_cache.json           # Cached TMDB data
├── results/                      # Analysis & recommendations
├── data/movielens/               # MovieLens dataset (62K movies, 25M ratings)
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip or conda
- TMDB API key (free from [themoviedb.org](https://www.themoviedb.org/settings/api))
- ~10 GB disk space for MovieLens data

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Meenhaz-1/Movie-semantic-search-recommender.git
cd Movie-semantic-search-recommender
```

2. **Create virtual environment**
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements_phase4.txt
```

4. **Set up environment variables**
```bash
# Copy example and add your TMDB API key
cp .env.example .env
# Edit .env:
# TMDB_API_KEY=your_api_key_here
```

5. **Download external datasets**
   - See [Large Files Not Included](#large-files-not-included) for the exact files and sources.
   - At minimum, download MovieLens 25M into `data/movielens/`.
   - Then run the notebooks in order to rebuild `checkpoints/` and `results/`.

6. **Run the interactive app**
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

## Large Files Not Included

Large datasets, generated indexes, caches, and local secrets are intentionally excluded from git. Download or regenerate the following files after cloning the repository.

| Local path | Required? | Source / how to create |
|------------|-----------|------------------------|
| `data/movielens/` | Required | Download MovieLens 25M from https://grouplens.org/datasets/movielens/25m/. Extract `ml-25m.zip` so files like `movies.csv`, `ratings.csv`, `tags.csv`, `links.csv`, `genome-scores.csv`, and `genome-tags.csv` are directly inside `data/movielens/`. |
| `data/imdb/title.basics.tsv.gz` | Optional for Phase 1 enrichment | Download from https://datasets.imdbws.com/title.basics.tsv.gz, or let `phase_1.ipynb` download it. |
| `data/imdb/title.ratings.tsv.gz` | Optional for Phase 1 enrichment | Download from https://datasets.imdbws.com/title.ratings.tsv.gz, or let `phase_1.ipynb` download it. |
| `data/tmdb/tmdb_5000_movies.csv` | Optional TMDB metadata | Download the TMDB 5000 Movie Dataset from https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata and extract this file into `data/tmdb/`. |
| `data/tmdb/tmdb_5000_credits.csv` | Optional TMDB metadata | Download the same Kaggle dataset and extract this file into `data/tmdb/`. |
| `.env` | Required for poster/details API calls | Copy `.env.example` to `.env`, then add your TMDB API key from https://www.themoviedb.org/settings/api. |
| `checkpoints/` | Generated | Run `phase_1.ipynb` through `phase_4.ipynb`. This creates files such as `movies.duckdb`, `movie_ids.csv`, `embeddings.npy`, `faiss_index.bin`, and local SQLite state. |
| `results/` | Generated | Created by the notebooks for comparison reports, evaluation output, and sample recommendations. |

Suggested folder layout after downloads:

```text
data/
  movielens/
    movies.csv
    ratings.csv
    tags.csv
    links.csv
    genome-scores.csv
    genome-tags.csv
  imdb/
    title.basics.tsv.gz
    title.ratings.tsv.gz
  tmdb/
    tmdb_5000_movies.csv
    tmdb_5000_credits.csv
```

## 📖 Usage

### Interactive App (Recommended)

```bash
streamlit run app.py
```

**Features:**

1. **🔍 Search Tab**
   - Find movies by title: "Interstellar" → exact match + similar films
   - Find by theme: "space exploration" → thematic search
   - Choose: Semantic (meaning) vs Keyword (BM25)
   - Click "❤️ Add" to add to your profile

2. **📊 Similar Tab**
   - Pick any movie → see 10 most similar ones
   - Uses embedding-based similarity
   - Add similar movies to your likes

3. **❤️ My Likes Tab**
   - View all movies you've liked
   - Track progress toward 15 movies
   - Remove movies with 🗑️ button
   - See strategy change at 10 likes

4. **🎯 Recommendations Tab**
   - Get personalized picks based on your likes
   - 0-10 likes: Content-based only
   - 10+ likes: Blended (70% content + 30% CF)
   - Recommendations improve as you add more movies

### Jupyter Notebooks

For detailed understanding of each phase:

```bash
jupyter notebook phase_1.ipynb   # Data exploration
jupyter notebook phase_2.ipynb   # Content-based similarity
jupyter notebook phase_3.ipynb   # Semantic search
jupyter notebook phase_4.ipynb   # Personalized recommendations
```

## ⚙️ Configuration

### TMDB API Key

Edit `.env` with your TMDB API key:
```bash
TMDB_API_KEY=your_key_here
```

The app automatically:
- Loads from `.env` on startup
- Falls back to manual input if `.env` missing
- Caches results to avoid API rate limits

### Recommendation Blending

In `app.py`, adjust the blend ratio:
```python
blend_ratio = 0.7  # 70% content-based, 30% collaborative filtering
```

## 📊 Results & Performance

### Datasets
- **MovieLens**: 62,423 movies, 25M ratings, 1.1M tags
- **Embeddings**: 384-dimensional vectors via `sentence-transformers`
- **FAISS Index**: Exact similarity search over 62K movies

### Performance (on 8GB RAM)
- Search query: <100ms
- Recommendation generation: <50ms
- BM25 indexing: <5s
- Cold start with 5 likes: instant

### Recommendation Quality

| Likes | Strategy | Precision@10 | Notes |
|-------|----------|-------------|-------|
| 5 | Content-only | 20% | Few overlaps with test set |
| 10 | Blended (70/30) | Variable | CF starts finding users |
| 15 | Blended (70/30) | Variable | More diverse, user-specific |

## 🎓 Key Learnings

### 1. Embeddings vs Keyword Search
- **TF-IDF**: Fast, interpretable, keyword-dependent
- **Embeddings**: Slower, captures meaning, works on themes
- **BM25**: Best at genre matching
- **Semantic**: Best at thematic concepts

### 2. Cold-Start Problem
- **Content-based**: Works with 1-2 likes (no collaborative data needed)
- **Collaborative Filtering**: Needs 10+ likes to find similar users
- **Mitigation**: Blend both approaches as data grows

### 3. User Modeling
- User preference vector = average of liked movie embeddings
- Works surprisingly well with just 5-10 examples
- Becomes increasingly accurate with more data

### 4. Recommendation Blending
- 70% content + 30% CF provides best user experience
- Pure content-based: too narrow, ignores community
- Pure CF: requires too much data, cold-start fails
- Blended: captures both personalization + discovery

## 🔐 Security

- ✅ API keys in `.env` (not in git)
- ✅ `.env` listed in `.gitignore`
- ✅ Local SQLite (no external DB credentials)
- ✅ TMDB data cached locally (minimize API calls)

## 📚 Technical Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Data Loading | pandas | Simple CSV/JSON handling |
| Embeddings | sentence-transformers | Lightweight, pre-trained, accurate |
| Vector Search | FAISS | Fast ANN for 62K vectors |
| Keyword Search | rank-bm25 | Pure Python, no dependencies |
| Databases | DuckDB + SQLite | No server needed, local only |
| UI | Streamlit | Interactive, zero-config deployment |
| Caching | JSON files | Simple, persistent, no setup |

## 🚀 Next Steps

### Deploy the App
```bash
# Docker (optional)
docker build -t movie-recommender .
docker run -p 8501:8501 movie-recommender

# Or Streamlit Cloud
streamlit run app.py --logger.level=info
```

### Enhancements
- [ ] Fine-tune embeddings on MovieLens ratings
- [ ] Add review sentiment to recommendations
- [ ] Matrix factorization for CF
- [ ] A/B testing framework
- [ ] Real-time feedback loop

## 📝 License

MIT License - Free to use for learning or commercial purposes

## 🤝 Contributing

This is a learning project. Contributions welcome!

Areas for improvement:
- Advanced CF algorithms (SVD, NMF)
- Deep learning recommendations (neural CF, attention)
- Multi-armed bandit exploration/exploitation
- Per-user blending ratios
- Real-time model updates

## 📞 Support

Questions? Check:
1. Phase notebooks for implementation details
2. Streamlit app code for usage examples
3. TMDB docs for API questions

---

**Built with ❤️ as a comprehensive learning project for recommendation systems**

Perfect for:
- Learning recommendation system architectures
- Understanding content-based + collaborative filtering
- Exploring embeddings and semantic search
- Building production-grade UIs with Streamlit
- Working with real-world movie data

Last updated: May 2026
Status: ✅ All 4 phases complete | ✅ Interactive UI live | ✅ Production ready
