import ast
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher
import torch

def get_t5_embedding(code, tokenizer, model):
    """Generates embeddings using T5"""
    inputs = tokenizer(code, return_tensors="pt", max_length=512, truncation=True, padding=True)
    with torch.no_grad():
        outputs = model.encoder(**inputs).last_hidden_state
    return outputs.mean(dim=1).numpy()

def get_ast_similarity(student_code, reference_code):
    """Compares AST structure similarity"""
    try:
        student_ast = ast.dump(ast.parse(student_code))
        reference_ast = ast.dump(ast.parse(reference_code))
        return SequenceMatcher(None, student_ast, reference_ast).ratio()
    except SyntaxError:
        return 0  # Completely invalid code

def token_overlap_score(student_code, reference_code):
    """Calculates token overlap percentage"""
    student_tokens = set(student_code.split())
    reference_tokens = set(reference_code.split())
    overlap = len(student_tokens & reference_tokens) / max(len(reference_tokens), 1)  # Avoid division by zero
    return overlap

def evaluate_code(student_code, reference_code, tokenizer, model, w_t5=0.7, w_ast=0.15, w_overlap=0.15, max_score=10):
    """Evaluates a student's code answer based on logic, structure, and tokens"""
    
    # Generate embeddings and compute similarity
    ref_embedding = get_t5_embedding(reference_code, tokenizer, model)
    student_embedding = get_t5_embedding(student_code, tokenizer, model)
    t5_score = cosine_similarity(ref_embedding, student_embedding)[0][0]
    
    # Compare AST structures
    ast_score = get_ast_similarity(student_code, reference_code)
    
    # Token similarity
    overlap_score = token_overlap_score(student_code, reference_code)

    # Compute final weighted score
    final_score = round((w_t5 * t5_score + w_ast * ast_score + w_overlap * overlap_score) * max_score, 2)

    print("\n🚀 DEBUG: Code Evaluation")
    print(f"Student Code:\n{student_code}")
    print(f"Reference Code:\n{reference_code}")
    print(f"T5 Similarity Score: {t5_score}")
    print(f"AST Similarity Score: {ast_score}")
    print(f"Token Overlap Score: {overlap_score}")
    print(f"Final Score (Scaled to 10): {final_score}\n")

    return final_score
