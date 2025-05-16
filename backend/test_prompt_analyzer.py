"""
Prompt Analyzer Test

This script tests the prompt analyzer's ability to automatically select the most appropriate
model based on the content of a user prompt. It sends various test prompts to the analyzer
and reports which model was selected for each prompt.

Usage:
    python test_prompt_analyzer.py
"""

import asyncio
import json
from typing import Dict, List, Any
from utils.prompt_analyzer import analyze_prompt_and_select_model
from utils.config import config
from utils.logger import logger
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Test prompts covering different task categories
TEST_PROMPTS = [
    # Chat prompts
    "What's the weather like today?",
    "Tell me a joke about programming.",
    "What's the capital of France?",
    
    # Code prompts
    "Write a Python function to calculate the Fibonacci sequence.",
    "Create a React component that displays a list of items with pagination.",
    "How do I fix this error in my JavaScript code: Uncaught TypeError: Cannot read property 'length' of undefined",
    
    # Math prompts
    "Solve the equation: 3x^2 + 2x - 5 = 0",
    "What is the derivative of f(x) = x^3 + 2x^2 - 4x + 7?",
    "If I have 5 red balls, 3 blue balls, and 2 green balls in a bag, what's the probability of drawing a red ball?",
    
    # Multilingual prompts
    "Translate this text to French: 'Hello, how are you?'",
    "¿Cómo puedo aprender español rápidamente?",
    "日本語を勉強するための最良の方法は何ですか？",
    
    # Tool use prompts
    "Create a function that calls the OpenAI API to generate images.",
    "How do I set up a webhook to receive Stripe payment notifications?",
    "Write a script that fetches data from a REST API and saves it to a CSV file.",
    
    # Complex prompts
    "Research the impact of quantum computing on modern cryptography.",
    "Analyze the pros and cons of different renewable energy sources.",
    "Explain the legal implications of using AI-generated content in commercial applications."
]

# Expected task types for each prompt (for validation)
EXPECTED_CATEGORIES = [
    # Chat prompts
    "chat", "chat", "chat",
    
    # Code prompts
    "code", "code", "fix_code",
    
    # Math prompts
    "math", "math", "math",
    
    # Multilingual prompts
    "multilingual", "multilingual", "multilingual",
    
    # Tool use prompts
    "tool_use", "tool_use", "tool_use",
    
    # Complex prompts
    "complex", "complex", "complex"
]

async def test_prompt_analyzer():
    """Run tests for the prompt analyzer with various prompts."""
    results = []
    
    print("\n" + "="*80)
    print("PROMPT ANALYZER TEST")
    print("="*80)
    
    for i, prompt in enumerate(TEST_PROMPTS):
        expected_category = EXPECTED_CATEGORIES[i]
        print(f"\n--- Test {i+1}: {expected_category.upper()} ---")
        print(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt: {prompt}")
        
        try:
            # Analyze the prompt and get the selected model
            selected_model = await analyze_prompt_and_select_model(prompt)
            
            # Determine which task category this model corresponds to
            task_category = "unknown"
            for category, info in {
                "chat": config.MODEL_FOR_CHAT,
                "complex_dialogue": config.MODEL_FOR_COMPLEX_DIALOGUE,
                "summarization": config.MODEL_FOR_SUMMARIZATION,
                "code": config.MODEL_FOR_CODE,
                "fix_code": config.MODEL_FOR_CODE_FIX,
                "math": config.MODEL_FOR_MATH,
                "multilingual": config.MODEL_FOR_MULTILINGUAL,
                "tool_use": config.MODEL_FOR_TOOL_USE,
                "fast": config.MODEL_FOR_FAST_RESPONSE,
                "complex": config.MODEL_FOR_COMPLEX_TASKS
            }.items():
                if selected_model == info:
                    task_category = category
                    break
            
            # Check if the selected category matches the expected category
            match = task_category == expected_category
            status = "✅ PASS" if match else "❌ FAIL"
            
            print(f"Selected model: {selected_model}")
            print(f"Detected category: {task_category}")
            print(f"Expected category: {expected_category}")
            print(f"Result: {status}")
            
            results.append({
                "prompt": prompt,
                "selected_model": selected_model,
                "detected_category": task_category,
                "expected_category": expected_category,
                "match": match
            })
            
        except Exception as e:
            print(f"Error: {str(e)}")
            results.append({
                "prompt": prompt,
                "error": str(e),
                "match": False
            })
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for r in results if r.get("match", False))
    accuracy = (passed / total) * 100 if total > 0 else 0
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Accuracy: {accuracy:.2f}%")
    
    if passed == total:
        print("\n✅ All tests passed! The prompt analyzer is working correctly.")
    else:
        print("\n⚠️ Some tests failed. The prompt analyzer may need improvement.")

if __name__ == "__main__":
    asyncio.run(test_prompt_analyzer())
