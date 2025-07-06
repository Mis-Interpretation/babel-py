"""
Universal Content Parser and Chunker
Intelligently processes scraped content for vector database storage
"""

import re
import json
from typing import List, Dict, Any, Optional
import logging
from openai import OpenAI
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UniversalContentParser:
    def __init__(self, config_file: str = "RAG_components/scraping_config.json", openai_api_key: Optional[str] = None):
        """Initialize the content parser"""
        self.config = self._load_config(config_file)
        self.classification_config = self.config.get("content_classification", {})
        
        # Initialize OpenAI client for embeddings
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
        else:
            # Try multiple ways to get OpenAI API key
            api_key = None
            
            try:
                # Method 1: Try to import config module
                import sys
                import os
                
                # Add current directory and parent directory to Python path
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(current_dir)
                
                for path in [parent_dir, current_dir]:
                    if path not in sys.path:
                        sys.path.insert(0, path)
                
                # Try importing config
                from config import get_openai_api_key
                api_key = get_openai_api_key()
                
            except ImportError:
                # Method 2: Try direct environment variable access
                import os
                api_key = os.getenv("OPENAI_API_KEY")
                
            except Exception:
                # Method 3: Fallback to environment variable
                import os
                api_key = os.getenv("OPENAI_API_KEY")
            
            # Initialize OpenAI client if we have a valid key
            if api_key and api_key != "sk-your-actual-openai-api-key-here":
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized for embedding generation")
            else:
                logger.info("OpenAI API key not configured. Embeddings will be skipped (this is fine for TF-IDF pipeline)")
                self.openai_client = None
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def parse_documents(self, scraped_docs: List[Dict]) -> List[Dict]:
        """Parse and chunk a list of scraped documents"""
        parsed_docs = []
        
        for doc in scraped_docs:
            try:
                chunks = self.parse_single_document(doc)
                parsed_docs.extend(chunks)
                logger.info(f"✅ Parsed {doc['title']} into {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"❌ Error parsing {doc.get('title', 'Unknown')}: {e}")
        
        logger.info(f"Total parsed chunks: {len(parsed_docs)}")
        return parsed_docs
    
    def parse_single_document(self, doc: Dict) -> List[Dict]:
        """Parse a single document into chunks"""
        content_type = doc.get("content_type", "general")
        
        # Get chunking strategy for this content type
        chunk_config = self.classification_config.get(content_type, {})
        chunk_strategy = chunk_config.get("chunk_strategy", "topic_based")
        chunk_size = chunk_config.get("chunk_size", 1000)
        overlap = chunk_config.get("overlap", 150)
        
        # Clean and prepare content
        cleaned_content = self._clean_content(doc["text"])
        
        # Apply chunking strategy
        if chunk_strategy == "preserve_structure":
            chunks = self._chunk_preserve_structure(cleaned_content, chunk_size, overlap)
        elif chunk_strategy == "sequential_steps":
            chunks = self._chunk_sequential_steps(cleaned_content, chunk_size, overlap)
        elif chunk_strategy == "preserve_code_blocks":
            chunks = self._chunk_preserve_code_blocks(cleaned_content, doc.get("code_blocks", []), chunk_size, overlap)
        else:  # topic_based
            chunks = self._chunk_topic_based(cleaned_content, chunk_size, overlap)
        
        # Create chunk documents
        chunk_docs = []
        for i, chunk_text in enumerate(chunks):
            if len(chunk_text.strip()) < 50:  # Skip very short chunks
                continue
                
            chunk_doc = self._create_chunk_document(doc, chunk_text, i, len(chunks))
            chunk_docs.append(chunk_doc)
        
        return chunk_docs
    
    def _clean_content(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common navigation elements
        text = re.sub(r'(Home|Navigation|Menu|Search|Login|Register)', '', text, flags=re.IGNORECASE)
        
        # Clean up common documentation artifacts
        text = re.sub(r'Table of Contents?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Skip to (main )?content', '', text, flags=re.IGNORECASE)
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def _chunk_preserve_structure(self, content: str, chunk_size: int, overlap: int) -> List[str]:
        """Chunk content while preserving document structure (good for API docs)"""
        chunks = []
        
        # Split by major sections (headers, etc.)
        sections = re.split(r'\n(?=\w+:|\d+\.|\w+\s*\n)', content)
        
        current_chunk = ""
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # If adding this section would exceed chunk size, save current chunk
            if len(current_chunk) + len(section) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + "\n\n" + section
            else:
                current_chunk += "\n\n" + section if current_chunk else section
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _chunk_sequential_steps(self, content: str, chunk_size: int, overlap: int) -> List[str]:
        """Chunk content by sequential steps (good for tutorials)"""
        chunks = []
        
        # Split by step indicators
        step_patterns = [
            r'\n(?=Step\s+\d+)',
            r'\n(?=\d+\.\s)',
            r'\n(?=\w+\s+\d+:)',
            r'\n(?=##?\s)',  # Markdown headers
        ]
        
        sections = [content]
        for pattern in step_patterns:
            new_sections = []
            for section in sections:
                new_sections.extend(re.split(pattern, section))
            sections = new_sections
        
        current_chunk = ""
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            if len(current_chunk) + len(section) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # For sequential content, include more overlap to maintain context
                overlap_text = self._get_overlap_text(current_chunk, overlap * 2)
                current_chunk = overlap_text + "\n\n" + section
            else:
                current_chunk += "\n\n" + section if current_chunk else section
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _chunk_preserve_code_blocks(self, content: str, code_blocks: List[str], chunk_size: int, overlap: int) -> List[str]:
        """Chunk content while preserving code blocks intact"""
        chunks = []
        
        # First, identify code block positions in content
        code_positions = []
        for code in code_blocks:
            if code in content:
                start = content.find(code)
                end = start + len(code)
                code_positions.append((start, end, code))
        
        # Sort by position
        code_positions.sort()
        
        # Split content around code blocks
        sections = []
        last_end = 0
        
        for start, end, code in code_positions:
            # Add text before code block
            if start > last_end:
                sections.append(("text", content[last_end:start]))
            
            # Add code block
            sections.append(("code", code))
            last_end = end
        
        # Add remaining text
        if last_end < len(content):
            sections.append(("text", content[last_end:]))
        
        # Build chunks
        current_chunk = ""
        current_size = 0
        
        for section_type, section_content in sections:
            section_content = section_content.strip()
            if not section_content:
                continue
            
            section_size = len(section_content)
            
            # If this is a code block and it would exceed chunk size
            if section_type == "code" and current_size + section_size > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(current_chunk.strip())
                
                # Start new chunk with the code block
                current_chunk = section_content
                current_size = section_size
            elif current_size + section_size > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + "\n\n" + section_content
                current_size = len(current_chunk)
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + section_content
                else:
                    current_chunk = section_content
                current_size = len(current_chunk)
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _chunk_topic_based(self, content: str, chunk_size: int, overlap: int) -> List[str]:
        """Default chunking strategy based on topics/paragraphs"""
        chunks = []
        
        # Split by paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Add overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + "\n\n" + paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get overlap text from the end of a chunk"""
        if len(text) <= overlap_size:
            return text
        
        # Try to break at sentence boundary
        overlap_text = text[-overlap_size:]
        sentence_end = overlap_text.rfind('.')
        
        if sentence_end > overlap_size // 2:  # If we found a good break point
            return text[-(overlap_size - sentence_end):]
        
        return overlap_text
    
    def _create_chunk_document(self, original_doc: Dict, chunk_text: str, chunk_index: int, total_chunks: int) -> Dict:
        """Create a chunk document with metadata"""
        # Generate content hash for deduplication
        content_hash = hashlib.md5(chunk_text.encode()).hexdigest()
        
        # Create chunk ID
        chunk_id = f"{content_hash}_{chunk_index}"
        
        chunk_doc = {
            "id": chunk_id,
            "text": chunk_text,
            "metadata": {
                **original_doc.get("metadata", {}),
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "chunk_id": chunk_id,
                "content_hash": content_hash,
                "original_title": original_doc.get("title", ""),
                "original_url": original_doc.get("url", ""),
                "chunk_size": len(chunk_text),
                "has_code_in_chunk": bool(re.search(r'```|`[^`]+`|\bclass\b|\bdef\b|\bfunction\b', chunk_text))
            }
        }
        
        return chunk_doc
    
    def generate_embeddings(self, chunk_docs: List[Dict], batch_size: int = 100) -> List[Dict]:
        """Generate embeddings for chunk documents"""
        if not self.openai_client:
            logger.warning("OpenAI client not configured. Skipping embedding generation.")
            return chunk_docs
        
        logger.info(f"Generating embeddings for {len(chunk_docs)} chunks...")
        
        for i in range(0, len(chunk_docs), batch_size):
            batch = chunk_docs[i:i + batch_size]
            texts = [doc["text"] for doc in batch]
            
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=texts
                )
                
                for j, embedding_data in enumerate(response.data):
                    embedding = embedding_data.embedding
                    # Ensure embedding is exactly 1536 dimensions
                    if len(embedding) != 1536:
                        logger.warning(f"OpenAI embedding has {len(embedding)} dimensions, expected 1536. Padding/truncating...")
                        if len(embedding) < 1536:
                            # Pad with zeros
                            embedding = embedding + [0.0] * (1536 - len(embedding))
                        else:
                            # Truncate
                            embedding = embedding[:1536]
                    
                    batch[j]["embedding"] = embedding
                
                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(chunk_docs) + batch_size - 1)//batch_size}")
                
            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Generate fallback 1536-dimensional embeddings
                import random
                import math
                for doc in batch:
                    if "embedding" not in doc:
                        # Generate normalized random 1536-dimensional vector
                        vector = [random.gauss(0, 1) for _ in range(1536)]
                        magnitude = math.sqrt(sum(x*x for x in vector))
                        if magnitude > 0:
                            vector = [x/magnitude for x in vector]
                        doc["embedding"] = vector
                        logger.warning("Generated fallback random embedding due to API error")
        
        return chunk_docs

# Convenience function for the complete parsing pipeline
def parse_scraped_content(scraped_docs: List[Dict], generate_embeddings: bool = True) -> List[Dict]:
    """Complete parsing pipeline for scraped content"""
    parser = UniversalContentParser()
    
    # Parse and chunk documents
    chunk_docs = parser.parse_documents(scraped_docs)
    
    # Generate embeddings if requested
    if generate_embeddings:
        chunk_docs = parser.generate_embeddings(chunk_docs)
    
    return chunk_docs

if __name__ == "__main__":
    # Test the parser with sample data
    sample_doc = {
        "title": "Unity Rigidbody Component",
        "text": "The Rigidbody component allows a GameObject to be affected by physics. Step 1: Add a Rigidbody component. Step 2: Configure mass and drag. Example code: rigidbody.AddForce(Vector3.up * 10);",
        "content_type": "api_reference",
        "code_blocks": ["rigidbody.AddForce(Vector3.up * 10);"],
        "metadata": {"source": "unity", "url": "test"}
    }
    
    parser = UniversalContentParser()
    chunks = parser.parse_single_document(sample_doc)
    
    print(f"Generated {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}: {chunk['text'][:100]}...")
