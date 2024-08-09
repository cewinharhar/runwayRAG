import csv
import ast
from neo4j import GraphDatabase
import pandas as pd
import numpy as np
import time

def similarity_sector(sectors1, sectors2, threshold_percentage=0.5):
    # Convert both sector lists to sets for easier comparison
    set1 = set(sectors1)
    set2 = set(sectors2)
    
    # Find the intersection of both sets
    intersection = set1.intersection(set2)
    
    # Determine the smaller set size
    #min_size = min(len(set1), len(set2))
    decidor = max(len(set1), len(set2))
    
    # Calculate the overlap percentage
    overlap_percentage = len(intersection) / decidor
    
    return overlap_percentage

def similarity_jaccard(list1, list2):
    """
    Calculate the Jaccard similarity between two lists.
    
    Parameters:
    list1 (list): The first list.
    list2 (list): The second list.
    
    Returns:
    float: The Jaccard similarity between the two lists.
    """
    set1 = set(list1)
    set2 = set(list2)
    
    # Calculate the intersection and union of the two sets
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    # Compute the Jaccard similarity
    if union == 0:
        return 0.0
    else:
        return intersection / union

def similarity_embedding_cosine(embedding1, embedding2):
    """
    Calculate the cosine similarity between two vectors.
    
    Parameters:
    embedding1 (list or numpy array): The first vector.
    embedding2 (list or numpy array): The second vector.
    
    Returns:
    float: The cosine similarity between the two vectors.
    """
    # Convert lists to numpy arrays if necessary
    embedding1 = np.array(embedding1)
    embedding2 = np.array(embedding2)
    
    # Calculate the dot product and the magnitudes of the vectors
    dot_product = np.dot(embedding1, embedding2)
    magnitude1 = np.linalg.norm(embedding1)
    magnitude2 = np.linalg.norm(embedding2)
    
    # Compute the cosine similarity
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    else:
        return dot_product / (magnitude1 * magnitude2)