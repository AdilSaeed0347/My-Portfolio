"""
Enhanced retriever with fixes for information extraction accuracy
"""
import numpy as np
import json
import logging
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path
import faiss
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

class UltraPreciseRetriever:
    """Enhanced retriever with improved accuracy for complete information extraction"""
    
    def __init__(self):
        self.embedding_model = None
        self.vector_index = None
        self.bm25_index = None
        self.documents = []
        self.tokenized_docs = []
        
        # Paths
        project_root = Path(__file__).parent.parent.parent
        self.documents_path = project_root / "rag" / "documents"
        self.vectorstore_path = project_root / "rag" / "vectorstore"
        
        self.vectorstore_path.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize with enhanced information capture"""
        try:
            logger.info("[INIT] Initializing enhanced retriever...")
            
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            await self._load_or_create_indexes()
            
            logger.info(f"[READY] Enhanced retriever ready with {len(self.documents)} chunks")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize retriever: {e}")
            raise

    async def _load_or_create_indexes(self):
        """Load or create indexes with data validation"""
        vector_file = self.vectorstore_path / "faiss.index"
        bm25_file = self.vectorstore_path / "bm25.json"
        metadata_file = self.vectorstore_path / "documents.json"
        
        if await self._should_rebuild_indexes():
            logger.info("[REBUILD] Rebuilding indexes for complete data capture...")
            await self._create_new_indexes(vector_file, bm25_file, metadata_file)
            return
        
        if all(f.exists() for f in [vector_file, bm25_file, metadata_file]):
            try:
                await self._load_existing_indexes(vector_file, bm25_file, metadata_file)
                
                # CRITICAL FIX: Validate that we have complete information
                if self._validate_information_completeness():
                    logger.info("[LOAD] Loaded complete indexes")
                    return
                else:
                    logger.warning("[INCOMPLETE] Existing indexes missing information, rebuilding...")
            except Exception as e:
                logger.warning(f"[WARN] Failed to load indexes: {e}. Creating new ones...")
        
        await self._create_new_indexes(vector_file, bm25_file, metadata_file)

    def _validate_information_completeness(self) -> bool:
        """CRITICAL FIX: Validate that all important information is captured"""
        
        if not self.documents:
            return False
        
        # Check for key information that should be present
        key_info_checks = {
            'imsciences_mentioned': False,
            'friends_details': False,
            'contact_info': False,
            'project_details': False,
            'giki_details': False
        }
        
        all_content = ' '.join([doc.get('content', '') for doc in self.documents]).lower()
        
        # Check IMSciences
        if 'imsciences' in all_content or 'institute of management sciences' in all_content:
            key_info_checks['imsciences_mentioned'] = True
        
        # Check friends with names
        friend_names = ['saad khan', 'rohail', 'daud khan', 'umer khan', 'hasnain']
        if any(name in all_content for name in friend_names):
            key_info_checks['friends_details'] = True
        
        # Check contact info
        if 'adilsaeed047@gmail.com' in all_content:
            key_info_checks['contact_info'] = True
        
        # Check project details
        if 'ocr' in all_content and 'sentiment analysis' in all_content:
            key_info_checks['project_details'] = True
        
        # Check GIKI details
        if 'giki' in all_content and 'bootcamp' in all_content:
            key_info_checks['giki_details'] = True
        
        # Require at least 4/5 key information types to be present
        passed_checks = sum(key_info_checks.values())
        is_complete = passed_checks >= 4
        
        if not is_complete:
            logger.warning(f"[INCOMPLETE] Only {passed_checks}/5 key information types found")
            
        return is_complete

    async def _should_rebuild_indexes(self) -> bool:
        """Check if indexes should be rebuilt"""
        adil_file = self.documents_path / "Adil.txt"
        metadata_file = self.vectorstore_path / "documents.json"
        
        if not adil_file.exists():
            return False
        
        if not metadata_file.exists():
            return True
        
        adil_mtime = adil_file.stat().st_mtime
        metadata_mtime = metadata_file.stat().st_mtime
        
        return adil_mtime > metadata_mtime

    async def _load_existing_indexes(self, vector_file: Path, bm25_file: Path, metadata_file: Path):
        """Load existing indexes"""
        self.vector_index = faiss.read_index(str(vector_file))
        
        with open(bm25_file, 'r', encoding='utf-8') as f:
            bm25_data = json.load(f)
            self.tokenized_docs = bm25_data['tokenized_docs']
            self.bm25_index = BM25Okapi(self.tokenized_docs)
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)

    async def _create_new_indexes(self, vector_file: Path, bm25_file: Path, metadata_file: Path):
        """Create new indexes with enhanced information capture"""
        try:
            logger.info("[CREATE] Creating indexes with complete information capture...")
            
            raw_documents = await self._load_documents()
            if not raw_documents:
                raise ValueError("No documents found")
            
            # CRITICAL FIX: Enhanced chunking to preserve complete information
            self.documents = await self._enhanced_information_chunking(raw_documents)
            if not self.documents:
                raise ValueError("No chunks created")
            
            await self._create_vector_index(vector_file)
            await self._create_bm25_index(bm25_file)
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Created complete indexes with {len(self.documents)} chunks")
            
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")
            raise

    async def _load_documents(self) -> List[Dict[str, Any]]:
        """Load documents with better processing"""
        documents = []
        
        for file_path in self.documents_path.rglob("*.txt"):
            if "adil" in file_path.name.lower():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if content:
                        content = self._clean_content(content)
                        
                        documents.append({
                            "source": file_path.name,
                            "content": content,
                            "file_path": str(file_path)
                        })
                        logger.info(f"📄 Loaded: {file_path.name}")
                
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load {file_path}: {e}")
        
        return documents

    def _clean_content(self, content: str) -> str:
        """Clean content while preserving important information"""
        # Remove excessive whitespace but preserve structure
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r' {2,}', ' ', content)
        
        # Fix formatting issues
        content = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', content)
        
        return content.strip()

    async def _enhanced_information_chunking(self, raw_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """CRITICAL FIX: Enhanced chunking to preserve ALL important information"""

        # STRATEGY: Create overlapping chunks that ensure no information is lost
        # IMPROVED: Larger chunks to preserve complete sections (social links, certifications)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,  # INCREASED: Better for preserving lists and multi-line sections
            chunk_overlap=150,  # INCREASED: Higher overlap to ensure continuity
            length_function=len,
            separators=["\n\n##", "\n\n", "\n", ". ", "! ", "? ", "; ", ": ", ", ", " "],  # ADDED: ## for markdown sections
            keep_separator=True,
            add_start_index=True
        )
        
        chunked_documents = []
        
        for doc in raw_documents:
            try:
                content = doc["content"]
                
                # CRITICAL: Also create section-based chunks for important sections
                sections = self._extract_important_sections(content)
                
                # Regular chunking
                regular_chunks = text_splitter.split_text(content)
                
                # Process regular chunks
                for i, chunk_content in enumerate(regular_chunks):
                    if chunk_content.strip() and len(chunk_content.strip()) > 15:
                        chunk = self._create_enhanced_chunk(chunk_content, doc["source"], i, "regular")
                        chunked_documents.append(chunk)
                
                # Process section-based chunks for complete information
                for section_name, section_content in sections.items():
                    if section_content.strip() and len(section_content.strip()) > 30:
                        chunk = self._create_enhanced_chunk(section_content, doc["source"], 
                                                          len(regular_chunks), f"section_{section_name}")
                        chunked_documents.append(chunk)
                        
            except Exception as e:
                logger.warning(f"⚠️ Failed to chunk {doc['source']}: {e}")
        
        # CRITICAL: Ensure key information is definitely captured
        chunked_documents = self._ensure_key_information_coverage(chunked_documents, raw_documents)
        
        logger.info(f"📊 Created {len(chunked_documents)} information-complete chunks")
        return chunked_documents

    def _extract_important_sections(self, content: str) -> Dict[str, str]:
        """Extract complete important sections"""
        sections = {}
        
        # Define section patterns
        section_patterns = {
            'contact': r'(## \*\*Contact Information\*\*.*?)(?=## |\*\*|$)',
            'education': r'(## \*\*Education\*\*.*?)(?=## |\*\*|$)',
            'projects': r'(## \*\*Projects Portfolio\*\*.*?)(?=## |\*\*|$)',
            'experience': r'(## \*\*Professional Experience\*\*.*?)(?=## |\*\*|$)',
            'skills': r'(## \*\*Technical Skills\*\*.*?)(?=## |\*\*|$)',
            'personal': r'(## \*\*Personal Background and Motivation\*\*.*?)(?=## |\*\*|$)',
            'training': r'(## \*\*Professional Training\*\*.*?)(?=## |\*\*|$)'
        }
        
        for section_name, pattern in section_patterns.items():
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if matches:
                sections[section_name] = matches[0].strip()
        
        return sections

    def _create_enhanced_chunk(self, content: str, source: str, index: int, chunk_type: str) -> Dict[str, Any]:
        """Create enhanced chunk with complete metadata"""
        
        # Enhanced analysis
        metadata = self._comprehensive_chunk_analysis(content)
        
        return {
            "id": f"{source}_chunk_{index}_{chunk_type}",
            "source": source,
            "content": content.strip(),
            "chunk_index": index,
            "chunk_type": chunk_type,
            "entities": metadata["entities"],
            "categories": metadata["categories"], 
            "keywords": metadata["keywords"],
            "importance_score": metadata["importance_score"],
            "content_type": metadata["content_type"],
            "semantic_tags": metadata["semantic_tags"],
            "has_complete_info": metadata["has_complete_info"]
        }

    def _comprehensive_chunk_analysis(self, content: str) -> Dict[str, Any]:
        """Comprehensive analysis to ensure no information is missed"""
        content_lower = content.lower()
        
        # Enhanced entity detection with more patterns
        entities = []
        entity_patterns = {
            "adil_saeed": [r'\badil\s+saeed\b', r'\badil\b(?!\s+ali)', r'\badeel\b'],
            "asad_ali": [r'\basad\s+ali\b', r'\basad\b', r'\belder\s+brother\b'],
            "sir_ali_imran": [r'\bsir\s+ali\s+imran\b', r'\bali\s+imran\s+sindhu\b', r'\bali\s+imran\b'],
            "saad_khan": [r'\bsaad\s+khan\b', r'\bsaad\b'],
            "rohail": [r'\brohail\b'],
            "daud_khan": [r'\bdaud\s+khan\b', r'\bdaud\b'],
            "umer_khan": [r'\bumer\s+khan\b', r'\bumer\b'],
            "hasnain": [r'\bhasnain\b'],
            "imsciences": [r'\bimsciences\b', r'\binstitute\s+of\s+management\s+sciences\b'],
            "giki": [r'\bgiki\b', r'\bghulam\s+ishaq\s+khan\b'],
            "islamia_college": [r'\bislamia\s+college\b', r'\bislamia\b'],
            "skyelectric": [r'\bskyelectric\b', r'\bsky\s+electric\b']
        }
        
        for entity, patterns in entity_patterns.items():
            if any(re.search(pattern, content_lower) for pattern in patterns):
                entities.append(entity)
        
        # Enhanced categories with better coverage
        categories = []
        category_patterns = {
            "contact": [
                r'\bcontact\b', r'\bemail\b', r'\bphone\b', r'\bgithub\b', r'\blinkedin\b',
                r'\bfacebook\b', r'\bsocial\b', r'\bprofile\b', r'\badilsaeed047\b'
            ],
            "projects": [
                r'\bproject\b', r'\bdevelop\b', r'\bbuild\b', r'\bocr\b', r'\bchatbot\b',
                r'\bsentiment\s+analysis\b', r'\bface\s+recognition\b', r'\bsystem\b', r'\bapplication\b'
            ],
            "skills": [
                r'\bskill\b', r'\bpython\b', r'\bjavascript\b', r'\bhtml\b', r'\bcss\b',
                r'\bprogramming\b', r'\btechnology\b', r'\bai\b', r'\bmachine\s+learning\b'
            ],
            "education": [
                r'\beducation\b', r'\buniversity\b', r'\bdegree\b', r'\bimsciences\b', 
                r'\bislamia\s+college\b', r'\bstudent\b', r'\bstudy\b', r'\bacademic\b'
            ],
            "experience": [
                r'\bexperience\b', r'\binternship\b', r'\bwork\b', r'\bjob\b', r'\btraining\b',
                r'\bbootcamp\b', r'\bmicrosoft\b', r'\bgiki\b'
            ],
            "personal": [
                r'\bbrother\b', r'\bfamily\b', r'\bfriend\b', r'\bpersonal\b', r'\bbackground\b',
                r'\basad\s+ali\b', r'\bsaad\s+khan\b', r'\brohail\b', r'\bdaud\b', r'\bumer\b', r'\bhasnain\b'
            ]
        }
        
        for category, patterns in category_patterns.items():
            if any(re.search(pattern, content_lower) for pattern in patterns):
                categories.append(category)
        
        if not categories:
            categories = ["general"]
        
        # Enhanced keyword extraction
        keywords = self._extract_comprehensive_keywords(content_lower)
        
        # Check if chunk has complete information
        has_complete_info = self._check_information_completeness(content)
        
        # Enhanced importance scoring
        importance_score = self._calculate_comprehensive_importance(
            content, entities, categories, keywords, has_complete_info
        )
        
        return {
            "entities": list(set(entities)),
            "categories": list(set(categories)),
            "keywords": list(set(keywords)),
            "importance_score": importance_score,
            "content_type": self._classify_content_type(content),
            "semantic_tags": self._generate_comprehensive_tags(content, entities, categories),
            "has_complete_info": has_complete_info
        }

    def _extract_comprehensive_keywords(self, content_lower: str) -> List[str]:
        """Extract keywords with comprehensive coverage"""
        keywords = []
        
        # Technical keywords
        tech_patterns = {
            'languages': r'\b(python|javascript|html|css|java|sql|mysql)\b',
            'ai_ml': r'\b(ai|ml|machine\s+learning|deep\s+learning|nlp|computer\s+vision|faiss)\b',
            'frameworks': r'\b(react|django|flask|opencv|tensorflow|pytorch|scikit-learn)\b',
            'tools': r'\b(git|github|jupyter|vs\s+code|gradio|huggingface)\b'
        }
        
        for category, pattern in tech_patterns.items():
            matches = re.findall(pattern, content_lower)
            keywords.extend([match if isinstance(match, str) else ' '.join(match) for match in matches])
        
        # Important project keywords
        project_keywords = re.findall(
            r'\b(ocr|chatbot|sentiment|analysis|face|recognition|heart|disease|login|risk)\b', 
            content_lower
        )
        keywords.extend(project_keywords)
        
        # Institution and organization keywords
        org_keywords = re.findall(
            r'\b(imsciences|giki|islamia|skyelectric|microsoft|bootcamp)\b', 
            content_lower
        )
        keywords.extend(org_keywords)
        
        return list(set(keywords))

    def _check_information_completeness(self, content: str) -> bool:
        """Check if chunk contains complete, useful information"""
        content_lower = content.lower()
        
        # Check for complete sentences
        sentence_count = len([s for s in content.split('.') if len(s.strip()) > 10])
        
        # Check for specific complete information patterns
        complete_patterns = [
            r'\badilsaeed047@gmail\.com\b',  # Complete email
            r'\binstitute\s+of\s+management\s+sciences\b',  # Complete institution name
            r'\bsaad\s+khan.*?bacha\s+khan\s+medical\s+college\b',  # Complete friend info
            r'\bocr.*?tesseract.*?opencv\b',  # Complete project info
            r'\bpython.*?javascript.*?html\b'  # Complete skills info
        ]
        
        has_specific_complete_info = any(re.search(pattern, content_lower) for pattern in complete_patterns)
        
        return sentence_count >= 2 or has_specific_complete_info

    def _calculate_comprehensive_importance(self, content: str, entities: List[str], 
                                          categories: List[str], keywords: List[str], 
                                          has_complete_info: bool) -> float:
        """Calculate importance with complete information priority"""
        score = 0.2  # Base score
        
        # Boost for complete information
        if has_complete_info:
            score += 0.3
        
        # Entity scoring with higher weights for key entities
        key_entities = ['adil_saeed', 'imsciences', 'asad_ali']
        entity_boost = sum(0.2 if entity in key_entities else 0.1 for entity in entities)
        score += min(entity_boost, 0.4)
        
        # Category scoring
        important_categories = ['contact', 'projects', 'education', 'personal']
        category_boost = sum(0.15 for cat in categories if cat in important_categories)
        score += min(category_boost, 0.3)
        
        # Keyword density
        if len(content.split()) > 0:
            keyword_density = len(keywords) / len(content.split())
            score += min(keyword_density * 0.2, 0.15)
        
        return min(score, 1.0)

    def _classify_content_type(self, content: str) -> str:
        """Classify content type"""
        content_lower = content.lower()
        
        type_patterns = {
            'contact': ['email', 'contact', 'linkedin', 'github', 'facebook'],
            'project': ['project', 'develop', 'build', 'ocr', 'chatbot'],
            'skill': ['skill', 'python', 'javascript', 'programming'],
            'education': ['university', 'degree', 'imsciences', 'education'],
            'experience': ['experience', 'internship', 'microsoft', 'giki'],
            'personal': ['brother', 'friend', 'family', 'personal']
        }
        
        for content_type, keywords in type_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                return content_type
        
        return 'general'

    def _generate_comprehensive_tags(self, content: str, entities: List[str], categories: List[str]) -> List[str]:
        """Generate comprehensive semantic tags"""
        tags = []
        content_lower = content.lower()
        
        # Add category tags
        tags.extend(categories)
        
        # Add entity-based tags
        if 'adil_saeed' in entities:
            tags.extend(['portfolio', 'profile', 'resume'])
        
        # Add domain tags
        if any(tech in content_lower for tech in ['python', 'javascript', 'web']):
            tags.append('web_development')
        
        if any(ai_term in content_lower for ai_term in ['ai', 'ml', 'machine learning']):
            tags.append('artificial_intelligence')
        
        return list(set(tags))

    def _ensure_key_information_coverage(self, chunks: List[Dict], raw_documents: List[Dict]) -> List[Dict]:
        """CRITICAL: Ensure all key information is covered"""
        
        # Check what information might be missing
        all_chunk_content = ' '.join([chunk.get('content', '') for chunk in chunks]).lower()
        
        missing_info = []
        
        # Key information that must be present
        required_info = {
            'imsciences_full': 'institute of management sciences',
            'email_contact': 'adilsaeed047@gmail.com',
            'friend_saad': 'saad khan',
            'friend_rohail': 'rohail',
            'ocr_project': 'ocr text recognition',
            'giki_bootcamp': 'giki ml llm bootcamp'
        }
        
        for info_key, info_pattern in required_info.items():
            if info_pattern not in all_chunk_content:
                missing_info.append(info_key)
        
        # If critical information is missing, create targeted chunks
        if missing_info:
            logger.warning(f"[MISSING] Creating chunks for missing info: {missing_info}")
            
            for doc in raw_documents:
                content = doc['content'].lower()
                
                for missing_key in missing_info:
                    pattern = required_info[missing_key]
                    
                    # Find section containing this information
                    pattern_index = content.find(pattern)
                    if pattern_index != -1:
                        # Extract broader context around the pattern
                        start = max(0, pattern_index - 200)
                        end = min(len(content), pattern_index + 300)
                        
                        context_content = doc['content'][start:end].strip()
                        
                        # Create targeted chunk
                        targeted_chunk = self._create_enhanced_chunk(
                            context_content, doc['source'], 
                            len(chunks), f"targeted_{missing_key}"
                        )
                        
                        chunks.append(targeted_chunk)
                        logger.info(f"[ADDED] Targeted chunk for {missing_key}")
        
        return chunks

    async def _create_vector_index(self, vector_file: Path):
        """Create vector index"""
        texts = [doc["content"] for doc in self.documents]
        
        embeddings = self.embedding_model.encode(
            texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True
        )
        
        dimension = embeddings.shape[1]
        self.vector_index = faiss.IndexFlatIP(dimension)
        self.vector_index.add(embeddings.astype('float32'))
        
        faiss.write_index(self.vector_index, str(vector_file))
        logger.info(f"📊 Created vector index with {embeddings.shape[0]} embeddings")

    async def _create_bm25_index(self, bm25_file: Path):
        """Create BM25 index"""
        self.tokenized_docs = []
        
        for doc in self.documents:
            text = doc["content"].lower()
            text = re.sub(r'[^\w\s]', ' ', text)
            tokens = [t for t in text.split() if len(t) > 2]
            
            # Add metadata tokens for better matching
            tokens.extend(doc.get("keywords", []))
            tokens.extend(doc.get("entities", []))
            
            self.tokenized_docs.append(tokens)
        
        self.bm25_index = BM25Okapi(self.tokenized_docs)
        
        bm25_data = {"tokenized_docs": self.tokenized_docs}
        with open(bm25_file, 'w', encoding='utf-8') as f:
            json.dump(bm25_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 Created BM25 index")

    async def hybrid_retrieve(self, query: str, top_k: int = 5, intent: Dict = None) -> List[Dict[str, Any]]:
        """Enhanced hybrid retrieval with complete information priority"""
        
        if not self.vector_index or not self.bm25_index:
            return []
        
        try:
            # Enhanced query processing
            processed_query = self._process_query_for_completeness(query)
            
            # Vector search
            vector_results = await self._vector_search(processed_query, top_k * 2)
            
            # BM25 search
            bm25_results = await self._bm25_search(processed_query, top_k * 2)
            
            # Exact matches
            exact_matches = self._find_exact_matches(query)
            
            # Hybrid ranking with completeness priority
            final_results = self._rank_with_completeness_priority(
                query, vector_results, bm25_results, exact_matches
            )
            
            # Filter for quality and completeness
            quality_results = [r for r in final_results if r.get("retrieval_score", 0) > 0.15]
            
            logger.info(f"🎯 Retrieved {len(quality_results)} complete results")
            return quality_results[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Retrieval error: {e}")
            return []

    def _process_query_for_completeness(self, query: str) -> str:
        """Process query to find complete information"""
        # Enhanced typo fixes for better matching
        typo_fixes = {
            'adeel': 'adil', 'contct': 'contact', 'porjects': 'projects',
            'skils': 'skills', 'eduction': 'education', 'experiance': 'experience',
            'freinds': 'friends', 'universtiy': 'university'
        }
        
        processed = query.lower()
        for typo, fix in typo_fixes.items():
            processed = processed.replace(typo, fix)
        
        return processed

    async def _vector_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Vector search with completeness boost"""
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        scores, indices = self.vector_index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents) and score > 0.2:
                # Boost score for complete information
                doc = self.documents[idx]
                if doc.get('has_complete_info', False):
                    score *= 1.2
                
                results.append((idx, float(score)))
        
        return results

    async def _bm25_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """BM25 search"""
        query_tokens = [t for t in query.lower().split() if len(t) > 2]
        if not query_tokens:
            return []
        
        scores = self.bm25_index.get_scores(query_tokens)
        indexed_scores = [(i, score) for i, score in enumerate(scores) if score > 0]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        return indexed_scores[:top_k]

    def _find_exact_matches(self, query: str) -> List[Tuple[int, float]]:
        """Find exact matches with high priority"""
        exact_matches = []
        query_lower = query.lower()
        
        for i, doc in enumerate(self.documents):
            content_lower = doc["content"].lower()
            
            # Exact phrase match
            if query_lower in content_lower:
                score = len(query_lower) / len(content_lower)
                exact_matches.append((i, score * 2.0))
        
        return exact_matches

    def _rank_with_completeness_priority(self, query: str, vector_results: List,
                                       bm25_results: List, exact_matches: List) -> List[Dict]:
        """Rank results prioritizing completeness - OPTIMIZED FOR 90% ACCURACY"""

        doc_scores = {}

        # IMPROVED WEIGHTS for better accuracy
        # Vector scores (40% weight - INCREASED for better semantic understanding)
        if vector_results:
            max_vector = max([s for _, s in vector_results], default=1.0)
            for idx, score in vector_results:
                normalized_score = (score / max_vector) * 0.40  # Increased from 0.35
                doc_scores[idx] = doc_scores.get(idx, 0) + normalized_score

        # BM25 scores (30% weight - INCREASED for better keyword matching)
        if bm25_results:
            max_bm25 = max([s for _, s in bm25_results], default=1.0)
            for idx, score in bm25_results:
                normalized_score = (score / max_bm25) * 0.30  # Increased from 0.25
                doc_scores[idx] = doc_scores.get(idx, 0) + normalized_score

        # Exact match scores (30% weight - HIGH priority for precise matches)
        for idx, score in exact_matches:
            doc_scores[idx] = doc_scores.get(idx, 0) + min(score * 0.30, 0.30)  # Adjusted from 0.40
        
        # Create ranked results
        ranked_results = []
        query_lower = query.lower()

        for idx, final_score in doc_scores.items():
            if idx < len(self.documents):
                doc = self.documents[idx].copy()

                # COMPLETENESS PRIORITY: Boost complete information
                if doc.get("has_complete_info", False):
                    final_score *= 1.3

                # Boost high importance scores
                importance_boost = doc.get("importance_score", 0.5) * 0.1
                final_score += importance_boost

                # INTENT-BASED BOOSTING: Boost documents matching query intent
                content_lower = doc.get("content", "").lower()

                # Social media queries - boost if contains multiple platforms
                if any(term in query_lower for term in ['social media', 'social accounts', 'all accounts']):
                    platforms_count = sum(1 for p in ['linkedin', 'github', 'facebook', 'twitter', 'medium'] if p in content_lower)
                    if platforms_count >= 3:  # If chunk has 3+ platforms
                        final_score *= 1.5  # Strong boost

                # Skills queries - boost if mentions multiple skills
                if 'skill' in query_lower:
                    skill_keywords = ['python', 'java', 'javascript', 'machine learning', 'tensorflow', 'pytorch']
                    skills_count = sum(1 for s in skill_keywords if s in content_lower)
                    if skills_count >= 3:
                        final_score *= 1.4

                # Projects queries - boost if mentions multiple projects
                if 'project' in query_lower:
                    project_keywords = ['chatbot', 'ocr', 'face recognition', 'sentiment', 'portfolio']
                    projects_count = sum(1 for p in project_keywords if p in content_lower)
                    if projects_count >= 2:
                        final_score *= 1.4

                # Contact queries - boost if has contact information
                if any(term in query_lower for term in ['contact', 'email', 'reach', 'connect']):
                    if any(contact in content_lower for contact in ['email', 'linkedin', 'github', '@gmail']):
                        final_score *= 1.3

                doc["retrieval_score"] = final_score
                ranked_results.append(doc)

        ranked_results.sort(key=lambda x: x["retrieval_score"], reverse=True)

        return ranked_results

    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics"""
        if not self.documents:
            return {"status": "not_initialized"}
        
        complete_chunks = sum(1 for doc in self.documents if doc.get("has_complete_info", False))
        
        return {
            "status": "initialized",
            "total_chunks": len(self.documents),
            "complete_info_chunks": complete_chunks,
            "completeness_ratio": round(complete_chunks / len(self.documents), 2),
            "features": ["complete_information_priority", "enhanced_chunking", "targeted_extraction"]
        }