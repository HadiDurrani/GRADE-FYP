import torch
from transformers import (
    GPT2LMHeadModel,
    GPT2Tokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments
)
import json

dataset_path = "CLOqu.json"
with open(dataset_path, "r") as f:
    data = json.load(f)

def convert_json_to_text(dataset, output_path):
    with open(output_path, "w") as f:
        for item in dataset:
            f.write(item["question"] + "\n")

training_file = "clo_training.txt"
convert_json_to_text(data, training_file)

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")

tokenizer.pad_token = tokenizer.eos_token

def load_text_dataset(file_path, tokenizer, block_size=128):
    from transformers import TextDataset

    return TextDataset(
        tokenizer=tokenizer,
        file_path=file_path,
        block_size=block_size,
    )

train_dataset = load_text_dataset(training_file, tokenizer)

from sklearn.model_selection import train_test_split

with open(training_file, "r") as f:
    all_lines = f.readlines()

train_lines, eval_lines = train_test_split(all_lines, test_size=0.2, random_state=42)

train_file = "clo_train_split.txt"
eval_file = "clo_eval_split.txt"

with open(train_file, "w") as f:
    f.writelines(train_lines)

with open(eval_file, "w") as f:
    f.writelines(eval_lines)

train_dataset = load_text_dataset(train_file, tokenizer)
eval_dataset = load_text_dataset(eval_file, tokenizer)

def fine_tune_model(model, tokenizer, train_dataset, eval_dataset):
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  
    )

    training_args = TrainingArguments(
        output_dir="./gpt2-finetuned",
        evaluation_strategy="steps",
        eval_steps=50,  
        save_steps=50,
        logging_steps=50,
        overwrite_output_dir=True,
        num_train_epochs=5,
        per_device_train_batch_size=8,
        save_total_limit=2,
        learning_rate=5e-5,
        warmup_steps=100,
        logging_dir="./logs",
        remove_unused_columns=False,  
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,  
        tokenizer=tokenizer,
    )

    trainer.train()

fine_tune_model(model, tokenizer, train_dataset, eval_dataset)

model.save_pretrained("./fine_tuned_model")
tokenizer.save_pretrained("./fine_tuned_model")

print("Model fine-tuning complete!")
