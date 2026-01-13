<img width="679" height="176" alt="image" src="https://github.com/user-attachments/assets/ec26b303-bc72-4bd9-bc18-b7c2e6aea035" />

---

**See how the news is shaped - not just what’s reported.**

Apogee is an AI-powered **media literacy tool** that visualizes how news stories relate to one another. Instead of consuming headlines in a linear feed, users explore a **3D semantic map of the news**, revealing topic clusters, coverage patterns, and under-reported stories.

---
### Demo Video
[![DEMO VIDEO](https://img.youtube.com/vi/06CLf0SW0aU/0.jpg)](https://youtu.be/06CLf0SW0aU)

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/b3383b8f-789c-4b1f-9297-bb846b664e93" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/5f289599-d56a-45a7-8728-14c5d259d9ec" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/ac1242a0-5b82-4d93-bf14-03aebf4c8fe0" />

---

## Inspiration

Most people consume news as endless lists and timelines. This format strips away context, hides bias, and makes it difficult to understand how different outlets frame, or ignore, the same events.

News Constellation was built to **combat misinformation and propaganda by restoring context**, helping users think critically about what they read.

---

## How It Works

1. **Ingest live news articles** based on a user’s query
2. **Scrape full article text** from each source
3. **Convert articles into semantic embeddings** using a transformer model
4. **Build a similarity graph** where articles are connected by meaning
5. **Automatically cluster stories** into topics using graph community detection
6. **Visualize the result as an interactive 3D galaxy**
7. Store article vectors, metadata, and cluster context in **Moorcheh AI**
8. Send vector-linked context to **Google Gemini** for memory-backed chat history, RAG and 

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

### AI & Memory
* **Moorcheh AI** – vector memory, retrieval, RAG
* **Google Gemini API** – conversational reasoning

### Data Processing

* **Pandas** – data storage and preprocessing

---

## System Architecture

<img width="806" height="471" alt="image" src="https://github.com/user-attachments/assets/ac419e17-8fd8-4121-99ea-4c0175f44209" />
```
NewsAPI / GNews
        ↓
newspaper3k (scraping)
        ↓
Sentence Transformers (embeddings)
        ↓
Cosine Similarity
        ↓
NetworkX Graph + Louvain Clustering
        ↓
PyVis (3D Galaxy)
        ↓
Streamlit UI
        ↓
Moorcheh AI (vector memory + RAG)
        ↓
Gemini (context-aware chat & explanations)
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
