from dotenv import load_dotenv
import os
import huggingface_hub

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

