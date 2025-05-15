"""
Model Self-Identification Test

This script tests whether AI models correctly identify themselves according to the
task-to-model assignment table. It sends a specific prompt to each model asking it
to identify itself, and then verifies if the response matches the expected model.

Usage:
    python test_model_self_identification.py
"""

import asyncio
import re
from typing import Dict, Tuple, List, Optional
from services.llm import make_llm_api_call, get_model_for_task
from utils.config import config

# Task types mapped to their expected models based on the assignment table
TASK_MODEL_MAPPING = {
    "chat": {
        "expected_model": config.MODEL_FOR_CHAT,
        "model_name": "Mistral 7B Instruct",
        "reason": "Fast, low-latency, low cost, trained for instruction use"
    },
    "complex_dialogue": {
        "expected_model": config.MODEL_FOR_COMPLEX_DIALOGUE,
        "model_name": "Qwen3 235B",
        "reason": "Strong long-term memory and instruction alignment"
    },
    "summarization": {
        "expected_model": config.MODEL_FOR_SUMMARIZATION,
        "model_name": "LLaMA 3.1 8B",
        "reason": "128K context, optimized for instruction + summarization"
    },
    "code": {
        "expected_model": config.MODEL_FOR_CODE,
        "model_name": "DeepSeek V3",
        "reason": "Highest score on code benchmarks, handles logic well"
    },
    "fix_code": {
        "expected_model": config.MODEL_FOR_CODE_FIX,
        "model_name": "DeepSeek V3",
        "reason": "Strong on logic, can debug and explain code"
    },
    "math": {
        "expected_model": config.MODEL_FOR_MATH,
        "model_name": "DeepSeek V3",
        "reason": "Best in class for mathematical and logical reasoning"
    },
    "multilingual": {
        "expected_model": config.MODEL_FOR_MULTILINGUAL,
        "model_name": "Qwen3 235B",
        "reason": "Supports 100+ languages, strong cross-lingual QA"
    },
    "tool_use": {
        "expected_model": config.MODEL_FOR_TOOL_USE,
        "model_name": "Qwen3 235B",
        "reason": "Optimized for function calling, tool use, agent planning"
    },
    "fast": {
        "expected_model": config.MODEL_FOR_FAST_RESPONSE,
        "model_name": "Mistral 7B Instruct",
        "reason": "Lightweight and quick, good for first-pass inference"
    },
    "complex": {
        "expected_model": config.MODEL_FOR_COMPLEX_TASKS,
        "model_name": "Qwen3 235B or DeepSeek V3",
        "reason": "For reasoning + context + detail"
    }
}

# Self-identification prompt template
SELF_ID_PROMPT = """
You are an AI assistant. Based on your architecture and capabilities, identify which of the following models you are:

1. Mistral 7B Instruct - Fast, low-latency, low cost, trained for instruction use
2. Qwen3 235B - Strong long-term memory and instruction alignment
3. LLaMA 3.1 8B - 128K context, optimized for instruction + summarization
4. DeepSeek V3 - Highest score on code benchmarks, handles logic well

Please respond with ONLY the model name (e.g., "Mistral 7B Instruct") and nothing else. Do not include explanations, introductions, or any other text.
"""

async def test_model_self_identification(task_type: str, task_info: Dict) -> Tuple[bool, str, str]:
    """
    Test if a model correctly identifies itself when asked.
    
    Args:
        task_type: The type of task to test
        task_info: Dictionary containing expected model info
        
    Returns:
        Tuple containing:
        - Whether the model correctly identified itself
        - The actual model used according to API
        - The model's self-identification response
    """
    print(f"\n--- Testing {task_type} task ---")
    expected_model = task_info["expected_model"]
    expected_name = task_info["model_name"]
    reason = task_info["reason"]
    
    print(f"Expected model: {expected_model}")
    print(f"Expected name: {expected_name}")
    print(f"Reason: {reason}")
    
    try:
        # Make the API call with the self-identification prompt
        response = await make_llm_api_call(
            task_type=task_type,
            messages=[{"role": "user", "content": SELF_ID_PROMPT}],
            temperature=0,  # Use 0 temperature for consistent responses
            max_tokens=50   # Short response expected
        )
        
        actual_model = response.model
        content = response.choices[0].message.content.strip()
        
        # Clean up the response to handle potential formatting issues
        content = re.sub(r'^[0-9.)\s]+', '', content)  # Remove numbering
        content = content.replace('**', '').replace('*', '').strip()  # Remove markdown
        
        # Check if the model identified itself correctly
        # We'll do a flexible match since models might respond in different formats
        model_patterns = {
            "Mistral 7B Instruct": r"(mistral|7b|instruct)",
            "Qwen3 235B": r"(qwen|235b)",
            "LLaMA 3.1 8B": r"(llama|3\.1|8b)",
            "DeepSeek V3": r"(deepseek|v3)"
        }
        
        # Extract the expected model name (before "or" if there are alternatives)
        primary_expected = expected_name.split(" or ")[0].strip()
        
        # Check if the response contains the expected model pattern
        pattern = model_patterns.get(primary_expected, "")
        match = bool(re.search(pattern, content.lower())) if pattern else False
        
        print(f"Model used (API): {actual_model}")
        print(f"Model self-identified as: {content}")
        print(f"Self-identification correct: {'✓' if match else '❌'}")
        
        return match, actual_model, content
    
    except Exception as e:
        print(f"Error testing {task_type}: {str(e)}")
        return False, "error", f"Error: {str(e)}"

async def run_tests() -> Dict[str, Dict[str, any]]:
    """
    Run self-identification tests for all task types and collect results.
    
    Returns:
        Dictionary of test results by task type
    """
    results = {}
    
    for task_type, task_info in TASK_MODEL_MAPPING.items():
        match, actual_model, content = await test_model_self_identification(task_type, task_info)
        
        results[task_type] = {
            "expected_model": task_info["expected_model"],
            "expected_name": task_info["model_name"],
            "actual_model": actual_model,
            "self_id_response": content,
            "match": match
        }
    
    return results

def print_results_table(results: Dict[str, Dict[str, any]]) -> None:
    """
    Print a formatted table of test results.
    
    Args:
        results: Dictionary of test results by task type
    """
    print("\n" + "="*120)
    print(f"{'Task Type':<20} | {'Expected Model':<30} | {'API Model':<30} | {'Self-ID':<20} | {'Result':<10}")
    print("-"*120)
    
    for task_type, result in results.items():
        expected_name = result["expected_name"]
        actual_model = result["actual_model"]
        self_id = result["self_id_response"][:20]  # Truncate for display
        match = result["match"]
        
        status = "✅ PASS" if match else "❌ FAIL"
        
        print(f"{task_type:<20} | {expected_name:<30} | {actual_model:<30} | {self_id:<20} | {status:<10}")
    
    print("="*120)
    
    # Overall statistics
    total = len(results)
    passed = sum(1 for r in results.values() if r["match"])
    failed = total - passed
    
    print(f"\nSummary: {passed}/{total} passed, {failed}/{total} failed")
    
    if passed == total:
        print("\n✅ All tests passed! Models correctly identify themselves.")
    else:
        print("\n⚠️ Some tests failed. Models may not be correctly identifying themselves.")

async def main():
    """Main test function."""
    print("\n" + "="*40)
    print("MODEL SELF-IDENTIFICATION TESTS")
    print("="*40)
    
    results = await run_tests()
    print_results_table(results)

if __name__ == "__main__":
    asyncio.run(main())
