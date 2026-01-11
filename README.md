<img width="679" height="176" alt="image" src="https://github.com/user-attachments/assets/ec26b303-bc72-4bd9-bc18-b7c2e6aea035" />

---

**See how the news is shaped - not just what’s reported.**

News Constellation is an AI-powered **media literacy tool** that visualizes how news stories relate to one another. Instead of consuming headlines in a linear feed, users explore a **3D semantic map of the news**, revealing topic clusters, coverage patterns, and under-reported stories.

---

## Inspiration

Most people consume news as endless lists and timelines. This format strips away context, hides bias, and makes it difficult to understand how different outlets frame — or ignore — the same events.

News Constellation was built to **combat misinformation and propaganda by restoring context**, helping users think critically about what they read.

---

## How It Works

1. **Ingest live news articles** based on a user’s query
2. **Scrape full article text** from each source
3. **Convert articles into semantic embeddings** using a transformer model
4. **Build a similarity graph** where articles are connected by meaning
5. **Automatically cluster stories** into topics using graph community detection
6. **Visualize the result as an interactive 3D galaxy**

Each cluster represents a topic, and each node represents an article — making coverage patterns immediately visible.

---

## Tech Stack

### Core Language

* **Python 3.9+**

### Data Ingestion

* **NewsAPI / GNews** – fetch live news articles
* **newspaper3k** – extract full article text from URLs

### NLP & Machine Learning

* **Sentence-Transformers** (`all-MiniLM-L6-v2`) – generate semantic embeddings
* **scikit-learn** – cosine similarity calculations

### Graph & Clustering

* **NetworkX** – graph construction and analysis
* **Louvain Community Detection** – unsupervised topic clustering

### Visualization & UI

* **PyVis** – interactive 3D network visualization
* **Streamlit** – UI wrapper for search and interaction

### Data Processing

* **Pandas** – data storage and preprocessing

---

## System Architecture

```
NewsAPI / GNews
        ↓
newspaper3k (scraping)
        ↓
Sentence Transformers (embeddings)
        ↓
Cosine Similarity
        ↓
NetworkX Graph
        ↓
Louvain Clustering
        ↓
PyVis (3D visualization)
        ↓
Streamlit UI
```

---

## Why This Matters

* Reveals **bias and framing** across media outlets
* Highlights **under-covered or fragmented stories**
* Encourages **critical thinking and media literacy**
* Moves beyond keyword matching to **semantic understanding**

## Getting Started

### Installation

```bash
git clone https://github.com/CaellumYHL/DeltaHacks2026.git
cd DeltaHacks2026
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```
