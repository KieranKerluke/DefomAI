"""
Test script for OpenRouter models.

This script tests the OpenRouter models configured in the LLM service.
"""

import asyncio
from services.llm import make_llm_api_call, DEFAULT_OPENROUTER_MODELS

async def test_model(model_name):
    """Test a specific model with a simple query."""
    print(f"\n--- Testing {model_name} ---")
    try:
        response = await make_llm_api_call(
            model_name=model_name,
            messages=[{"role": "user", "content": "Hello, what can you do for me?"}],
            temperature=0.7,
            max_tokens=100
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
    
    results = {}
    
    # Test each model
    for name, model in DEFAULT_OPENROUTER_MODELS.items():
        print(f"\nTesting {name} model: {model}")
        results[name] = await test_model(model)
    
    # Print summary
    print("\n--- Test Summary ---")
    for name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{name}: {status}")
    
    if all(results.values()):
        print("\n✅ All OpenRouter models tested successfully!")
    else:
        print("\n❌ Some OpenRouter model tests failed!")

if __name__ == "__main__":
    asyncio.run(main())
