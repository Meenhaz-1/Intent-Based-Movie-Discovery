# Quick Start Guide — Phase 1

## Before You Run the Notebook

### Step 1: Install Dependencies
```bash
pip install -r requirements_phase1.txt
```

This installs:
- `pandas` — data manipulation
- `duckdb` — analytical queries
- `numpy` — numerical operations
- `requests` — downloading IMDB data

### Step 2: Download Manual Datasets

**MovieLens 25M** (REQUIRED — no Phase 1 without this):
1. Go to https://grouplens.org/datasets/movielens/25m/
2. Click "Download ml-25m.zip" (takes a few minutes)
3. Extract to: `data/movielens/`
4. Verify these files exist:
   - `data/movielens/movies.csv`
   - `data/movielens/ratings.csv`
   - `data/movielens/tags.csv`

**TMDB Metadata** (OPTIONAL but recommended):
1. Go to https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata
2. Download the dataset (requires Kaggle account)
3. Extract to: `data/tmdb/`
4. Verify these files exist:
   - `data/tmdb/tmdb_5000_movies.csv`
   - `data/tmdb/tmdb_5000_credits.csv`

**IMDB Data** (AUTO-DOWNLOADED):
- The notebook will fetch this automatically
- Files go to: `data/imdb/`
- If download fails, manually download from https://datasets.imdbws.com/

### Step 3: Create Data Directory
```bash
mkdir data
mkdir checkpoints
```

### Step 4: Run the Notebook

```bash
jupyter lab phase_1.ipynb
```

Then:
1. Run cells in order (top to bottom)
2. Pay attention to any `⚠ WARNING` messages
3. Review the data quality report at the end
4. Check that all acceptance criteria show `✓ PASS`

## Expected Output

After running Phase 1, you should see:

```
✓ Data Sourcing & Exploration Complete

Key Statistics:
- Movies loaded: ~25,000
- Ratings loaded: ~25 million
- Tags loaded: ~1.1 million
- IMDB titles: ~10 million
- IMDB ratings: ~1 million

Artifacts saved:
✓ checkpoints/movies.duckdb (analytics database)
✓ checkpoints/movies.sqlite (user state database)
✓ checkpoints/phase1_quality_report.txt
✓ checkpoints/data_dictionary.txt
```

## Troubleshooting

**Problem**: `FileNotFoundError: data/movielens/movies.csv`
- **Solution**: Download MovieLens 25M manually and extract to `data/movielens/`

**Problem**: IMDB download fails
- **Solution**: Manually download `title.basics.tsv.gz` and `title.ratings.tsv.gz` from https://datasets.imdbws.com/ and place in `data/imdb/`

**Problem**: Out of memory errors
- **Solution**: Your machine may have <8GB RAM. The notebook will subsample larger datasets automatically.

**Problem**: Jupyter command not found
- **Solution**: Install Jupyter: `pip install jupyter jupyterlab`

## Next Steps After Phase 1

1. Review the generated reports:
   - `checkpoints/phase1_quality_report.txt`
   - `checkpoints/data_dictionary.txt`

2. Make note of any warnings or missing fields

3. Move to Phase 2 when ready:
   - Phase 2 loads the DuckDB/SQLite from Phase 1
   - No need to re-run Phase 1 (checkpoints persist)

## Questions?

Refer to:
- `README.md` — Full project overview
- `Movie_Recommendation_PRD_v1.0.docx` — Product requirements
- `Movie_Recommendation_TRD_v1.0.docx` — Technical requirements

---

Good luck! 🚀
