from sklearn.metrics.pairwise import cosine_similarity

def similarity_to_score(similarity, max_score=10):
    return round(similarity * max_score, 2)


def evaluate_theory(student_answer, reference_solution, model, max_score=10):
    """Evaluates a theory answer using Sentence Transformer similarity & token overlap"""
    
    ref_embedding = model.encode(reference_solution)
    student_embedding = model.encode(student_answer)
    
    similarity = cosine_similarity([ref_embedding], [student_embedding])[0][0]

    final_score = round(similarity * max_score, 2)

    if similarity < 0.3: 
        print("🚨 Low Similarity Detected! Applying penalty.")
        final_score = max(0, final_score * 0.5)  

    return final_score
