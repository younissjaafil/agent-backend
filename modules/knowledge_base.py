"""
Enhanced Knowledge Base Module - CORRECTED FINAL VERSION
User-Specific Knowledge + Company Root Knowledge + PDF Support + Encoding Fixes
"""

import os
import glob
import hashlib
import logging
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
import time
import json
import shutil

logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self, user_name=None):
        """Initialize with user-specific knowledge"""
        self.user_name = user_name or "default"
        self.knowledge_chunks = []
        
        # Paths
        self.company_knowledge_dir = "./company_knowledge"
        self.user_knowledge_dir = f"./user_knowledge/{self.user_name}"
        
        self.create_directories()
        logger.info(f"🧠 Knowledge Base initialized for user: {self.user_name}")
    
    def create_directories(self):
        """Create directories for knowledge management"""
        directories = [
            self.company_knowledge_dir,
            f"{self.company_knowledge_dir}/docs",
            f"{self.company_knowledge_dir}/websites",
            self.user_knowledge_dir,
            f"{self.user_knowledge_dir}/docs",
            f"{self.user_knowledge_dir}/uploads"
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"📁 Created directory: {directory}")
    
    def chunk_text(self, text: str, chunk_size: int = 400) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk.strip()) > 50:
                chunks.append(chunk.strip())
        
        return chunks
    
    def add_user_file(self, file_path: str, original_filename: str = None) -> bool:
        """Add user-uploaded file to their knowledge base - ENHANCED VERSION"""
        try:
            if not original_filename:
                original_filename = os.path.basename(file_path)
            
            # Copy to user directory
            user_file_path = os.path.join(self.user_knowledge_dir, "uploads", original_filename)
            shutil.copy2(file_path, user_file_path)
            
            # Process the file based on extension
            file_ext = original_filename.lower().split('.')[-1]
            text = ""
            
            if file_ext == 'txt':
                # Handle text files with multiple encoding attempts
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            text = f.read()
                        logger.info(f"✅ Read text file with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if not text:
                    logger.error(f"❌ Could not decode text file: {original_filename}")
                    return False
                    
            elif file_ext == 'pdf':
                # Handle PDF files
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page_num, page in enumerate(reader.pages):
                            try:
                                page_text = page.extract_text()
                                text += page_text + "\\n"
                            except Exception as e:
                                logger.warning(f"Failed to extract page {page_num}: {e}")
                                continue
                    
                    if not text.strip():
                        logger.error(f"❌ No text extracted from PDF: {original_filename}")
                        return False
                        
                    logger.info(f"✅ Extracted text from PDF: {len(text)} characters")
                    
                except ImportError:
                    logger.error("❌ PyPDF2 not installed. Run: pip install PyPDF2")
                    return False
                except Exception as e:
                    logger.error(f"❌ PDF processing error: {e}")
                    return False
            
            else:
                logger.warning(f"⚠️ Unsupported file type: {file_ext}. Supported: txt, pdf")
                return False
            
            # Process text into chunks
            if text and text.strip():
                chunks = self.chunk_text(text)
                for chunk in chunks:
                    self.knowledge_chunks.append({
                        "content": chunk,
                        "source": f"user_upload:{original_filename}",
                        "type": "user_document",
                        "user": self.user_name
                    })
                
                logger.info(f"✅ Added user file: {original_filename} ({len(chunks)} chunks)")
                return True
            else:
                logger.error(f"❌ No content extracted from: {original_filename}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to add user file {original_filename}: {e}")
            return False
    
    def process_audio_file(self, audio_path: str, is_company: bool = False) -> bool:
        """Process MP3/audio files using speech-to-text"""
        try:
            import speech_recognition as sr
            
            # Convert MP3 to WAV if needed
            processed_path = audio_path
            if audio_path.lower().endswith('.mp3'):
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_mp3(audio_path)
                    processed_path = audio_path.replace('.mp3', '_temp.wav')
                    audio.export(processed_path, format="wav")
                except ImportError:
                    logger.error("pydub not installed. Run: pip install pydub")
                    return False
            
            # Speech to text
            r = sr.Recognizer()
            with sr.AudioFile(processed_path) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data)
            
            # Clean up temp file
            if processed_path != audio_path and os.path.exists(processed_path):
                os.remove(processed_path)
            
            # Process text into chunks
            if text:
                chunks = self.chunk_text(text)
                source_prefix = "company" if is_company else "user"
                
                for chunk in chunks:
                    self.knowledge_chunks.append({
                        "content": chunk,
                        "source": f"{source_prefix}_audio:{os.path.basename(audio_path)}",
                        "type": "audio_transcript",
                        "user": "company" if is_company else self.user_name
                    })
                
                logger.info(f"✅ Processed audio: {os.path.basename(audio_path)}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return False
    
    def load_company_knowledge(self):
        """Load company root knowledge (available to all users)"""
        logger.info("🏢 Loading company knowledge...")
        
        # 1. Load company TEXT documents
        company_docs = glob.glob(f"{self.company_knowledge_dir}/docs/*.txt")
        print(f"🔍 DEBUG: Found company docs: {company_docs}")
        
        for doc_path in company_docs:
            try:
                # Handle text files with multiple encoding attempts
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                text = ""
                
                for encoding in encodings:
                    try:
                        with open(doc_path, 'r', encoding=encoding) as f:
                            text = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if text:
                    chunks = self.chunk_text(text)
                    for chunk in chunks:
                        self.knowledge_chunks.append({
                            "content": chunk,
                            "source": f"company:{os.path.basename(doc_path)}",
                            "type": "company_document",
                            "user": "company"
                        })
                    
                    logger.info(f"✅ Loaded company doc: {os.path.basename(doc_path)}")
                else:
                    logger.error(f"❌ Could not decode company doc: {doc_path}")
                    
            except Exception as e:
                logger.error(f"Failed to load company doc {doc_path}: {e}")
        
        # 2. Load company PDF documents
        company_pdfs = glob.glob(f"{self.company_knowledge_dir}/docs/*.pdf")
        print(f"🔍 DEBUG: Found company PDFs: {company_pdfs}")

        for pdf_path in company_pdfs:
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        try:
                            text += page.extract_text() + "\\n"
                        except:
                            continue
                
                if text.strip():
                    chunks = self.chunk_text(text)
                    for chunk in chunks:
                        self.knowledge_chunks.append({
                            "content": chunk,
                            "source": f"company_pdf:{os.path.basename(pdf_path)}",
                            "type": "company_document",
                            "user": "company"
                        })
                    
                    logger.info(f"✅ Loaded company PDF: {os.path.basename(pdf_path)} ({len(chunks)} chunks)")
                
            except ImportError:
                logger.error("❌ PyPDF2 not installed for PDF processing")
            except Exception as e:
                logger.error(f"Failed to load company PDF {pdf_path}: {e}")
        
        # 3. Load company AUDIO files
        audio_extensions = ['*.mp3', '*.wav', '*.m4a']
        company_audio = []
        for ext in audio_extensions:
            company_audio.extend(glob.glob(f"{self.company_knowledge_dir}/docs/{ext}"))
        
        print(f"🔍 DEBUG: Found company audio: {company_audio}")
        
        for audio_path in company_audio:
            self.process_audio_file(audio_path, is_company=True)
        
        # 4. Load company websites
        websites_file = f"{self.company_knowledge_dir}/websites/urls.txt"
        if os.path.exists(websites_file):
            try:
                with open(websites_file, 'r') as f:
                    urls = [line.strip() for line in f if line.strip()]
                
                print(f"🔍 DEBUG: Found company websites: {len(urls)} URLs")
                
                for url in urls:
                    self.add_website(url, is_company=True)
                    time.sleep(2)  # Be nice to servers
                    
            except Exception as e:
                logger.error(f"Failed to load company websites: {e}")
    
    def load_user_knowledge(self):
        """Load user-specific knowledge"""
        logger.info(f"👤 Loading knowledge for user: {self.user_name}")
        
        # Load user documents
        user_docs = glob.glob(f"{self.user_knowledge_dir}/docs/*.txt")
        for doc_path in user_docs:
            try:
                # Handle text files with multiple encoding attempts
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                text = ""
                
                for encoding in encodings:
                    try:
                        with open(doc_path, 'r', encoding=encoding) as f:
                            text = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if text:
                    chunks = self.chunk_text(text)
                    for chunk in chunks:
                        self.knowledge_chunks.append({
                            "content": chunk,
                            "source": f"user_doc:{os.path.basename(doc_path)}",
                            "type": "user_document",
                            "user": self.user_name
                        })
                    
                    logger.info(f"✅ Loaded user doc: {os.path.basename(doc_path)}")
                else:
                    logger.error(f"❌ Could not decode user doc: {doc_path}")
                    
            except Exception as e:
                logger.error(f"Failed to load user doc {doc_path}: {e}")
        
        # Load user uploads (both txt and pdf)
        user_uploads = glob.glob(f"{self.user_knowledge_dir}/uploads/*")
        print(f"🔍 DEBUG: Found user uploads: {user_uploads}")
        
        for upload_path in user_uploads:
            file_ext = upload_path.lower().split('.')[-1]
            
            try:
                text = ""
                
                if file_ext == 'txt':
                    # Handle text files with multiple encoding attempts
                    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                    for encoding in encodings:
                        try:
                            with open(upload_path, 'r', encoding=encoding) as f:
                                text = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                
                elif file_ext == 'pdf':
                    # Handle PDF files
                    try:
                        import PyPDF2
                        with open(upload_path, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            for page in reader.pages:
                                try:
                                    text += page.extract_text() + "\\n"
                                except:
                                    continue
                    except ImportError:
                        logger.error("PyPDF2 not installed for PDF processing")
                        continue
                    except Exception as e:
                        logger.error(f"PDF processing error: {e}")
                        continue
                
                if text and text.strip():
                    chunks = self.chunk_text(text)
                    for chunk in chunks:
                        self.knowledge_chunks.append({
                            "content": chunk,
                            "source": f"user_upload:{os.path.basename(upload_path)}",
                            "type": "user_upload",
                            "user": self.user_name
                        })
                    
                    logger.info(f"✅ Loaded user upload: {os.path.basename(upload_path)}")
                    
            except Exception as e:
                logger.error(f"Failed to load user upload {upload_path}: {e}")
    
    def add_website(self, url: str, is_company: bool = False) -> bool:
        """Scrape and add website content"""
        try:
            logger.info(f"📄 Scraping: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            text = ' '.join(text.split())
            chunks = self.chunk_text(text)
            
            # Store chunks
            for chunk in chunks:
                self.knowledge_chunks.append({
                    "content": chunk,
                    "source": f"{'company' if is_company else 'user'}_website:{url}",
                    "type": "website",
                    "user": "company" if is_company else self.user_name
                })
            
            logger.info(f"✅ Added {len(chunks)} chunks from {url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add website {url}: {e}")
            return False
    
    def search_knowledge(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search both company and user knowledge"""
        try:
            query_words = query.lower().split()
            results = []
            
            for chunk in self.knowledge_chunks:
                content_lower = chunk["content"].lower()
                score = sum(1 for word in query_words if word in content_lower)
                
                if score > 0:
                    # Boost company knowledge slightly
                    boost = 1.2 if chunk["user"] == "company" else 1.0
                    
                    results.append({
                        "content": chunk["content"],
                        "source": chunk["source"],
                        "type": chunk["type"],
                        "user": chunk["user"],
                        "similarity": (score / len(query_words)) * boost
                    })
            
            # Sort by score and return top results
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:n_results]
            
        except Exception as e:
            logger.error(f"❌ Knowledge search failed: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get knowledge statistics"""
        company_chunks = len([c for c in self.knowledge_chunks if c["user"] == "company"])
        user_chunks = len([c for c in self.knowledge_chunks if c["user"] == self.user_name])
        
        return {
            "total_chunks": len(self.knowledge_chunks),
            "company_chunks": company_chunks,
            "user_chunks": user_chunks,
            "user_name": self.user_name,
            "status": "loaded" if len(self.knowledge_chunks) > 0 else "empty"
        }
    
    def load_all_knowledge(self):
        """Load both company and user knowledge"""
        self.knowledge_chunks = []  # Reset
        self.load_company_knowledge()
        self.load_user_knowledge()
        
        stats = self.get_stats()
        logger.info(f"📊 Knowledge loaded - Company: {stats['company_chunks']}, User: {stats['user_chunks']}")
    
    def get_user_files(self) -> List[str]:
        """Get list of user uploaded files"""
        try:
            uploads_dir = f"{self.user_knowledge_dir}/uploads"
            if os.path.exists(uploads_dir):
                return [f for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))]
            return []
        except Exception as e:
            logger.error(f"Failed to get user files: {e}")
            return []
