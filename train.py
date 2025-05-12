from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
import torch

from datasets import load_dataset, Dataset
import os

MODEL_NAME = "gpt2"
TRAIN_TEST_SPLIT = 0.1

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

print("Loading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME).to(device)
print("Model and tokenizer loaded.")

SEPARATOR_TOKEN = "\n\n" + "="*50 + " FILE SEPARATOR " + "="*50 + "\n\n"
tokenizer.add_special_tokens({'additional_special_tokens': [SEPARATOR_TOKEN]})
tokenizer.pad_token = tokenizer.eos_token
model.resize_token_embeddings(len(tokenizer))

data_dir = "data"
texts = []

print("Loading data...")
for filename in os.listdir(data_dir):
    if filename.endswith(".txt"):
      with open(os.path.join(data_dir, filename), "r", encoding="utf-8") as f:
          texts.append({"text": f.read()})

dataset = Dataset.from_list(texts)
split_dataset = dataset.train_test_split(test_size=TRAIN_TEST_SPLIT, shuffle=True, seed=42)

train_dataset = split_dataset['train']
val_dataset = split_dataset['test']

print("Loaded data:")
print(f"Number of files: {len(texts)}")
print(f"Train dataset size: {len(train_dataset)}")
print(f"Validation dataset size: {len(val_dataset)}")

def tokenize_function(examples):
    tokenized = tokenizer(examples["text"], truncation=True, padding="max_length", max_length=1024)
    tokenized["labels"] = tokenized["input_ids"].copy()  # GPT-2 uses same tokens as labels
    return tokenized

print("Tokenizing data...")
tokenized_train_dataset = train_dataset.map(tokenize_function, batched=True)
tokenized_val_dataset = val_dataset.map(tokenize_function, batched=True)
print("Data tokenized.")

training_args = TrainingArguments(
    output_dir="./gpt2-java",
    per_device_train_batch_size=2,
    num_train_epochs=20,
    save_steps=500,
    logging_dir="./logs",
    logging_steps=10,
    fp16=True,
    push_to_hub=False
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train_dataset,
    eval_dataset=tokenized_val_dataset,
)

print("Starting training...")
print(trainer.train())
print("Training completed.")
print("Saving model...")
trainer.save_model("./gpt2-java")
print("Model saved.")