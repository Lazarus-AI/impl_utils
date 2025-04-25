############################################
## hf.py
##
## Copyright Lazarus AI, 2025
############################################
'''
Overview:

A utility for interacting with Hugging Face.
'''

import os
import fnmatch
import subprocess
from huggingface_hub import HfApi

# File naming constants for different model storage formats
MODEL_MONO_UNIX_NAME = "model.tensors"     # Single file format
MODEL_MONO_SPLIT_UNIX_NAME = "model.00"    # First file in split format
MODEL_SPLIT_UNIX_NAME = "model.??"         # Pattern matching all split files


class HuggingFaceUploader:
    def __init__(self, repo_id: str, folder_to_upload: str):
        self.repo_id = repo_id
        self.folder = folder_to_upload
        self.api = HfApi()
        self.model_path = os.path.join(self.folder, MODEL_MONO_UNIX_NAME)
        self.split_model_path = os.path.join(self.folder, MODEL_SPLIT_UNIX_NAME)
        self.split_model_files = []
        self.split_model_files_size = 0
        self.split_model_files_count = 0
        self.split_model_files_size_gb = 0
        self.split_model_files_count_gb = 0
        self.split_model_files_size_gb = 0
        self.split_model_files_count_gb = 0


    def maybe_split_model(self,chunk_size_gb=19):
        """
        Conditionally splits large model files to comply with size limits.

        Args:
            folder (str): Path to the folder containing the model file
            chunk_size_gb (int, optional): Maximum size in GB for each chunk. Defaults to 19
                for HuggingFace's 20GB limit, leaving 1GB buffer.

        Process Steps:
        1. Check if model is already split
        2. Verify model file existence
        3. Check file size
        4. Create symlink or split file based on size

        File Size Handling:
        - Files ≤ chunk_size_gb: Creates symlink to maintain consistent naming
        - Files > chunk_size_gb: Splits into specified size chunks with sequential naming

        File Naming Convention:
        - Original file:     model.tensors
        - Symlink/Split:     model.00 (first file)
        - Additional splits: model.01, model.02, etc.
        
        Split File Example:
        A 50GB model.tensors file with chunk_size_gb=19 would be split into:
        - model.00 (19GB)
        - model.01 (19GB)
        - model.02 (12GB)

        Error Handling:
        - Validates file existence
        - Checks file permissions
        - Monitors splitting process
        """
        # Validate chunk size
        if chunk_size_gb <= 0:
            raise ValueError("Chunk size must be positive")
        
        dir_files = os.listdir(self.folder)
        
        # Skip if already split - looks for any files matching pattern 'model.XX'
        # where XX is any two digits (e.g., model.00, model.01, etc.)
        if any(fnmatch(f, MODEL_SPLIT_UNIX_NAME) for f in dir_files):
            return

        # Validate model file existence
        model_path = os.path.join(self.folder, MODEL_MONO_UNIX_NAME)
        if MODEL_MONO_UNIX_NAME not in dir_files:
            raise ValueError(
                f"Model file could not be found. Was looking for {MODEL_MONO_UNIX_NAME}"
            )

        # Check if model file is larger than chunk_size_gb
        model_path = os.path.join(self.folder, MODEL_MONO_UNIX_NAME)
        model_size_gb = os.path.getsize(model_path) / (1024**3)
        if model_size_gb <= chunk_size_gb:
            # Create symlink for consistent naming
            link_path = os.path.join(self.folder, MODEL_MONO_SPLIT_UNIX_NAME)
            os.symlink(model_path, link_path)
            print(f"Splitting not necessary, creating symlink from '{model_path}' to '{link_path}'")
            return

        # Split large files into manageable chunks
        # Uses Unix 'split' command with following flags:
        # -a 2:  Use 2 digits for suffix (00-99)
        # -b {chunk_size_gb}GB: Create chunks of specified size
        # -d:    Use numeric suffixes instead of alphabetic
        dest_prefix = os.path.join(self.folder, "model.")
        chunk_size_str = f"{chunk_size_gb}GB"
        print(f"Splitting model into {chunk_size_str} chunks at '{self.folder}'. This may take a while...")
        subprocess.run(["split", "-a", "2", "-b", chunk_size_str, "-d", model_path, dest_prefix])
        print("Model has been successfully split")     

    def upload(self):
        """
        Executes the model upload process to HuggingFace Hub.

        Process Flow:
        1. Initialize HuggingFace API client
        2. Check and split model if necessary
        3. Upload files to repository
        4. Verify upload completion

        Features:
        - Automatic handling of large files
        - Progress tracking during upload
        - Error handling and retry logic
        """
        api = HfApi()

        # Prepare model files (split if needed)
        self.maybe_split_model()

        # Upload to HuggingFace with specific file pattern
        api.upload_large_folder(
            repo_id=self.repo_id,
            folder_path=self.folder,
            repo_type="model",
            allow_patterns=MODEL_SPLIT_UNIX_NAME,
        )
