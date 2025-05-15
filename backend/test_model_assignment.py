"""
Model Assignment Verification Tests

This script tests whether the correct AI model is being assigned to each task type
according to the task-to-model assignment table. It verifies that:
1. The correct model is selected for each task type
2. The model actually responds with content appropriate for the task
3. The fallback model is used when specified

Usage:
    python test_model_assignment.py
"""

import asyncio
import re
from typing import Dict, Tuple, List, Optional
from services.llm import make_llm_api_call, get_model_for_task
from utils.config import config

# Task types mapped to their expected models based on the assignment table
TASK_MODEL_MAPPING = {
    "chat": config.MODEL_FOR_CHAT,                           # Mistral 7B Instruct
    "complex_dialogue": config.MODEL_FOR_COMPLEX_DIALOGUE,   # Qwen3 235B
    "summarization": config.MODEL_FOR_SUMMARIZATION,         # LLaMA 3.1 8B
    "code": config.MODEL_FOR_CODE,                           # DeepSeek V3
    "fix_code": config.MODEL_FOR_CODE_FIX,                   # DeepSeek V3
    "math": config.MODEL_FOR_MATH,                           # DeepSeek V3
    "multilingual": config.MODEL_FOR_MULTILINGUAL,           # Qwen3 235B
    "tool_use": config.MODEL_FOR_TOOL_USE,                   # Qwen3 235B
    "fast": config.MODEL_FOR_FAST_RESPONSE,                  # Mistral 7B Instruct
    "complex": config.MODEL_FOR_COMPLEX_TASKS,               # Qwen3 235B or DeepSeek V3
}

# Test prompts for each task type
TEST_PROMPTS = {
    "chat": "Hello, how are you today? Tell me about yourself.",
    "complex_dialogue": "Let's discuss the philosophical implications of artificial consciousness. What are the ethical considerations?",
    "summarization": "Summarize the following text: The Industrial Revolution was a period of major industrialization and innovation during the late 1700s and early 1800s. It began in Great Britain and quickly spread throughout the world, transforming economies from agricultural to industrial and urban-based.",
    "code": "Write a Python function to calculate the Fibonacci sequence up to n terms.",
    "fix_code": "Fix this code: def fibonacci(n):\n    if n == 0: return 0\n    if n == 1: return 1\n    return fibonacci(n+1) + fibonacci(n+2)",
    "math": "Solve this equation step by step: 3x² + 5x - 2 = 0",
    "multilingual": "Translate 'Hello, how are you?' to French, Spanish, and Arabic.",
    "tool_use": "I need to check the weather in Paris. How would you call a weather API to get this information?",
    "fast": "What's the capital of France?",
    "complex": "Explain the legal implications of intellectual property in international trade agreements, focusing on patent law."
}

# Verification patterns to check if the response is appropriate for the task
VERIFICATION_PATTERNS = {
    "chat": r"(hello|hi|greet|pleasure|assist|help)",
    "complex_dialogue": r"(consciousness|philosophy|ethics|implications|consider)",
    "summarization": r"(industrial|revolution|transform|economy|period)",
    "code": r"(def|function|fibonacci|return|for|while)",
    "fix_code": r"(def fibonacci|n-1|n-2|base case|recursion)",
    "math": r"(equation|solve|quadratic|formula|x =|solution)",
    "multilingual": r"(bonjour|hola|مرحبا|translate|french|spanish|arabic)",
    "tool_use": r"(api|call|function|weather|parameter|request)",
    "fast": r"(paris|capital|france)",
    "complex": r"(intellectual property|patent|trade|legal|international|agreement)"
}

async def test_model_assignment(task_type: str, expected_model: str, prompt: str, verification_pattern: str) -> Tuple[bool, bool, str, Optional[str]]:
    """
    Test if the correct model is assigned and responds appropriately for a given task.
    
    Args:
        task_type: The type of task to test
        expected_model: The expected model for this task type
        prompt: The test prompt to send
        verification_pattern: Regex pattern to verify appropriate response
        
    Returns:
        Tuple containing:
        - Whether the correct model was assigned
        - Whether the response was appropriate
        - The actual model used
        - The response content (or None if error)
    """
    print(f"\n--- Testing {task_type} task ---")
    print(f"Expected model: {expected_model}")
    
    try:
        # Get the model that would be assigned for this task type
        assigned_model = get_model_for_task(task_type)
        model_match = assigned_model == expected_model
        
        if not model_match:
            print(f"❌ MODEL MISMATCH: Expected {expected_model}, got {assigned_model}")
            return False, False, assigned_model, None
        
        print(f"✓ Model correctly assigned: {assigned_model}")
        
        # Make the actual API call
        response = await make_llm_api_call(
            task_type=task_type,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        
        actual_model = response.model
        content = response.choices[0].message.content.lower()
        
        # Check if the response matches the expected pattern
        response_match = bool(re.search(verification_pattern.lower(), content))
        
        print(f"Model used: {actual_model}")
        print(f"Response appropriate: {'✓' if response_match else '❌'}")
        print(f"Response snippet: {content[:100]}...")
        
        return model_match, response_match, actual_model, content
    
    except Exception as e:
        print(f"Error testing {task_type}: {str(e)}")
        return False, False, "error", None

async def run_tests() -> Dict[str, Dict[str, any]]:
    """
    Run tests for all task types and collect results.
    
    Returns:
        Dictionary of test results by task type
    """
    results = {}
    
    for task_type, expected_model in TASK_MODEL_MAPPING.items():
        prompt = TEST_PROMPTS.get(task_type, "Test prompt")
        verification_pattern = VERIFICATION_PATTERNS.get(task_type, "")
        
        model_match, response_match, actual_model, content = await test_model_assignment(
            task_type, expected_model, prompt, verification_pattern
        )
        
        results[task_type] = {
            "expected_model": expected_model,
            "actual_model": actual_model,
            "model_match": model_match,
            "response_match": response_match,
            "content_snippet": content[:100] if content else None
        }
    
    return results

def print_results_table(results: Dict[str, Dict[str, any]]) -> None:
    """
    Print a formatted table of test results.
    
    Args:
        results: Dictionary of test results by task type
    """
    print("\n" + "="*100)
    print(f"{'Task Type':<20} | {'Expected Model':<35} | {'Actual Model':<35} | {'Result':<10}")
    print("-"*100)
    
    for task_type, result in results.items():
        expected = result["expected_model"]
        actual = result["actual_model"]
        model_match = result["model_match"]
        response_match = result["response_match"]
        
        if model_match and response_match:
            status = "✅ PASS"
        elif model_match:
            status = "⚠️ PARTIAL"
        else:
            status = "❌ FAIL"
        
        print(f"{task_type:<20} | {expected:<35} | {actual:<35} | {status:<10}")
    
    print("="*100)
    
    # Overall statistics
    total = len(results)
    passed = sum(1 for r in results.values() if r["model_match"] and r["response_match"])
    partial = sum(1 for r in results.values() if r["model_match"] and not r["response_match"])
    failed = total - passed - partial
    
    print(f"\nSummary: {passed}/{total} passed, {partial}/{total} partial, {failed}/{total} failed")
    
    if passed == total:
        print("\n✅ All tests passed! The model assignment is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the model assignments.")

async def main():
    """Main test function."""
    print("\n" + "="*40)
    print("MODEL ASSIGNMENT VERIFICATION TESTS")
    print("="*40)
    
    results = await run_tests()
    print_results_table(results)

if __name__ == "__main__":
    asyncio.run(main())
