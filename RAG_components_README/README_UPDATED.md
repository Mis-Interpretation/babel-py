# Unity RAG Pipeline - Complete Solution

A production-ready scraper-to-Pinecone pipeline for building a Unity knowledge base for your game engine copilot.

## 🎯 What This Does

- **Scrapes Unity Documentation**: Automatically crawls Unity's official docs
- **Processes Content**: Parses, chunks, and cleans the content
- **Generates Embeddings**: Creates 1536-dimensional vectors for semantic search
- **Stores in Pinecone**: Uploads to your vector database with proper metadata
- **Provides Search Interface**: Clean API for querying the knowledge base

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Edit your `.env` file:
```
PINECONE_API_KEY=your-pinecone-api-key-here
OPENAI_API_KEY=your-openai-api-key-here  # Optional, for advanced features
```

### 3. Run the Pipeline
```bash
python run_rag_pipeline.py
```

This launches an interactive menu with options to:
- Test all fixes
- Populate your database
- Search the knowledge base
- Run complete fix and repopulation

## 📁 Project Structure

```
babel-py/
├── RAG_components/                    # All RAG-related code
│   ├── html_scraper.py               # Web scraping logic
│   ├── generic_scraper.py            # Universal scraper
│   ├── content_parser.py             # Content processing
│   ├── pinecone_manager.py           # Vector database management
│   ├── knowledge_retriever.py        # Search interface
│   ├── unity_pipeline.py             # Complete pipeline
│   ├── populate_vector_db.py         # Database population
│   ├── simple_usage_example.py       # Basic usage
│   ├── fix_and_repopulate_database.py # Complete fix script
│   ├── test_fixes.py                 # Validation tests
│   └── scraping_config.json          # Scraping configuration
├── run_rag_pipeline.py               # Main launcher script
├── config.py                         # Configuration management
├── .env                              # API keys (create this)
└── requirements.txt                  # Dependencies
```

## 🔧 Key Features

### ✅ **All Critical Issues Fixed**

1. **Vector Dimensions**: Always generates exactly 1536 dimensions
2. **Text Content Storage**: Stores actual content, not just metadata
3. **UTF-8 Encoding**: Handles international characters properly
4. **Error Handling**: Robust error recovery and reporting

### 🎮 **Unity-Specific Optimizations**

- **Content Classification**: API references, tutorials, guides, code examples
- **Smart Chunking**: Preserves code blocks and maintains context
- **Metadata Enrichment**: Stores titles, URLs, content types, and more
- **Deduplication**: Prevents duplicate content using content hashes

### 🔍 **Advanced Search Capabilities**

- **Semantic Search**: Find content by meaning, not just keywords
- **Filtered Search**: Search by content type, category, or source
- **Code Examples**: Specifically find code snippets for Unity APIs
- **Contextual Results**: Get beginner, intermediate, or advanced content

## 📊 Usage Examples

### Basic Population
```python
from RAG_components.populate_vector_db import populate_unity_vector_db_auto

result = populate_unity_vector_db_auto(
    max_pages=50,           # Number of pages to scrape
    clear_existing=True,    # Clear old data
    namespace=""            # Pinecone namespace
)
```

### Search Knowledge Base
```python
from RAG_components.knowledge_retriever import UnityKnowledgeRetriever

retriever = UnityKnowledgeRetriever()
results = retriever.search_unity_knowledge(
    query="How to create a rigidbody?",
    max_results=5,
    content_type="tutorial"  # Optional filter
)
```

### Get Code Examples
```python
code_results = retriever.get_code_examples(
    api_name="Rigidbody",
    max_results=3
)
```

## 🛠️ Troubleshooting

### Common Issues

1. **"Pinecone API key not configured"**
   - Add your API key to `.env` file
   - Get key from: https://pinecone.io

2. **"Vector dimension mismatch"**
   - Run: `python run_rag_pipeline.py` → Option 1 (Test fixes)
   - If tests fail, the dimension fix isn't working

3. **"No text content in results"**
   - Run: `python run_rag_pipeline.py` → Option 3 (Complete fix)
   - This clears corrupted data and repopulates

### Validation Commands

```bash
# Test all fixes
python -m RAG_components.test_fixes

# Complete database refresh
python -m RAG_components.fix_and_repopulate_database

# Simple population
python -m RAG_components.simple_usage_example
```

## 🎯 For Your Unity Copilot

This pipeline creates a production-ready knowledge base that your Unity copilot can use to:

- **Answer Unity Questions**: Semantic search finds relevant documentation
- **Provide Code Examples**: Retrieve actual Unity code snippets
- **Explain Concepts**: Get detailed explanations with proper context
- **Guide Workflows**: Find step-by-step tutorials and guides

### Integration Example
```python
# In your copilot code
from RAG_components.knowledge_retriever import UnityKnowledgeRetriever

retriever = UnityKnowledgeRetriever()

def get_unity_help(user_question):
    results = retriever.search_unity_knowledge(user_question, max_results=3)
    
    if results['status'] == 'success':
        # Use results to enhance your copilot's response
        context = "\n".join([r['content'] for r in results['results']])
        return f"Based on Unity documentation: {context}"
    
    return "Sorry, I couldn't find relevant Unity documentation."
```

## 📈 Scaling to Other Game Engines

The pipeline is designed to be extensible:

1. **Add New Sources**: Update `scraping_config.json`
2. **Custom Parsers**: Extend `UniversalContentParser`
3. **Multiple Indexes**: Use different Pinecone namespaces
4. **Engine-Specific Logic**: Add new scrapers in `RAG_components/`

## 🤝 Contributing

1. All RAG components are in `RAG_components/` folder
2. Use relative imports within the folder
3. Test changes with `python run_rag_pipeline.py`
4. Update this README for new features

## 📝 License

See LICENSE file for details.

---

**Ready to build your Unity copilot? Start with `python run_rag_pipeline.py`!** 🚀
