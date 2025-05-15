"""
Test script for OpenRouter models.

This script tests the OpenRouter models configured in the LLM service.
"""

import asyncio
from services.llm import make_llm_api_call, DEFAULT_OPENROUTER_MODELS

async def test_openrouter():
    """Test the OpenRouter integration with a simple query."""
    test_messages = [
        {"role": "user", "content": "Hello, can you give me a quick test response?"}
    ]

    try:
        # Test with deepseek model
        print("\n--- Testing deepseek model ---")
        response = await make_llm_api_call(
            model_name="openrouter/deepseek/deepseek-chat:free",
            messages=test_messages,
            temperature=0.7,
            max_tokens=100
        )
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")

        # Test with Llama 3.1 model
        print("\n--- Testing Llama 3.1 model ---")
        response = await make_llm_api_call(
            model_name="openrouter/meta-llama/llama-3.1-8b-instruct:free",
            messages=test_messages,
            temperature=0.7,
            max_tokens=100
        )
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")

        # Test with Qwen model
        print("\n--- Testing Qwen model ---")
        response = await make_llm_api_call(
            model_name="openrouter/qwen/qwen3-235b-a22b:free",
            messages=test_messages,
            temperature=0.7,
            max_tokens=100
        )
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")

        # Test with Mistral model
        print("\n--- Testing Mistral model ---")
        response = await make_llm_api_call(
            model_name="openrouter/mistralai/mistral-7b-instruct:free",
            messages=test_messages,
            temperature=0.7,
            max_tokens=100
        )
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")

        return True
    except Exception as e:
        print(f"Error testing OpenRouter: {str(e)}")
        return False

async def main():
    """Test the OpenRouter integration."""
    print("Testing OpenRouter...")
    result = await test_openrouter()
    if result:
        print("\n✅ OpenRouter integration tested successfully!")
    else:
        print("\n❌ OpenRouter integration test failed!")

if __name__ == "__main__":
    asyncio.run(main())
