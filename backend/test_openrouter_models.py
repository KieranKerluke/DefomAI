"""
Test script for OpenRouter models.

This script tests the OpenRouter models configured in the LLM service.
"""

import asyncio
import os
from services.llm import make_llm_api_call
from utils.config import config

async def test_model(model_name, prompt="What can you tell me about yourself?"):
    """Test a specific model with a simple query."""
    print(f"\n--- Testing {model_name} ---")
    try:
        response = await make_llm_api_call(
            model_name=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")
        return True
    except Exception as e:
        print(f"Error testing {model_name}: {str(e)}")
        return False

async def main():
    """Test all configured OpenRouter models."""
    print("Testing OpenRouter models...")
    
    # Check if OpenRouter API key is set
    if not config.OPENROUTER_API_KEY:
        print("⚠️ WARNING: OPENROUTER_API_KEY is not set in environment variables.")
        print("Set it before running this test.")
        return
    
    # Models to test - using free versions
    models = [
        config.OPENROUTER_DEEPSEEK_MODEL,  # deepseek/deepseek-chat:free
        config.OPENROUTER_LLAMA_MODEL,     # meta-llama/llama-3.1-8b-instruct:free
        config.OPENROUTER_QWEN_MODEL,      # qwen/qwen3-235b-a22b:free
        config.OPENROUTER_MISTRAL_MODEL    # mistralai/mistral-7b-instruct:free
    ]
    
    results = {}
    
    # Test each model
    for model in models:
        results[model] = await test_model(model)
    
    # Print summary
    print("\n--- Test Summary ---")
    for model, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{model}: {status}")
    
    if all(results.values()):
        print("\n✅ All OpenRouter models tested successfully!")
    else:
        print("\n❌ Some OpenRouter model tests failed!")

if __name__ == "__main__":
    asyncio.run(main())
