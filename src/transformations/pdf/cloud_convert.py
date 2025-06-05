import logging
import os
import shutil

import cloudconvert
import requests

from config import CLOUD_CONVERT_API_KEY
from general.core import log_timing

logger = logging.getLogger(__name__)

# This is the cloud convert method for converting a director to pdfs
# You'll need to set the API key in the .env file before using.
# If you don't want the file to leave your system consider using
# the libre office converter
@log_timing
def convert_directory_to_pdfs(source_dir, dest_dir):
    """
    Converts all files in the source directory to PDFs using the CloudConvert API.
    The resulting PDFs are saved in the destination directory, preserving the directory structure.

    :param source_dir: The path to the source directory containing the original files.
    :param dest_dir: The path to the destination directory where PDFs will be saved.
    """
    api_key = CLOUD_CONVERT_API_KEY
    cloudconvert.configure(api_key=api_key, sandbox=False)

    # List of supported input formats
    supported_formats = ["doc", "docx", "xlsx", "xls", "ppt", "pptx", "txt"]

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for root, dirs, files in os.walk(source_dir):
        rel_path = os.path.relpath(root, source_dir)
        dest_root = os.path.join(dest_dir, rel_path)
        if not os.path.exists(dest_root):
            os.makedirs(dest_root)

        for file in files:
            input_file_path = os.path.join(root, file)
            filename, ext = os.path.splitext(file)
            input_format = ext[1:].lower()  # Remove leading '.' and convert to lowercase
            output_format = "pdf"
            dest_file = f"{filename}.pdf"
            dest_file_path = os.path.join(dest_root, dest_file)

            # Skip if the file is already converted
            if os.path.exists(dest_file_path):
                continue

            if input_format == "pdf":
                try:
                    shutil.copy2(input_file_path, dest_file_path)
                    logging.info(f"Copied PDF {input_file_path} to {dest_file_path}")
                except Exception as e:
                    logging.info(f"Failed to copy PDF {input_file_path}: {e}")
                continue

            # Skip unsupported file formats
            if input_format not in supported_formats:
                logging.info(f"Skipping unsupported file format: {input_file_path}")
                continue

            try:
                # Create a job with import/upload, convert, and export/url tasks
                job = cloudconvert.Job.create(
                    payload={
                        "tasks": {
                            "import-my-file": {"operation": "import/upload"},
                            "convert-my-file": {
                                "operation": "convert",
                                "input": "import-my-file",
                                "input_format": input_format,
                                "output_format": output_format,
                                # Removed 'engine' parameter for flexibility
                            },
                            "export-my-file": {
                                "operation": "export/url",
                                "input": "convert-my-file",
                            },
                        }
                    }
                )

                # Get the import task
                import_task = next(
                    (task for task in job["tasks"] if task["name"] == "import-my-file"),
                    None,
                )
                if not import_task:
                    logging.info(f"Failed to find import task for {input_file_path}")
                    continue

                # Upload the file
                upload_task = cloudconvert.Task.find(id=import_task["id"])
                upload_url = upload_task["result"]["form"]["url"]
                form_data = upload_task["result"]["form"]["parameters"]
                with open(input_file_path, "rb") as file_stream:
                    files = {"file": file_stream}
                    response = requests.post(upload_url, data=form_data, files=files)
                    response.raise_for_status()

                # Wait for the job to complete
                job = cloudconvert.Job.wait(id=job["id"])

                # Get the export task
                export_task = next(
                    (
                        task
                        for task in job["tasks"]
                        if task["name"] == "export-my-file" and task["status"] == "finished"
                    ),
                    None,
                )
                if not export_task:
                    logging.info(f"Failed to find export task for {input_file_path}")
                    continue

                # Get the file URL from the export task
                file_url = export_task["result"]["files"][0]["url"]

                # Download the converted file
                with requests.get(file_url, stream=True) as r:
                    r.raise_for_status()
                    with open(dest_file_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                logging.info(f"Converted {input_file_path} to {dest_file_path}")
            except Exception as e:
                logging.info(f"Failed to convert {input_file_path}: {e}")
    logging.info("Conversion process completed.")
