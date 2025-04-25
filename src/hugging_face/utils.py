from dotenv import load_dotenv
import os
import huggingface_hub
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def login_to_huggingface():
    """
    Logs in to Hugging Face using the token from the environment variables.
    If no token is found, then Hugging Face will prompt the user to enter a token.
    """
    load_dotenv()
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        hf_token = os.getenv("HUGGING_FACE_TOKEN")
    huggingface_hub.login(token=hf_token)

def save_model_state_dict(model: AutoModelForCausalLM, tokenizer: AutoTokenizer, output_dir: str, overwrite: bool = True) -> None:
    """
    Save all model files (state dict, config, and tokenizer files) to the specified directory.
    If the directory exists and overwrite is False, the files will not be saved again.
    """
    print(f"## Saving model files to `{output_dir}`...")
    
    # See if the output directory exists. If so, no need to save the files again.
    if os.path.exists(output_dir):
        if overwrite:
            print(f"## ... Overwriting existing files in `{output_dir}`.")
            shutil.rmtree(output_dir)
        else:
            print(f"## ... Output directory `{output_dir}` already exists. Skipping saving model files.")
            return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save state dict
    state_dict_path = os.path.join(output_dir, "pytorch_model.bin")
    print(f"## ... Saving state dict to `{state_dict_path}`...")
    torch.save(model.state_dict(), state_dict_path)
    
    # Save config
    print("## ... Saving config and tokenizer files...")
    model.config.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print(f"## ... All model files saved to `{output_dir}`.")
    

def save_model_state_dict(model_id: str, output_dir: str, overwrite: bool = True) -> None:
    """
    Save all model files (state dict, config, and tokenizer files) to the specified directory.
    If the directory exists and overwrite is False, the files will not be saved again.
    """
        
    model, tokenizer = get_model_from_hf(model_id) 
    save_model_state_dict(model, tokenizer, output_dir, overwrite)

    
def get_model_from_hf(model_id: str) -> tuple[AutoTokenizer, AutoModelForCausalLM]:
    """
    Load a model from HuggingFace. If the model is already downloaded, it will be loaded from the local HF cache.
    Otherwise, the model will be downloaded from HuggingFace.
    
    The HF_TOKEN will be loaded from the .env file or from the environment variable HF_TOKEN. If the token is not found, 
    the user will be prompted to enter the token.
    """
    print(f"## Loading model `{model_id}` from HuggingFace...")
    
    # Download model
    load_dotenv()
    huggingface_hub.login(token=os.getenv("HF_TOKEN"))

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16)
    print(f"## ... Model `{model_id}` has been loaded.")
    return model, tokenizer

