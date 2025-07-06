# Unity Knowledge Base RAG Pipeline

A modular, scalable pipeline for scraping Unity documentation and building a vector database knowledge base using Pinecone. Designed for building AI copilots for game development.

## 🎯 Overview

This pipeline transforms Unity documentation into a searchable knowledge base that can power AI assistants, chatbots, and copilots for game developers. It's built with modularity in mind, making it easy to extend to other game engines like Unreal Engine or Godot.

## 🏗️ Architecture

```
Unity Docs → Generic Scraper → Content Parser → Pinecone Vector DB → Knowledge Retriever → Your Copilot
```

### Core Components

1. **Generic Web Scraper** - Configurable scraper for any documentation site
2. **Universal Content Parser** - Intelligent chunking and content classification
3. **Pinecone Manager** - Vector database operations and management
4. **Knowledge Retriever** - Clean API for querying the knowledge base
5. **Unity Pipeline** - Orchestrates the complete workflow

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Set up your API keys as environment variables:

```bash
# Required API keys
export PINECONE_API_KEY="your-pinecone-api-key"
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. Basic Usage

```python
from RAG_components import scrape_and_index_unity, search_unity_knowledge

# Populate the knowledge base
result = scrape_and_index_unity(max_pages=50)

# Search the knowledge base
results = search_unity_knowledge("How to create a rigidbody?")
print(results)
```

### 4. Integration with Your Friend's System

Your friend can use these simple functions in their copilot:

```python
from RAG_components import search_unity_knowledge, get_unity_code_examples

# Main search function
def get_unity_help(user_question):
    results = search_unity_knowledge(user_question, max_results=5)
    return results['results']

# Get code examples
def get_code_help(api_name):
    examples = get_unity_code_examples(api_name, max_results=3)
    return examples['results']
```

## 📚 Detailed Usage

### Advanced Pipeline Usage

```python
from RAG_components import UnityKnowledgePipeline

# Create pipeline instance
pipeline = UnityKnowledgePipeline()

# Health check
health = pipeline.health_check()
print(f"System status: {health['status']}")

# Scrape and index with custom settings
result = pipeline.scrape_and_index(
    source="unity",
    max_pages=100,
    namespace="unity-2023",
    clear_existing=False
)

# Advanced search with filters
results = pipeline.search_knowledge(
    query="physics simulation",
    max_results=10,
    content_type="api_reference"
)

# Get contextual documentation
contextual_results = pipeline.retriever.get_contextual_docs(
    query="rigidbody movement",
    context_type="beginner",  # or "programmer", "artist", "designer"
    max_results=5
)
```

### Search Functions Available

```python
# Main search function
search_unity_knowledge(query, max_results=5, content_type=None)

# Get code examples for specific APIs
get_unity_code_examples(api_name, max_results=3)

# Find related concepts and workflows
get_related_concepts(topic, max_results=5)

# Search by category
pipeline.retriever.search_by_category(query, category="physics")

# Contextual search for different user types
pipeline.retriever.get_contextual_docs(query, context_type="beginner")
```

## 🔧 Configuration

### Scraping Configuration

Edit `RAG_components/scraping_config.json` to add new documentation sources:

```json
{
  "unity": {
    "name": "Unity Documentation",
    "base_urls": [
      "https://docs.unity3d.com/ScriptReference/",
      "https://docs.unity3d.com/Manual/"
    ],
    "discovery_patterns": ["/ScriptReference/", "/Manual/"],
    "exclude_patterns": [".pdf", "#", "?"],
    "metadata": {
      "source": "unity",
      "engine": "unity3d",
      "version": "2023.3"
    }
  }
}
```

### Content Classification

The system automatically classifies content into types:

- **api_reference** - API documentation and class references
- **tutorial** - Step-by-step tutorials and guides
- **guide** - General documentation and overviews
- **code_example** - Code samples and examples

### Chunking Strategies

Different content types use optimized chunking strategies:

- **preserve_structure** - For API docs (maintains class/method structure)
- **sequential_steps** - For tutorials (keeps steps together)
- **preserve_code_blocks** - For code examples (keeps code intact)
- **topic_based** - For general content (paragraph-based)

## 📊 Monitoring and Management

### Health Checks

```python
from RAG_components import health_check

# Check system health
health = health_check()
print(health)
```

### Pipeline Statistics

```python
pipeline = UnityKnowledgePipeline()
stats = pipeline.get_pipeline_stats()
print(f"Total vectors: {stats['index_stats']['total_vector_count']}")
```

### Index Management

```python
# Clear namespace
pipeline.pinecone_manager.clear_namespace("unity-old")

# Get index statistics
stats = pipeline.pinecone_manager.get_index_stats()

# Delete specific documents
pipeline.pinecone_manager.delete_documents(["doc_id_1", "doc_id_2"])
```

## 🔄 Updating the Knowledge Base

### Manual Updates

```python
# Update with new content
result = pipeline.update_knowledge_base("unity", max_pages=50)
```

### Adding New Sources

```python
# Add Unreal Engine documentation
unreal_config = {
    "name": "Unreal Engine Documentation",
    "base_urls": ["https://docs.unrealengine.com/5.3/en-US/"],
    "discovery_patterns": ["/en-US/API/", "/en-US/BlueprintAPI/"],
    "metadata": {"source": "unreal", "engine": "unreal_engine"}
}

pipeline.add_new_source(unreal_config, "unreal")
```

## 🎮 Multi-Engine Support

The pipeline is designed to support multiple game engines:

```python
# Scrape Unity documentation
unity_result = pipeline.scrape_and_index("unity", namespace="unity")

# Scrape Unreal documentation (when configured)
unreal_result = pipeline.scrape_and_index("unreal", namespace="unreal")

# Search across all engines
all_results = pipeline.search_knowledge("physics simulation")

# Search specific engine
unity_results = pipeline.search_knowledge("physics", source="unity")
```

## 📁 File Structure

```
RAG_components/
├── __init__.py                 # Package initialization
├── scraping_config.json        # Configuration for documentation sources
├── generic_scraper.py          # Configurable web scraper
├── content_parser.py           # Content parsing and chunking
├── pinecone_manager.py         # Pinecone vector database operations
├── knowledge_retriever.py      # Query interface for the knowledge base
└── unity_pipeline.py           # Main pipeline orchestrator

example_usage.py                # Example usage script
README_RAG_Pipeline.md          # This documentation
requirements.txt                # Python dependencies
```

## 🔍 Search Result Format

All search functions return results in this format:

```python
{
    "query": "user query",
    "results": [
        {
            "content": "relevant content preview...",
            "source_url": "https://docs.unity3d.com/...",
            "title": "Document Title",
            "relevance_score": 0.95,
            "content_type": "api_reference",
            "has_code_example": true,
            "source": "unity",
            "chunk_info": {
                "chunk_index": 0,
                "total_chunks": 3
            }
        }
    ],
    "total_results": 5,
    "status": "success"
}
```

## 🚨 Error Handling

The pipeline includes comprehensive error handling:

```python
result = search_unity_knowledge("query")
if result['status'] == 'error':
    print(f"Search failed: {result['error']}")
else:
    print(f"Found {result['total_results']} results")
```

## 🔧 Troubleshooting

### Common Issues

1. **API Key Errors**
   ```bash
   # Check if keys are set
   echo $PINECONE_API_KEY
   echo $OPENAI_API_KEY
   ```

2. **Import Errors**
   ```bash
   # Install missing dependencies
   pip install -r requirements.txt
   ```

3. **Pinecone Connection Issues**
   ```python
   # Test Pinecone connection
   from RAG_components import health_check
   print(health_check())
   ```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎯 Performance Optimization

### Batch Processing

The pipeline automatically handles batch processing for:
- Embedding generation (100 texts per batch)
- Pinecone uploads (100 vectors per batch)
- Rate limiting (configurable delays)

### Memory Management

For large documentation sets:
- Process in smaller chunks using `max_pages` parameter
- Use namespaces to organize content
- Monitor index usage with `get_index_stats()`

## 🤝 Integration Examples

### For Your Friend's Copilot System

```python
# Simple integration
from RAG_components import search_unity_knowledge

def answer_unity_question(user_question):
    """Main function for your friend's copilot"""
    results = search_unity_knowledge(user_question, max_results=3)
    
    if results['status'] == 'success' and results['total_results'] > 0:
        # Return the most relevant result
        best_result = results['results'][0]
        return {
            'answer': best_result['content'],
            'source': best_result['source_url'],
            'confidence': best_result['relevance_score']
        }
    else:
        return {'answer': 'No relevant documentation found', 'source': None}
```

### Advanced Integration

```python
from RAG_components import UnityKnowledgePipeline

class UnityCopilot:
    def __init__(self):
        self.pipeline = UnityKnowledgePipeline()
    
    def get_help(self, question, user_type="programmer"):
        """Get contextual help based on user type"""
        results = self.pipeline.retriever.get_contextual_docs(
            query=question,
            context_type=user_type,
            max_results=5
        )
        return self._format_response(results)
    
    def get_code_help(self, api_name):
        """Get code examples for Unity APIs"""
        return self.pipeline.get_code_examples(api_name)
    
    def _format_response(self, results):
        """Format results for the copilot UI"""
        # Your formatting logic here
        pass
```

## 📈 Future Enhancements

- **Change Detection**: Automatically detect when documentation is updated
- **Multi-language Support**: Support for documentation in different languages
- **Visual Content**: Extract and index images, diagrams, and videos
- **Community Content**: Include Unity forums, tutorials, and community guides
- **Performance Analytics**: Track query patterns and optimize retrieval

## 📄 License

This pipeline is designed for building Unity copilots and can be extended for other game engines. Make sure to respect the terms of service of the documentation sites you scrape.

---

**Ready to build your Unity copilot?** Start with the example script and customize the pipeline for your specific needs!
