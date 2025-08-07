"""
This class is used to evaluate the accuracy of string outputs of a model. 

Given a reference answer and a model output, it will return the accuracy of the model output as a percentage.

This class supports both exact match and fuzzy match (using the Monge Elkan Levenshtein algorithm).

INPUTS:
- reference_answer: The reference answer to the question.
- model_output: The output of the model.

OUTPUTS:
- accuracy: The accuracy of the model output as a score between 0.0 and 1.0.

"""
import pandas as pd
from rapidfuzz import fuzz
import logging

logger = logging.getLogger(__name__)

class AccuracyEvaluator:
    """
    A class for evaluating the accuracy of string outputs of a model.
    """
    def __init__(self):
        pass
    
    def evaluate_exact_match_json_answer(self, reference_answer: dict, model_output: dict) -> float:
        """
        Evaluate the accuracy of a model's JSON output against a reference answer. The JSON is 
        assumed to NOT be nested.
        
        To do this, we will go through each key in the reference answer and check if the model output has the same key.
        If the key is not in the model output, we will add 0 to the accuracy score.
        If the key is in the model output:
            - If the value is a string and it is the same as the reference answer, we will add 1 to the accuracy score.
            - If the value is a string and it is not the same as the reference answer, we will add 0 to the accuracy score.
            - If the value is not a string, we will add 0 to the accuracy score.
        We will then return the accuracy score.
        
        @param reference_answer: The reference answer to the question.
        @param model_output: The output of the model.
        @return: The accuracy of the model output as a score between 0.0 and 1.0.
        """
        if not reference_answer:
            logger.error("Reference answer is empty")
            return 0.0
        
        if not model_output:
            logger.error("Model output is empty")
            return 0.0
        
        correct_count = 0
        total_keys = len(reference_answer)
        
        for key in reference_answer:
            if key not in model_output:
                # Key not in model output, add 0 (no increment to correct_count)
                logger.debug(f"Key {key} not in model output")
                continue
            
            ref_value = reference_answer[key]
            model_value = model_output[key]
            
            # Check if both values are strings
            if isinstance(ref_value, str) and isinstance(model_value, str):
                # Compare strings (case-insensitive, consistent with other methods)
                if ref_value.lower() == model_value.lower():
                    correct_count += 1
                # If not the same, add 0 (no increment)
            # If either value is not a string, add 0 (no increment)
        
        # Return accuracy as a ratio (0.0 to 1.0)
        accuracy = correct_count / total_keys
        logger.debug(f"Total correct: {correct_count}, Total keys: {total_keys}, Accuracy: {accuracy}")
        return accuracy
    
    def evaluate_fuzzy_match_json_answer(self, reference_answer: dict, model_output: dict) -> float:
        """
        Evaluate the accuracy of a model's JSON output against a reference answer. The JSON is 
        assumed to NOT be nested.
        
        To do this, we will go through each key in the reference answer and check if the model output has the same key.
        If the key is not in the model output, we will add 0 to the accuracy score.
        If the key is in the model output, evaluate the fuzzy match accuracy of the value.
        We will then return the accuracy score.
        
        @param reference_answer: The reference answer to the question.
        @param model_output: The output of the model.
        @return: The accuracy of the model output as a score between 0.0 and 1.0.
        """
        if not reference_answer:
            logger.error("Reference answer is empty")
            return 0.0
        
        if not model_output:
            logger.error("Model output is empty")
            return 0.0
        
        total_accuracy = 0.0
        total_keys = len(reference_answer)
        
        for key in reference_answer:
            if key not in model_output:
                # Key not in model output, add 0 to the accuracy score (no change to total_accuracy score)
                logger.debug(f"Key {key} not in model output")
                continue
            
            ref_value = reference_answer[key]
            model_value = model_output[key]
            
            # Convert both values to strings and evaluate fuzzy match accuracy
            ref_str = str(ref_value) if ref_value is not None else ""
            model_str = str(model_value) if model_value is not None else ""
            
            # Use the existing fuzzy_match_accuracy function
            fuzzy_score = fuzzy_match_accuracy(ref_str, model_str)
            total_accuracy += fuzzy_score
            
            logger.debug(f"Key {key}: fuzzy match score = {fuzzy_score}")
        
        # Return average accuracy across all keys
        accuracy = total_accuracy / total_keys
        logger.debug(f"Total accuracy: {total_accuracy}, Total keys: {total_keys}, Accuracy: {accuracy}")
        return accuracy



########################################################
# ACCURACY EVALUATION FUNCTIONS
########################################################

def monge_elkan_similarity(str1: str, str2: str) -> float:
    """
    Monge-Elkan similarity using Levenshtein ratio
    Returns a similarity score between 0.0 and 1.0
    
    Note: This alogrithm only captures lexical similarity (how similar the actual words are), 
    not semantic similarity (how similar the meanings are).
    
    Note: when this is called, the strings are already lowercased.
    """
    # Split strings into tokens
    tokens1 = str1.split()
    tokens2 = str2.split()

    # If either string is empty, return exact match
    if not tokens1 or not tokens2: 
        return str1 == str2

    # Monge-Elkan algorithm
    total_sim = 0
    for token1 in tokens1:
        max_sim = max(fuzz.ratio(token1, token2) / 100.0 for token2 in tokens2)
        total_sim += max_sim

    avg_similarity = total_sim / len(tokens1)
    return avg_similarity

def fuzzy_match_accuracy(str1: str, str2: str) -> float:
    """
    Fuzzy string matching (case-insensitive)
    Returns a similarity score between 0.0 and 1.0
    """
    # the similarity of A→B might differ from B→A if they have different lengths.Therefore we take the minimum of both 
    # directions to be more conservative.
    return min(monge_elkan_similarity(str1.lower(), str2.lower()), monge_elkan_similarity(str2.lower(), str1.lower()))

def exact_match_accuracy(str1: str, str2: str) -> float: # returns 1.0 if exact match, 0.0 otherwise
    """
    Exact string matching (case-insensitive)
    Returns 1.0 if exact match, 0.0 otherwise
    """
    if pd.isna(str1) or pd.isna(str2):
        logger.debug(f"One of the strings is NaN: {str1} or {str2}")
        return 0
    return_int = 1 if str1.lower() == str2.lower() else 0
    return float(return_int)