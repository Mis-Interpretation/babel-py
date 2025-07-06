# Simple Usage Guide - Unity Vector Database

## 🎯 What This Does

This tool scrapes Unity documentation and puts it into a Pinecone vector database so you can search it later. **No OpenAI required** - it uses simple TF-IDF embeddings.

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Pinecone API Key
- Sign up at [pinecone.io](https://pinecone.io)
- Get your API key from the dashboard

### 3. Set Environment Variable
```bash
# Windows
set PINECONE_API_KEY=your-pinecone-api-key-here

# Mac/Linux
export PINECONE_API_KEY=your-pinecone-api-key-here
```

## 📝 How to Use

### Method 1: Simple Command Line
```bash
python populate_vector_db.py
```

### Method 2: Call from Python
```python
from populate_vector_db import populate_unity_vector_db

# Populate your vector database
result = populate_unity_vector_db(
    pinecone_api_key="your-pinecone-api-key",
    max_pages=50,  # Start small for testing
    clear_existing=True  # Clear old data
)

print(result)
```

### Method 3: Environment Variable
```python
from populate_vector_db import quick_populate

# Uses PINECONE_API_KEY environment variable
result = quick_populate()
```

## 🔍 What Happens

1. **Scrapes Unity Docs** - Downloads Unity documentation pages
2. **Chunks Content** - Breaks content into searchable pieces
3. **Creates Embeddings** - Uses TF-IDF (no OpenAI needed)
4. **Uploads to Pinecone** - Stores in your vector database

## 📊 Example Output

```
🚀 Starting Unity documentation scraping and indexing...
📋 Initializing scraper and database components...
🕷️ Scraping Unity documentation (max 50 pages)...
✅ Successfully scraped 45 documents
📝 Parsing and chunking content...
✅ Created 127 content chunks
🔢 Generating simple embeddings...
   ✅ Generated 127 TF-IDF embeddings
☁️ Uploading to Pinecone vector database...
🎉 Vector database population completed!
📊 Results: 45 docs → 127 chunks → 127 vectors
```

## ⚙️ Configuration Options

```python
populate_unity_vector_db(
    pinecone_api_key="your-key",
    max_pages=100,           # How many pages to scrape
    index_name="my-unity-kb", # Pinecone index name
    clear_existing=False,     # Keep existing data
    namespace="unity-2023"    # Organize data by namespace
)
```

## 🎮 For Copilot

Once populated, we can search the vector database:

```python
from RAG_components.pinecone_manager import PineconeManager

# Connect to the populated database
pm = PineconeManager(api_key="your-pinecone-api-key")

# Search by metadata (no embeddings needed for basic search)
results = pm.search_by_metadata(
    filter_dict={"content_type": "api_reference"},
    top_k=10
)

# Or use the full retriever (requires OpenAI for query embeddings)
from RAG_components.knowledge_retriever import UnityKnowledgeRetriever
retriever = UnityKnowledgeRetriever(pinecone_api_key="your-key", openai_api_key="your-openai-key")
results = retriever.search_unity_knowledge("rigidbody physics")
```

## 🔧 Troubleshooting

### "No documents scraped"
- Check internet connection
- Unity docs might be temporarily unavailable
- Try reducing `max_pages` to 10 for testing

### "ImportError: sklearn"
```bash
pip install scikit-learn
```

### "Pinecone connection failed"
- Check your API key is correct
- Make sure you have Pinecone credits/free tier available

### "Random embeddings" message
- This is normal if scikit-learn isn't installed
- Install scikit-learn for proper TF-IDF embeddings

## 📈 Scaling Up

Start small and scale up:

1. **Test**: `max_pages=10`
2. **Small**: `max_pages=50` 
3. **Medium**: `max_pages=200`
4. **Full**: `max_pages=None` (scrapes everything)

## 🎯 Next Steps

1. Run the population script
2. Check your Pinecone dashboard to see the vectors
3. Your friend can integrate the search functions into their copilot
4. Add more game engines by editing `RAG_components/scraping_config.json`

That's it! You now have a searchable Unity knowledge base in Pinecone.
