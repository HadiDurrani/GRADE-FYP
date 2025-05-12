import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
import json
import random
from peft import PeftModel
import torch

# Load the fine-tuned LoRA model
model_path = "./Generate_assignment_FLAN/fine_tuned_lora_model"
tokenizer = T5Tokenizer.from_pretrained(model_path)
base_model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-large")
model = PeftModel.from_pretrained(base_model, model_path)

# Ensure the model is in evaluation mode
model.eval()

# Load dataset from existing JSON file
dataset_path = "./Generate_assignment_FLAN/data.json"
with open(dataset_path, "r") as f:
    dataset = json.load(f)

# Filter dataset by CLO and question type
def filter_questions_by_clos_and_type(clos, question_type):
    return [
        item["clo"]
        for item in dataset
        if question_type in item["type"] and any(clo in item["clo"] for clo in clos)
    ]

def get_prompt(clo, question_type):
    return (
        f"Instruction: Generate a {question_type} question in Python.\n"
        f"Topic: {clo}\n"
        f"Output:"
    )


# def get_prompt(clo, question_type):
#     if question_type == "code":
#         return f"Generate a coding question related to Python that focuses on the topic: '{clo}', ensuring it aligns with programming fundamentals."
#     elif question_type == "theory":
#         return f"Generate a theory question related to Python focusing on the topic: '{clo}'. Be specific to programming and avoid unrelated domains."
#     else:
#         return f"Generate a Python question focusing on the topic: '{clo}', ensuring relevance to programming concepts."


def generate_questions_for_clo(clo, question_type, num_questions, max_length=250):
    generated_questions = []
    attempts = 0
    max_attempts = num_questions * 3  # Allow 3 tries per question

    while len(generated_questions) < num_questions and attempts < max_attempts:
        input_text = get_prompt(clo, question_type)
        input_ids = tokenizer.encode(input_text, return_tensors="pt")

        with torch.no_grad():
            outputs = model.generate(
                input_ids=input_ids,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                top_k=20,
                top_p=0.8,
                do_sample=True
            )

        for output in outputs:
            generated_question = tokenizer.decode(output, skip_special_tokens=True)
            if generated_question not in generated_questions:
                generated_questions.append(generated_question)

        attempts += 1

    return generated_questions[:num_questions]

def generate_questions_based_on_clos(clos_allocation, question_type, max_length=50):
    all_generated_questions = []
    for clo, num_questions in clos_allocation.items():
        questions = generate_questions_for_clo(clo, question_type, num_questions, max_length)
        all_generated_questions.extend(questions)
    return all_generated_questions

# Example usage
# clos_allocation = {
#     "Arithmetic Operations": 1,
#     "Input/Output Operations": 1
# }
# question_type = "code"  # Change to "code" for coding questions
# questions = generate_questions_based_on_clos(clos_allocation, question_type)

# print("\nGenerated Questions:")
# for i, q in enumerate(questions, 1):
#     print(f"{i}. {q}")
