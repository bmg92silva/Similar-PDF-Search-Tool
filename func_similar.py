import numpy as np
from func_db import fetch_embeddings_from_db


def normalize_query_embedding(query_embedding):
    """
    Convert query embedding to numpy array and flatten to 1D.
    
    Parameters:
    -----------
    query_embedding : numpy.ndarray or bytes
        The query embedding vector
    
    Returns:
    --------
    numpy.ndarray
        Flattened 1D numpy array of float32
    """
    if isinstance(query_embedding, bytes):
        query_embedding = np.frombuffer(query_embedding, dtype=np.float32)
    else:
        query_embedding = np.array(query_embedding, dtype=np.float32)
    
    return query_embedding.flatten()


def calculate_cosine_similarity(query_embedding, stored_embedding_blob):
    """
    Calculate cosine similarity between query and stored embedding.
    
    Parameters:
    -----------
    query_embedding : numpy.ndarray
        Normalized query embedding vector
    stored_embedding_blob : bytes
        Stored embedding as bytes
    
    Returns:
    --------
    float
        Cosine similarity score (-1 to 1)
    """
    stored_embedding = np.frombuffer(stored_embedding_blob, dtype=np.float32)
    
    dot_product = np.dot(query_embedding, stored_embedding)
    query_norm = np.linalg.norm(query_embedding)
    stored_norm = np.linalg.norm(stored_embedding)
    
    if query_norm == 0 or stored_norm == 0:
        return 0
    
    return dot_product / (query_norm * stored_norm)


def compute_all_similarities(query_embedding, db_rows):
    """
    Compute similarities for all database entries.
    
    Parameters:
    -----------
    query_embedding : numpy.ndarray
        Normalized query embedding vector
    db_rows : list of tuples
        List of (material_code, embedding_blob, image_blob)
    
    Returns:
    --------
    list of tuples
        List of (material_code, similarity_score, image_blob)
    """
    similarities = []
    
    for material_code, embedding_blob, image_blob in db_rows:
        cosine_similarity = calculate_cosine_similarity(query_embedding, embedding_blob)
        similarities.append((material_code, cosine_similarity, image_blob))
    
    return similarities


def get_top_k_results(similarities, top_k=12):
    """
    Sort similarities and return top k results.
    
    Parameters:
    -----------
    similarities : list of tuples
        List of (material_code, similarity_score, image_blob)
    top_k : int
        Number of top results to return
    
    Returns:
    --------
    list of tuples
        Top k results sorted by similarity (highest first)
    """
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]



def find_similar_pipeline(query_embedding, top_k=12):
    """
    Find the k most similar embeddings using cosine similarity.
    
    Pipeline function that orchestrates the entire similarity search process.
    
    Parameters:
    -----------
    query_embedding : numpy.ndarray or bytes
        The query embedding vector (can be numpy array or bytes)
    top_k : int
        Number of closest embeddings to return (default: 12)
    
    Returns:
    --------
    list of tuples
        List of (material_code, similarity_score, image_blob) for the top_k most similar embeddings.
        - similarity_score: cosine similarity (higher = more similar, range: -1 to 1)
    """
    # Retrieve all embeddings
    rows = fetch_embeddings_from_db()
    
    if not rows:
        return []
    
    # Normalize query embedding
    query_embedding = normalize_query_embedding(query_embedding)
    
    # Compute similarities for all embeddings
    similarities = compute_all_similarities(query_embedding, rows)
    
    # Get top k results
    top_results = get_top_k_results(similarities, top_k)
    
    return top_results
