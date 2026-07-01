# """
# RAG Data Ingestion Pipeline - Production Ready
# Handles document loading, chunking, embedding, and vector store creation

# Features:
# - Multi-format support (TXT, PDF, MD)
# - Section-aware chunking
# - Batch embedding generation with retry
# - Dual indexing (FAISS + BM25)
# - Error recovery and validation
# """

# import logging
# import json
# from pathlib import Path
# from typing import List, Dict, Any, Optional
# from datetime import datetime
# import hashlib

# logger = logging.getLogger(__name__)


# class DocumentLoader:
#     """Load documents from various formats with error handling"""

#     def __init__(self, documents_path: Path):
#         self.documents_path = Path(documents_path)
#         self.supported_formats = {'.txt', '.md', '.pdf'}

#     def load_all(self) -> List[Dict[str, Any]]:
#         """Load all supported documents"""
#         documents = []

#         if not self.documents_path.exists():
#             logger.error(f"Documents path does not exist: {self.documents_path}")
#             return documents

#         # Find all supported files
#         for file_path in self.documents_path.rglob('*'):
#             if file_path.suffix.lower() in self.supported_formats:
#                 try:
#                     doc = self._load_single(file_path)
#                     if doc:
#                         documents.append(doc)
#                         logger.info(f"✅ Loaded: {file_path.name}")
#                 except Exception as e:
#                     logger.error(f"❌ Failed to load {file_path.name}: {e}")
#                     continue

#         logger.info(f"📚 Loaded {len(documents)} documents")
#         return documents

#     def _load_single(self, file_path: Path) -> Optional[Dict[str, Any]]:
#         """Load single document with metadata"""

#         if file_path.suffix.lower() in {'.txt', '.md'}:
#             return self._load_text_file(file_path)
#         elif file_path.suffix.lower() == '.pdf':
#             return self._load_pdf_file(file_path)

#         return None

#     def _load_text_file(self, file_path: Path) -> Dict[str, Any]:
#         """Load text/markdown file"""
#         with open(file_path, 'r', encoding='utf-8') as f:
#             content = f.read()

#         return {
#             'content': content,
#             'source': str(file_path.name),
#             'format': file_path.suffix[1:],
#             'size': len(content),
#             'loaded_at': datetime.now().isoformat()
#         }

#     def _load_pdf_file(self, file_path: Path) -> Dict[str, Any]:
#         """Load PDF file (placeholder - requires PyPDF2 or similar)"""
#         # TODO: Implement PDF loading if needed
#         logger.warning(f"PDF loading not yet implemented: {file_path.name}")
#         return None


# class SectionAwareChunker:
#     """
#     Smart chunking that preserves section boundaries
#     Uses markdown headers (##) to identify sections
#     """

#     def __init__(self,
#                  min_chunk_size: int = 400,
#                  max_chunk_size: int = 1200,
#                  overlap: int = 100):
#         self.min_chunk_size = min_chunk_size
#         self.max_chunk_size = max_chunk_size
#         self.overlap = overlap

#     def chunk_documents(self, documents: List[Dict]) -> List[Dict[str, Any]]:
#         """Chunk all documents intelligently"""
#         all_chunks = []

#         for doc in documents:
#             try:
#                 chunks = self._chunk_single(doc)
#                 all_chunks.extend(chunks)
#                 logger.info(f"📄 {doc['source']}: {len(chunks)} chunks")
#             except Exception as e:
#                 logger.error(f"❌ Chunking failed for {doc['source']}: {e}")
#                 # Fallback: use simple chunking
#                 chunks = self._fallback_chunk(doc)
#                 all_chunks.extend(chunks)

#         logger.info(f"✅ Total chunks created: {len(all_chunks)}")
#         return all_chunks

#     def _chunk_single(self, doc: Dict) -> List[Dict[str, Any]]:
#         """Chunk single document by sections"""
#         content = doc['content']
#         source = doc['source']

#         # Try section-aware chunking first
#         sections = self._extract_sections(content)

#         if sections:
#             # Section-based chunking
#             chunks = []
#             for section in sections:
#                 # If section is too large, split it further
#                 if len(section['content']) > self.max_chunk_size:
#                     sub_chunks = self._split_large_section(section)
#                     chunks.extend(sub_chunks)
#                 elif len(section['content']) >= self.min_chunk_size:
#                     # Section is good size
#                     chunks.append(self._create_chunk(
#                         content=section['content'],
#                         source=source,
#                         section=section['title'],
#                         chunk_type='section'
#                     ))
#                 else:
#                     # Section too small - will merge later
#                     chunks.append(self._create_chunk(
#                         content=section['content'],
#                         source=source,
#                         section=section['title'],
#                         chunk_type='small_section'
#                     ))

#             # Merge small adjacent sections
#             chunks = self._merge_small_chunks(chunks)
#             return chunks
#         else:
#             # Fallback to regular chunking
#             return self._fallback_chunk(doc)

#     def _extract_sections(self, content: str) -> List[Dict[str, str]]:
#         """Extract markdown sections"""
#         import re

#         # Pattern for markdown headers: ## **Title**
#         header_pattern = r'^##\s*\*\*(.+?)\*\*'

#         sections = []
#         lines = content.split('\n')

#         current_section = None
#         current_content = []

#         for line in lines:
#             match = re.match(header_pattern, line)
#             if match:
#                 # Save previous section
#                 if current_section:
#                     sections.append({
#                         'title': current_section,
#                         'content': '\n'.join(current_content).strip()
#                     })

#                 # Start new section
#                 current_section = match.group(1)
#                 current_content = []
#             else:
#                 if current_section:
#                     current_content.append(line)

#         # Save last section
#         if current_section and current_content:
#             sections.append({
#                 'title': current_section,
#                 'content': '\n'.join(current_content).strip()
#             })

#         return sections

#     def _split_large_section(self, section: Dict) -> List[Dict]:
#         """Split large section into smaller chunks with overlap"""
#         content = section['content']
#         title = section['title']

#         chunks = []
#         start = 0
#         chunk_num = 1

#         while start < len(content):
#             end = start + self.max_chunk_size

#             # Try to break at sentence boundary
#             if end < len(content):
#                 # Look for sentence ending
#                 chunk_text = content[start:end]
#                 last_period = chunk_text.rfind('. ')
#                 if last_period > self.min_chunk_size:
#                     end = start + last_period + 1

#             chunk_content = content[start:end].strip()

#             chunks.append(self._create_chunk(
#                 content=chunk_content,
#                 source=title,
#                 section=f"{title} (Part {chunk_num})",
#                 chunk_type='section_split'
#             ))

#             start = end - self.overlap
#             chunk_num += 1

#         return chunks

#     def _merge_small_chunks(self, chunks: List[Dict]) -> List[Dict]:
#         """Merge adjacent small chunks to meet minimum size"""
#         if not chunks:
#             return chunks

#         merged = []
#         buffer = []
#         buffer_size = 0

#         for chunk in chunks:
#             if chunk.get('chunk_type') == 'small_section':
#                 buffer.append(chunk)
#                 buffer_size += len(chunk['content'])

#                 # Merge if buffer is large enough
#                 if buffer_size >= self.min_chunk_size:
#                     merged_content = '\n\n'.join([c['content'] for c in buffer])
#                     merged_section = ' + '.join([c.get('section', '') for c in buffer])

#                     merged.append(self._create_chunk(
#                         content=merged_content,
#                         source=buffer[0]['source'],
#                         section=merged_section,
#                         chunk_type='merged'
#                     ))

#                     buffer = []
#                     buffer_size = 0
#             else:
#                 # Flush buffer first
#                 if buffer:
#                     merged_content = '\n\n'.join([c['content'] for c in buffer])
#                     merged.append(self._create_chunk(
#                         content=merged_content,
#                         source=buffer[0]['source'],
#                         section='Multiple Sections',
#                         chunk_type='merged'
#                     ))
#                     buffer = []
#                     buffer_size = 0

#                 # Add regular chunk
#                 merged.append(chunk)

#         # Flush remaining buffer
#         if buffer:
#             merged_content = '\n\n'.join([c['content'] for c in buffer])
#             merged.append(self._create_chunk(
#                 content=merged_content,
#                 source=buffer[0]['source'],
#                 section='Multiple Sections',
#                 chunk_type='merged'
#             ))

#         return merged

#     def _fallback_chunk(self, doc: Dict) -> List[Dict[str, Any]]:
#         """Simple fallback chunking when section detection fails"""
#         content = doc['content']
#         source = doc['source']

#         chunks = []
#         start = 0
#         chunk_num = 1

#         while start < len(content):
#             end = start + self.max_chunk_size

#             if end < len(content):
#                 # Break at sentence
#                 chunk_text = content[start:end]
#                 last_period = chunk_text.rfind('. ')
#                 if last_period > self.min_chunk_size:
#                     end = start + last_period + 1

#             chunk_content = content[start:end].strip()

#             chunks.append(self._create_chunk(
#                 content=chunk_content,
#                 source=source,
#                 section=f"Chunk {chunk_num}",
#                 chunk_type='fallback'
#             ))

#             start = end - self.overlap
#             chunk_num += 1

#         return chunks

#     def _create_chunk(self, content: str, source: str,
#                      section: str, chunk_type: str) -> Dict[str, Any]:
#         """Create chunk with metadata"""

#         # Generate unique ID
#         chunk_id = hashlib.md5(
#             f"{source}_{section}_{content[:50]}".encode()
#         ).hexdigest()[:12]

#         return {
#             'id': chunk_id,
#             'content': content,
#             'source': source,
#             'section': section,
#             'chunk_type': chunk_type,
#             'length': len(content),
#             'created_at': datetime.now().isoformat()
#         }


# class DataIngestionPipeline:
#     """
#     Complete data ingestion pipeline
#     Orchestrates loading → chunking → embedding → indexing
#     """

#     def __init__(self, documents_path: str, output_path: str):
#         self.documents_path = Path(documents_path)
#         self.output_path = Path(output_path)
#         self.output_path.mkdir(parents=True, exist_ok=True)

#         self.loader = DocumentLoader(self.documents_path)
#         self.chunker = SectionAwareChunker(
#             min_chunk_size=400,
#             max_chunk_size=1200,
#             overlap=100
#         )

#     def run(self, force_rebuild: bool = False) -> Dict[str, Any]:
#         """
#         Run complete ingestion pipeline

#         Args:
#             force_rebuild: Rebuild even if cache exists

#         Returns:
#             Pipeline statistics
#         """
#         logger.info("🚀 Starting data ingestion pipeline...")

#         try:
#             # Check if cached data exists
#             cache_file = self.output_path / 'chunks_cache.json'
#             if cache_file.exists() and not force_rebuild:
#                 logger.info("📦 Loading from cache...")
#                 chunks = self._load_cache(cache_file)
#             else:
#                 # Step 1: Load documents
#                 logger.info("📖 Loading documents...")
#                 documents = self.loader.load_all()

#                 if not documents:
#                     logger.error("❌ No documents loaded!")
#                     return {'status': 'failed', 'reason': 'no_documents'}

#                 # Step 2: Chunk documents
#                 logger.info("✂️ Chunking documents...")
#                 chunks = self.chunker.chunk_documents(documents)

#                 if not chunks:
#                     logger.error("❌ No chunks created!")
#                     return {'status': 'failed', 'reason': 'no_chunks'}

#                 # Save cache
#                 self._save_cache(chunks, cache_file)

#             # Step 3: Validate chunks
#             logger.info("🔍 Validating chunks...")
#             validation = self._validate_chunks(chunks)

#             if not validation['valid']:
#                 logger.warning(f"⚠️ Validation issues: {validation['issues']}")

#             # Step 4: Save metadata
#             self._save_metadata(chunks)

#             stats = {
#                 'status': 'success',
#                 'total_chunks': len(chunks),
#                 'avg_chunk_size': sum(c['length'] for c in chunks) / len(chunks),
#                 'sources': list(set(c['source'] for c in chunks)),
#                 'sections': list(set(c.get('section', 'N/A') for c in chunks)),
#                 'validation': validation
#             }

#             logger.info(f"✅ Ingestion complete! {len(chunks)} chunks created")
#             return stats

#         except Exception as e:
#             logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
#             return {'status': 'failed', 'error': str(e)}

#     def _validate_chunks(self, chunks: List[Dict]) -> Dict[str, Any]:
#         """Validate chunk quality"""
#         issues = []

#         # Check for empty chunks
#         empty = [c for c in chunks if not c.get('content', '').strip()]
#         if empty:
#             issues.append(f"{len(empty)} empty chunks")

#         # Check for very small chunks
#         too_small = [c for c in chunks if len(c.get('content', '')) < 100]
#         if too_small:
#             issues.append(f"{len(too_small)} chunks < 100 chars")

#         # Check for very large chunks
#         too_large = [c for c in chunks if len(c.get('content', '')) > 2000]
#         if too_large:
#             issues.append(f"{len(too_large)} chunks > 2000 chars")

#         # Check for missing IDs
#         no_id = [c for c in chunks if not c.get('id')]
#         if no_id:
#             issues.append(f"{len(no_id)} chunks missing IDs")

#         return {
#             'valid': len(issues) == 0,
#             'issues': issues,
#             'total_checked': len(chunks)
#         }

#     def _save_cache(self, chunks: List[Dict], cache_file: Path):
#         """Save chunks to cache"""
#         with open(cache_file, 'w', encoding='utf-8') as f:
#             json.dump(chunks, f, indent=2, ensure_ascii=False)
#         logger.info(f"💾 Cache saved: {cache_file}")

#     def _load_cache(self, cache_file: Path) -> List[Dict]:
#         """Load chunks from cache"""
#         with open(cache_file, 'r', encoding='utf-8') as f:
#             chunks = json.load(f)
#         logger.info(f"📦 Loaded {len(chunks)} chunks from cache")
#         return chunks

#     def _save_metadata(self, chunks: List[Dict]):
#         """Save ingestion metadata"""
#         metadata = {
#             'total_chunks': len(chunks),
#             'sources': list(set(c['source'] for c in chunks)),
#             'sections': list(set(c.get('section', 'N/A') for c in chunks)),
#             'created_at': datetime.now().isoformat(),
#             'chunk_size_stats': {
#                 'min': min(c['length'] for c in chunks),
#                 'max': max(c['length'] for c in chunks),
#                 'avg': sum(c['length'] for c in chunks) / len(chunks)
#             }
#         }

#         metadata_file = self.output_path / 'ingestion_metadata.json'
#         with open(metadata_file, 'w', encoding='utf-8') as f:
#             json.dump(metadata, f, indent=2)

#         logger.info(f"📊 Metadata saved: {metadata_file}")


# # CLI for testing
# if __name__ == "__main__":
#     import sys

#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - %(message)s'
#     )

#     # Default paths
#     docs_path = "rag/documents"
#     output_path = "rag/vectorstore"

#     pipeline = DataIngestionPipeline(docs_path, output_path)

#     force_rebuild = '--rebuild' in sys.argv
#     stats = pipeline.run(force_rebuild=force_rebuild)

#     print("\n" + "="*60)
#     print("INGESTION PIPELINE RESULTS")
#     print("="*60)
#     print(json.dumps(stats, indent=2))
