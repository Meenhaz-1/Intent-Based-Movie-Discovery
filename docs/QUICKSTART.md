# Quickstart

This is the shortest path to get the project running locally.

## 1. Create An Environment

From the repo root:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 2. Add Optional TMDB Details

The app can show posters, plots, ratings, release dates, and cast data through TMDB.

```bash
cp .env.example .env
```

Add your key:

```bash
TMDB_API_KEY=your_key_here
```

You can skip this step. Search and recommendations still work without posters.

## 3. Download MovieLens

MovieLens 25M is required because it is too large to commit to git.

1. Download MovieLens 25M from https://grouplens.org/datasets/movielens/25m/.
2. Extract the zip.
3. Place these files directly inside `data/movielens/`:

```text
data/movielens/movies.csv
data/movielens/ratings.csv
data/movielens/tags.csv
data/movielens/links.csv
data/movielens/genome-scores.csv
data/movielens/genome-tags.csv
```

Optional datasets:

- IMDB title data: https://datasets.imdbws.com/
- TMDB 5000 metadata: https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata

## 4. Build Checkpoints

Run notebooks in order:

```bash
jupyter notebook phase_1.ipynb
jupyter notebook phase_2.ipynb
jupyter notebook phase_3.ipynb
jupyter notebook phase_4.ipynb
```

The important generated files are:

```text
checkpoints/embeddings.npy
checkpoints/faiss_index.bin
checkpoints/movie_ids.csv
checkpoints/user_preferences.sqlite
```

## 5. Start The App

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Troubleshooting

`FileNotFoundError: data/movielens/movies.csv`

Download MovieLens 25M and extract the CSV files into `data/movielens/`.

`ModuleNotFoundError`

Make sure your virtual environment is activated, then rerun `pip install -r requirements.txt`.

`faiss_index.bin` or `embeddings.npy` is missing

Run Phase 1 through Phase 3. The app needs the generated embedding and index files.

No posters appear

Add `TMDB_API_KEY` to `.env`, or enter a key in the app sidebar. This is optional.
