import json
import torch
import random
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Load the fine-tuned model and tokenizer
model_path = "./question_generator/fine_tuned_model"
tokenizer = GPT2Tokenizer.from_pretrained(model_path)
model = GPT2LMHeadModel.from_pretrained(model_path)

# Load dataset from existing JSON file
dataset_path = "./question_generator/CLOqu.json"
with open(dataset_path, "r") as f:
    dataset = json.load(f)

def filter_questions_by_clos_and_type(clos, question_type):
    return [
        item["question"]
        for item in dataset
        if question_type in item["type"] and any(clo in item["clo"] for clo in clos)
    ]

def generate_questions_for_clo(clo, question_type, num_questions, max_length=55):
    filtered_prompts = filter_questions_by_clos_and_type([clo], question_type)

    random.shuffle(filtered_prompts)

    generated_questions = []
    for prompt in filtered_prompts[:num_questions]:
        input_ids = tokenizer.encode(prompt, return_tensors="pt")
        with torch.no_grad():
            output = model.generate(
                input_ids=input_ids,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                top_k=50,
                top_p=0.9,
                do_sample=True
            )

        for sequence in output:
            generated_question = tokenizer.decode(sequence, skip_special_tokens=True)
            if generated_question.lower() not in [item["question"].lower() for item in dataset]:
                generated_questions.append(generated_question)

    return generated_questions[:num_questions]

def generate_questions_based_on_clos(clos_allocation, question_type, max_length=50):
    all_generated_questions = []
    for clo, num_questions in clos_allocation.items():
        questions = generate_questions_for_clo(clo, question_type, num_questions, max_length)
        all_generated_questions.extend(questions)
    return all_generated_questions

# Example usage
clos_allocation = {
    "Strings": 2,
    "Arithmetic Operations": 2,
    "Input/Output Operations": 1
}
question_type = "theory"
questions = generate_questions_based_on_clos(clos_allocation, question_type)

print("\nGenerated Questions:")
for i, q in enumerate(questions, 1):
    print(f"{i}. {q}")
