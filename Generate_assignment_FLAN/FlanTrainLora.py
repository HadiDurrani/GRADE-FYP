from transformers import T5ForConditionalGeneration, T5Tokenizer, DataCollatorForSeq2Seq, TrainingArguments, Trainer
from datasets import Dataset
from peft import LoraConfig, get_peft_model
import json

# Load dataset
dataset_path = "C:/FYP/front end/mywebsite/Generate_assignment_FLAN/data.json"
with open(dataset_path, "r") as f:
    raw_data = json.load(f)

# Load tokenizer and model
model_name = "google/flan-t5-large"  # Use "flan-t5-base" or "flan-t5-large"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)


# Preprocess data
def preprocess_data(dataset, tokenizer, max_input_length=128, max_output_length=64):
    inputs = []
    outputs = []
    for item in dataset:
        input_text = f"generate question: {item['clo']} type: {item['type']}"
        output_text = item['question']
        inputs.append(input_text)
        outputs.append(output_text)

    tokenized_inputs = tokenizer(
        inputs, max_length=max_input_length, truncation=True, padding="max_length"
    )
    tokenized_outputs = tokenizer(
        outputs, max_length=max_output_length, truncation=True, padding="max_length"
    )

    tokenized_inputs["labels"] = tokenized_outputs["input_ids"]
    return tokenized_inputs

# Tokenize and split data
tokenized_data = preprocess_data(raw_data, tokenizer)
hf_dataset = Dataset.from_dict(tokenized_data)
train_test_split = hf_dataset.train_test_split(test_size=0.2, seed=42)
train_dataset = train_test_split["train"]
eval_dataset = train_test_split["test"]

# LoRA configuration
lora_config = LoraConfig(
    r=8,  
    lora_alpha=16,  # Scaling factor
    target_modules=["q", "v"],  # Target layers (e.g., query/key/value in attention)
    lora_dropout=0.1,  # Dropout for LoRA layers
    bias="none",  # Use "none", "all", or "lora_only"
    task_type="SEQ_2_SEQ_LM"  # Task type
)

# Apply LoRA to the model
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Fine-tune the model
def fine_tune_with_lora(model, tokenizer, train_dataset, eval_dataset):
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
    )

    training_args = TrainingArguments(
        output_dir="./flan-t5-lora",
        evaluation_strategy="steps",
        eval_steps=50,
        save_steps=50,
        logging_steps=50,
        overwrite_output_dir=True,
        num_train_epochs=5,
        per_device_train_batch_size=8,
        learning_rate=5e-5,
        warmup_steps=100,
        save_total_limit=2,
        logging_dir="./logs",
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

# Train the model with LoRA
fine_tune_with_lora(model, tokenizer, train_dataset, eval_dataset)

# Save the LoRA-adapted model
model.save_pretrained("./fine_tuned_lora_model")
tokenizer.save_pretrained("./fine_tuned_lora_model")

print("LoRA fine-tuning complete!")
