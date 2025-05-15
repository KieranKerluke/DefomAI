"""
Test script for task-specific model selection.

This script demonstrates how to use the task-specific model selection
to automatically choose the right model for different tasks.
"""

import asyncio
from services.llm import make_llm_api_call
from utils.config import config

async def test_task_model(task_type, prompt):
    """Test a specific task with the appropriate model."""
    print(f"\n--- Testing {task_type} task ---")
    try:
        response = await make_llm_api_call(
            task_type=task_type,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150  # Keep token count low for free tier
        )
        print(f"Model used: {response.model}")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"Error testing {task_type}: {str(e)}")
        return False

async def main():
    """Test various task types with appropriate models."""
    print("Testing task-specific model selection...")
    
    # Define tasks to test with appropriate prompts
    tasks = [
        ("chat", "Hello, how are you today?"),
        ("complex_dialogue", "Let's discuss the implications of quantum computing on modern cryptography."),
        ("summarization", "Summarize the following text: The Industrial Revolution was a period of major industrialization and innovation that took place during the late 1700s and early 1800s. The Industrial Revolution began in Great Britain and quickly spread throughout the world. The American Industrial Revolution commonly referred to as the Second Industrial Revolution, started sometime between 1820 and 1870."),
        ("code", "Write a Python function to calculate the Fibonacci sequence."),
        ("fix_code", "Fix this code: def fibonacci(n):\n    if n == 0: return 0\n    if n == 1: return 1\n    return fibonacci(n+1) + fibonacci(n+2)"),
        ("math", "Solve this equation: 3x + 5 = 14"),
        ("multilingual", "Translate 'Hello, how are you?' to French, Spanish, and Arabic."),
        ("tool_use", "Call an API to get the weather for Paris."),
        ("fast", "Give me a quick answer about the capital of France."),
        ("complex", "Explain the legal implications of intellectual property in international trade agreements.")
    ]
    
    results = {}
    
    # Test each task type
    for task_type, prompt in tasks:
        results[task_type] = await test_task_model(task_type, prompt)
    
    # Print summary
    print("\n--- Test Summary ---")
    for task_type, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{task_type}: {status}")
    
    if all(results.values()):
        print("\n✅ All task-specific models tested successfully!")
    else:
        print("\n❌ Some task-specific model tests failed!")

if __name__ == "__main__":
    asyncio.run(main())
