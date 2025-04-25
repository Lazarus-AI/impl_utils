import torch
from vllm import LLM, SamplingParams
from vllm.utils import cleanup_dist_env_and_memory

def terminate_llm(llm: LLM) -> None:
    """
    Properly terminate the vLLM instance and clean up resources.
    """
    print("## Terminating vLLM...")
    
    # First ensure all CUDA operations are complete
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    
    # Clean up the model executor
    if hasattr(llm, 'llm_engine') and hasattr(llm.llm_engine, 'model_executor'):
        del llm.llm_engine.model_executor
    
    # Delete the LLM instance
    del llm
    
    # Clean up distributed environment
    cleanup_dist_env_and_memory()
    
    # Final CUDA sync to ensure all operations are complete
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.empty_cache()
    
    print("## ... vLLM terminated successfully")

def test_prompts(llm: LLM, prompts: list[str]) -> None:
    """
    Test the vLLM model with the given prompts.
    """
    try:    
        sampling_params = SamplingParams(
            temperature=0.7,
            top_p=0.95,
            max_tokens=100
        )
    
        print("## Running inference with vLLM...")
        outputs = llm.generate(prompts, sampling_params)
        
        print("\n## vLLM Test Results:")
        for prompt, output in zip(prompts, outputs):
            print("\nPrompt:", prompt)
            print("Response:", output.outputs[0].text)
            print("-" * 50)
        
    except Exception as e:
        print(f"## Error during vLLM testing: {str(e)}")
        raise
    
    print("## vLLM testing completed successfully")


def test_prompts_from_file(llm: LLM, file_path: str) -> None:
    """
    Test the vLLM model with the prompts in the given file.
    """
    with open(file_path, 'r') as file:
        prompts = file.readlines()
    test_prompts(llm, prompts)