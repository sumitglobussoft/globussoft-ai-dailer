import os
import faiss
import numpy as np
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import json

# Ensure index folder exists
INDEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faiss_indexes")
os.makedirs(INDEX_DIR, exist_ok=True)

# Load local embedding model (free, rapid execution)
# all-MiniLM-L6-v2 maps sentences to 384 dimensional dense vector space.
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def get_index_path(org_id: int):
    return os.path.join(INDEX_DIR, f"org_{org_id}.index")

def get_metadata_path(org_id: int):
    return os.path.join(INDEX_DIR, f"org_{org_id}_meta.json")

def load_index_and_meta(org_id: int):
    index_path = get_index_path(org_id)
    meta_path = get_metadata_path(org_id)
    
    if os.path.exists(index_path) and os.path.exists(meta_path):
        index = faiss.read_index(index_path)
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        return index, meta
    return None, []

def save_index_and_meta(org_id: int, index, meta):
    index_path = get_index_path(org_id)
    faiss.write_index(index, index_path)
    with open(get_metadata_path(org_id), 'w', encoding='utf-8') as f:
        json.dump(meta, f)

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100):
    """Split text into overlapping pieces to ensure complete semantic capture."""
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def ingest_pdf(filepath: str, org_id: int, filename: str) -> int:
    """Extracts text from a PDF, embeds the chunks, and appends to the Org FAISS index."""
    doc = fitz.open(filepath)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    
    chunks = chunk_text(full_text)
    if not chunks:
        return 0

    # Generate embeddings
    embeddings = embedder.encode(chunks)
    embeddings = np.array(embeddings).astype('float32')

    # Build or Load index
    index, meta = load_index_and_meta(org_id)
    
    if index is None:
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
    
    # Add to FAISS
    index.add(embeddings)
    
    # Store metadata associated with the new embeddings
    for chunk in chunks:
        meta.append({"filename": filename, "text": chunk})
        
    save_index_and_meta(org_id, index, meta)
    return len(chunks)

def remove_file_from_index(filename: str, org_id: int):
    """Rebuilds the FAISS index cleanly omitting the specified file's chunks."""
    index, meta = load_index_and_meta(org_id)
    if not index or not meta:
        return False
        
    filtered_meta = [m for m in meta if m.get("filename") != filename]
    if len(filtered_meta) == len(meta):
        # File not found
        return False
        
    # FAISS does not natively support deleting rows from IndexFlatL2 easily,
    # so we rebuild the core vector index from text directly if needed.
    # To save overhead, we'll re-embed the filtered chunks! 
    # (In massive systems you'd use IndexIDMap, but FlatL2 rebuilding is ~20ms here)
    if len(filtered_meta) == 0:
        # Clear out completely
        if os.path.exists(get_index_path(org_id)):
            os.remove(get_index_path(org_id))
        if os.path.exists(get_metadata_path(org_id)):
            os.remove(get_metadata_path(org_id))
        return True
        
    texts_to_keep = [m["text"] for m in filtered_meta]
    new_embeddings = embedder.encode(texts_to_keep)
    new_embeddings = np.array(new_embeddings).astype('float32')
    
    dim = new_embeddings.shape[1]
    new_index = faiss.IndexFlatL2(dim)
    new_index.add(new_embeddings)
    
    save_index_and_meta(org_id, new_index, filtered_meta)
    return True

def retrieve_context(query: str, org_id: int, top_k: int = 3) -> str:
    """Returns the top matching context chunks for the given LLM intent."""
    index, meta = load_index_and_meta(org_id)
    if not index or not meta:
        return ""
        
    query_vector = embedder.encode([query]).astype('float32')
    distances, indices = index.search(query_vector, min(top_k, len(meta)))
    
    results = []
    for idx in indices[0]:
        if idx >= 0 and idx < len(meta):
            results.append(meta[idx]["text"])
            
    if not results:
        return ""
        
    return " ".join(results)
