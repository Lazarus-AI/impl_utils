import json
import os

# use the impl_utils toolkit to query the Rikai2 API
from lazarus_implementation_tools.models.utils import query_rikai2

def infer_rikai2(prompt: str, 
                 file_path_or_url: str, 
                 url: str = os.environ["RIKAI2_URL"], 
                 org_id: str = os.environ["RIKAI2_ORG_ID"], 
                 auth_key: str = os.environ["RIKAI2_AUTH_KEY"], 
                 webhook: str = os.environ["WEBHOOK_URL"]
                 ) -> str:
    """
    Process a document using the Rikai2 API and return the extracted answer.
    This is a synchronous function that will block until the document is processed.
    
    Args:
        prompt (str): The prompt/question to ask about the document
        file_path_or_url (str): The path to the document being processed.
            - If the document is a local file path, it will be processed locally.
            - If the document is a cloud URL, the file will be downloaded and processed locally.
        url (str): The URL of the Rikai2 API. Defaults to the value of the RIKAI2_URL environment variable.
        org_id (str): The organization ID for the Rikai2 API. Defaults to the value of the RIKAI2_ORG_ID environment variable.
        auth_key (str): The authentication key for the Rikai2 API. Defaults to the value of the RIKAI2_AUTH_KEY environment variable.
        webhook (str): The webhook that will be called when the document is processed. Defaults to the value of the WEBHOOK_URL environment variable.
    Returns:
        str: The extracted answer from the document processing
    """
    
    # Query Rikai2 API with document and prompt
    model_api_list = query_rikai2(file_path_or_url=file_path_or_url, 
                        prompt=prompt, 
                        url=url, 
                        org_id=org_id, 
                        auth_key=auth_key,
                        webhook=webhook)
    
    # Get the path to the results file from the first API response
    results_file = model_api_list[0].return_file_path
    
    # Read and parse the JSON results file
    with open(results_file, "r") as f:
        the_json = json.load(f)
        # Extract the answer from the nested JSON structure
        return the_json["data"][0]["answer"]