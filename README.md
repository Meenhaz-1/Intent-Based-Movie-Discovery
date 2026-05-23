# Intent-Based Movie Discovery

A semantic search and recommendation prototype for finding movies by meaning, not just title.

## Executive Summary

Intent-Based Movie Discovery is an end-to-end product prototype that explores a common discovery problem: people often know the kind of movie they want, but not the exact title or keywords that a catalog search expects.

The project uses MovieLens 25M data to build a local movie discovery experience with semantic search, keyword search, content similarity, lightweight personalization, and optional TMDB enrichment. It is structured as a product case study: the notebooks show the data and modeling progression, while the Streamlit app demonstrates the final user-facing workflow.

The core product question is simple: how far can a movie discovery experience get by understanding user intent before it has enough behavioral history for traditional recommendations?

## Product Problem

Movie discovery breaks down in three familiar moments:

- A user remembers a theme, mood, or premise, but not the title.
- A keyword search returns literal matches, but misses adjacent ideas.
- A new user has too little history for collaborative filtering to be useful.

This project targets that cold-start gap. Instead of starting with heavy personalization, it begins with intent capture: let the user search by meaning, find adjacent movies, like a few examples, and then build a simple preference profile from those signals.

## Solution Overview

The prototype supports four connected discovery jobs:

- Search by title, genre, tag, or natural-language theme.
- Compare lexical retrieval with semantic retrieval.
- Find similar movies from embedding similarity.
- Generate content-based recommendations from a user's liked movies.

The Streamlit app keeps the recommendation path intentionally lightweight and content-based. The Phase 4 notebook explores collaborative filtering and blended scoring, but the interactive app focuses on the path that works most reliably with sparse user input.

## What This Demonstrates

- Product framing: starts from a user problem rather than an algorithm.
- Prioritization: solves cold-start discovery first before adding heavier personalization.
- Technical fluency: compares BM25, TF-IDF, sentence embeddings, FAISS, SQLite, and DuckDB in a practical workflow.
- End-to-end execution: moves from raw data ingestion to generated artifacts to an interactive app.
- Tradeoff awareness: documents where the prototype is strong, where it is limited, and what would be needed before productionizing.

## Product And Technical Decisions

| Decision | Rationale | Tradeoff |
| --- | --- | --- |
| Use semantic search alongside keyword search | Users describe intent in varied language; exact keyword overlap is not enough. | Embeddings are less interpretable than lexical search and require generated artifacts. |
| Start personalization with content-based recommendations | Works with only a few likes, which fits the cold-start problem. | Can become narrower than collaborative recommendations when user history is rich. |
| Keep collaborative filtering in the notebook layer | Useful for experimentation and comparison without overstating app readiness. | The Streamlit app does not yet expose the blended recommender path. |
| Use local SQLite for user likes | Keeps the prototype easy to run without external services. | Not designed for multi-user production deployment. |
| Exclude datasets, checkpoints, and caches from git | Keeps the public repo lightweight and safe to share. | New users must rebuild artifacts locally before running the app. |
| Add optional TMDB enrichment | Improves browsing quality with posters, plots, ratings, release dates, and cast. | Requires an API key and depends on third-party availability. |

## System Overview

The project is organized as a four-phase pipeline:

| Phase | Focus | Output |
| --- | --- | --- |
| Phase 1 | Data sourcing and profiling | MovieLens data loaded and profiled with local database artifacts. |
| Phase 2 | Content-based similarity | TF-IDF features, sentence embeddings, and FAISS similarity index. |
| Phase 3 | Natural-language search | BM25 keyword search and semantic search comparison. |
| Phase 4 | Personalization | User preference vectors, collaborative filtering experiments, and evaluation notes. |

The app depends on generated local artifacts, especially:

```text
checkpoints/embeddings.npy
checkpoints/faiss_index.bin
checkpoints/movie_ids.csv
data/movielens/movies.csv
data/movielens/tags.csv
```

## Repository Guide

```text
.
|-- app.py                         # Streamlit app
|-- tmdb_helper.py                 # Optional TMDB poster/details lookup
|-- phase_1.ipynb                  # Data sourcing and profiling
|-- phase_2.ipynb                  # Content-based similarity
|-- phase_3.ipynb                  # Keyword and semantic search
|-- phase_4.ipynb                  # Personalization and CF experiments
|-- requirements.txt               # Main environment for the full project
|-- requirements_phase*.txt        # Smaller per-phase dependency files
|-- docs/
|   |-- QUICKSTART.md
|   |-- Movie_Recommendation_PRD_v1.0.docx
|   `-- Movie_Recommendation_TRD_v1.0.docx
|-- data/                          # Local datasets, not committed
|-- checkpoints/                   # Generated models/indexes, not committed
`-- results/                       # Generated reports, not committed
```

## Run Locally

Use Python 3.10 or newer.

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional: add a TMDB API key for posters and movie details.

```bash
cp .env.example .env
```

Then edit `.env`:

```bash
TMDB_API_KEY=your_key_here
```

The app still runs without TMDB. It will skip posters and extra movie details.

### Data And Generated Files

Large files are not committed to this repo. After cloning, download or regenerate them locally.

| Local path | Required? | How to get it |
| --- | --- | --- |
| `data/movielens/` | Required | Download MovieLens 25M from https://grouplens.org/datasets/movielens/25m/ and extract files such as `movies.csv`, `ratings.csv`, `tags.csv`, and `links.csv` into this folder. |
| `data/imdb/title.basics.tsv.gz` | Optional | Download from https://datasets.imdbws.com/title.basics.tsv.gz, or let Phase 1 try to download it. |
| `data/imdb/title.ratings.tsv.gz` | Optional | Download from https://datasets.imdbws.com/title.ratings.tsv.gz, or let Phase 1 try to download it. |
| `data/tmdb/tmdb_5000_movies.csv` | Optional | Download from the TMDB 5000 Movie Dataset on Kaggle and place it in `data/tmdb/`. |
| `data/tmdb/tmdb_5000_credits.csv` | Optional | Download from the same Kaggle dataset and place it in `data/tmdb/`. |
| `.env` | Optional | Copy `.env.example` and add a TMDB key for posters/details. |
| `checkpoints/` | Generated | Run the notebooks in order. This creates the DuckDB database, embeddings, FAISS index, movie ID mapping, and local SQLite state. |
| `results/` | Generated | Created by the notebooks for comparisons, evaluation notes, and sample outputs. |

Expected local layout after downloading MovieLens:

```text
data/
  movielens/
    movies.csv
    ratings.csv
    tags.csv
    links.csv
    genome-scores.csv
    genome-tags.csv
```

### Build The Artifacts

Run the notebooks in order:

```bash
jupyter notebook phase_1.ipynb
jupyter notebook phase_2.ipynb
jupyter notebook phase_3.ipynb
jupyter notebook phase_4.ipynb
```

### Start The App

```bash
streamlit run app.py
```

Streamlit usually opens the app at:

```text
http://localhost:8501
```

If required local data or checkpoints are missing, the app stops with a short list of the files it needs.

## Current Constraints And Next Iterations

This is a local prototype, not a production recommender service. The current implementation is strongest as a product and technical case study for intent-based discovery.

Current constraints:

- The app depends on generated artifacts that are too large to keep in git.
- MovieLens tags are useful, but they are not a substitute for full plot summaries or editorial metadata.
- The interactive recommendation path is content-based; collaborative filtering and blended scoring are explored in the Phase 4 notebook.
- TMDB enrichment is optional and depends on API availability and cache freshness.

Potential next iterations:

- Expose the blended recommendation strategy in the app once evaluation supports it.
- Add richer query understanding from plots, reviews, or editorial metadata.
- Add evaluation slices for theme search, title search, and cold-start recommendation quality.
- Package the artifact build process into a repeatable command-line workflow.
- Add a lightweight demo dataset so reviewers can run the app without downloading MovieLens 25M.

## Supporting Documents

- [Quickstart](docs/QUICKSTART.md)
- [Product requirements](docs/Movie_Recommendation_PRD_v1.0.docx)
- [Technical requirements](docs/Movie_Recommendation_TRD_v1.0.docx)

## License

MIT. See [LICENSE](LICENSE).
