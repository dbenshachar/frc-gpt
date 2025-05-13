from fastapi import FastAPI, Request
from transformers import GPT2LMHeadModel, GPT2Tokenizer, AutoTokenizer
import torch

app = FastAPI()

MODEL_NAME = "gpt2"
MODEL_PATH = "gpt2-java"

model = GPT2LMHeadModel.from_pretrained(MODEL_PATH)
model.eval()

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
SEPARATOR_TOKEN = "\n\n" + "="*50 + " FILE SEPARATOR " + "="*50 + "\n\n"
tokenizer.add_special_tokens({'additional_special_tokens': [SEPARATOR_TOKEN]})
tokenizer.pad_token = tokenizer.eos_token

@app.post("/autocomplete")
async def autocomplete(request: Request):
    data = await request.json()
    try:
        prompt = data.get("prompt", "")
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            **inputs,
            max_new_tokens=50,
            do_sample=True,
            top_p=0.95,
            temperature=0.8,
            pad_token_id=tokenizer.eos_token_id
        )
        completion = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return {"completion": completion[len(prompt):]}
    except Exception as e:
        return {"completion": ""}