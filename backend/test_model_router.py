"""
Test script for the model router.
"""
import asyncio
import httpx
import json

async def test_model_selection():
    """Test the model selection endpoint."""
    url = "https://defomai-backend-production.up.railway.app/api/model/suggest"
    
    test_cases = [
        {
            "name": "Code example",
            "prompt": "How do I write a Python function to sort a list?"
        },
        {
            "name": "Creative writing",
            "prompt": "Write a short story about a robot learning to love"
        },
        {
            "name": "Math problem",
            "prompt": "What is the square root of 144?"
        },
        {
            "name": "Translation",
            "prompt": "Translate 'Hello, how are you?' to French"
        },
        {
            "name": "Summarization",
            "prompt": "Summarize the following text: " + 
                     """The Industrial Revolution was a period of major industrialization """ +
                     """that took place during the late 1700s and early 1800s. This period """ +
                     """saw the mechanization of agriculture and textile manufacturing and a """ +
                     """revolution in power, including steam ships and railroads, that """ +
                     """affected social, cultural and economic conditions."""
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for test in test_cases:
            print(f"\n{'='*50}")
            print(f"Test: {test['name']}")
            print(f"Prompt: {test['prompt']}")
            
            response = await client.post(
                url,
                json={
                    "prompt": test["prompt"],
                    "user_id": "test_user_123",
                    "lock_preference": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Status: {result['status']}")
                print(f"Selected model: {result['data']['model_id']}")
                print(f"Reason: {result['data']['reason']}")
                print(f"Confidence: {result['data']['confidence']:.2f}")
                if 'suggested_model' in result['data'] and result['data']['suggested_model']:
                    print(f"Suggested model: {result['data']['suggested_model']}")
            else:
                print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(test_model_selection())
