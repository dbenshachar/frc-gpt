import torch
from transformers import GPT2LMHeadModel, AutoTokenizer
import gguf
import numpy as np
import os

MODEL_NAME = "gpt2"
MODEL_PATH = "gpt2-java"
MAX_NEW_TOKENS = 512

model = GPT2LMHeadModel.from_pretrained(MODEL_PATH)
model.eval()

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
SEPARATOR_TOKEN = "\n\n" + "="*50 + " FILE SEPARATOR " + "="*50 + "\n\n"
tokenizer.add_special_tokens({'additional_special_tokens': [SEPARATOR_TOKEN]})
tokenizer.pad_token = tokenizer.eos_token

def convert_gpt2_to_gguf(output_path):
    """Convert GPT-2 model to GGUF format"""
        
    # Get model config
    config = model.config
    
    print(f"Model config: {config}")
    
    # Create GGUF writer
    gguf_writer = gguf.GGUFWriter(output_path, "gpt2-custom")
    
    # Add metadata
    gguf_writer.add_name("GPT-2 Custom Java Model")
    gguf_writer.add_description("Custom fine-tuned GPT-2 model for Java code completion")
    gguf_writer.add_architecture("gpt2")
    gguf_writer.add_context_length(config.n_positions)
    gguf_writer.add_embedding_length(config.n_embd)
    gguf_writer.add_block_count(config.n_layer)
    gguf_writer.add_feed_forward_length(config.n_inner or 4 * config.n_embd)
    gguf_writer.add_head_count(config.n_head)
    gguf_writer.add_vocab_size(config.vocab_size)
    
    # Add tokenizer
    tokens = []
    scores = []
    for i in range(tokenizer.vocab_size):
        token = tokenizer.decode([i])
        tokens.append(token.encode('utf-8'))
        scores.append(0.0)  # Default score
    
    gguf_writer.add_tokenizer_model("gpt2")
    gguf_writer.add_token_list(tokens)
    gguf_writer.add_token_scores(scores)
    
    # Convert model weights
    state_dict = model.state_dict()
    
    # Map PyTorch parameter names to GGUF names
    name_mapping = {
        "transformer.wte.weight": "token_embd.weight",
        "transformer.wpe.weight": "pos_embd.weight",
        "transformer.ln_f.weight": "output_norm.weight",
        "transformer.ln_f.bias": "output_norm.bias",
        "lm_head.weight": "output.weight",
    }
    
    # Add layer weights
    for i in range(config.n_layer):
        layer_prefix = f"transformer.h.{i}"
        gguf_prefix = f"blk.{i}"
        
        name_mapping.update({
            f"{layer_prefix}.ln_1.weight": f"{gguf_prefix}.attn_norm.weight",
            f"{layer_prefix}.ln_1.bias": f"{gguf_prefix}.attn_norm.bias",
            f"{layer_prefix}.attn.c_attn.weight": f"{gguf_prefix}.attn_qkv.weight",
            f"{layer_prefix}.attn.c_attn.bias": f"{gguf_prefix}.attn_qkv.bias",
            f"{layer_prefix}.attn.c_proj.weight": f"{gguf_prefix}.attn_output.weight",
            f"{layer_prefix}.attn.c_proj.bias": f"{gguf_prefix}.attn_output.bias",
            f"{layer_prefix}.ln_2.weight": f"{gguf_prefix}.ffn_norm.weight",
            f"{layer_prefix}.ln_2.bias": f"{gguf_prefix}.ffn_norm.bias",
            f"{layer_prefix}.mlp.c_fc.weight": f"{gguf_prefix}.ffn_up.weight",
            f"{layer_prefix}.mlp.c_fc.bias": f"{gguf_prefix}.ffn_up.bias",
            f"{layer_prefix}.mlp.c_proj.weight": f"{gguf_prefix}.ffn_down.weight",
            f"{layer_prefix}.mlp.c_proj.bias": f"{gguf_prefix}.ffn_down.bias",
        })
    
    # Add tensors to GGUF
    for pytorch_name, tensor in state_dict.items():
        if pytorch_name in name_mapping:
            gguf_name = name_mapping[pytorch_name]
            
            # Convert to numpy and ensure correct data type
            tensor_np = tensor.detach().cpu().numpy().astype(np.float32)
            
            print(f"Adding tensor: {pytorch_name} -> {gguf_name}, shape: {tensor_np.shape}")
            gguf_writer.add_tensor(gguf_name, tensor_np)
        else:
            print(f"Warning: Unmapped tensor {pytorch_name}")
    
    # Write the file
    print(f"Writing GGUF file to {output_path}")
    gguf_writer.write_header_to_file()
    gguf_writer.write_kv_data_to_file()
    gguf_writer.write_tensors_to_file()
    gguf_writer.close()
    
    print(f"Successfully converted model to {output_path}")

if __name__ == "__main__":
    MODEL_PATH = "gpt2-java"  # Your model directory
    OUTPUT_PATH = "gpt2-java-custom.gguf"
    
    # Install required packages if not already installed
    try:
        import gguf
    except ImportError:
        print("Installing gguf package...")
        os.system("pip install gguf")
        import gguf
    
    convert_gpt2_to_gguf(MODEL_PATH, OUTPUT_PATH)