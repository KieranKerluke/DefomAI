"""
Prompt Analyzer for Model Selection

This module provides functionality to analyze user prompts and automatically select
the most appropriate AI model based on the content and requirements of the prompt.
It uses a lightweight model to classify the prompt into different task categories,
then maps those categories to specialized models.
"""

import asyncio
from typing import Dict, Any, Optional, List
import logging

from services.llm import make_llm_api_call, get_model_for_task
from utils.config import config
from utils.logger import logger

# Classification categories and their descriptions
TASK_CATEGORIES = {
    "chat": "General conversation, simple Q&A, basic information requests",
    "complex_dialogue": "Deep multi-turn conversations requiring memory and context",
    "summarization": "Summarizing or condensing content, extracting key points",
    "code": "Writing, generating, or explaining code in any programming language",
    "fix_code": "Debugging, refactoring, or improving existing code",
    "math": "Mathematical calculations, equations, logic problems, or reasoning",
    "multilingual": "Non-English content, translation tasks, or language analysis",
    "tool_use": "Tasks requiring tools, APIs, function calls, or structured outputs",
    "complex": "Research, detailed analysis, legal tasks, or specialized knowledge"
}

async def analyze_prompt_and_select_model(prompt: str) -> str:
    """
    Use a fast model to analyze the prompt and determine the best model to use.
    
    Args:
        prompt: The user's input prompt
        
    Returns:
        The appropriate model name for this prompt
    """
    # Use the fast model (Mistral 7B) for analysis
    analysis_model = config.MODEL_FOR_FAST_RESPONSE
    
    # Create a detailed system prompt for accurate classification
    categories_text = "\n".join([f"- {cat}: {desc}" for cat, desc in TASK_CATEGORIES.items()])
    
    system_message = {
        "role": "system", 
        "content": f"""You are a prompt classifier that analyzes user inputs to determine the most appropriate AI model to use.
        
Analyze the following user prompt and classify it into exactly ONE of these categories:
{categories_text}

Consider these guidelines:
- For simple questions or casual conversation, use 'chat'
- For programming tasks or code generation, use 'code'
- For mathematical or logical reasoning, use 'math'
- For non-English content or translation, use 'multilingual'
- For tasks requiring structured outputs or API calls, use 'tool_use'
- For complex research or detailed analysis, use 'complex'

Respond with ONLY the category name and nothing else. No explanations or additional text."""
    }
    
    user_message = {"role": "user", "content": prompt}
    
    try:
        # Make the API call with the classification prompt
        response = await make_llm_api_call(
            model_name=analysis_model,
            messages=[system_message, user_message],
            temperature=0,  # Use 0 temperature for consistent classification
            max_tokens=20   # Short response expected
        )
        
        # Extract the task type from the response
        task_type = response.choices[0].message.content.strip().lower()
        
        # Clean up response to handle potential formatting issues
        task_type = task_type.replace("'", "").replace("\"", "").replace(".", "").strip()
        
        # Log the classification result
        logger.info(f"Prompt classified as '{task_type}' task type")
        
        # Validate that the task type is one of our known categories
        if task_type not in TASK_CATEGORIES:
            logger.warning(f"Unknown task type '{task_type}', falling back to default model")
            return config.DEFAULT_MODEL
        
        # Get the appropriate model for this task type
        selected_model = get_model_for_task(task_type)
        logger.info(f"Selected model '{selected_model}' for task type '{task_type}'")
        
        return selected_model
        
    except Exception as e:
        logger.error(f"Error in prompt analysis: {str(e)}")
        # Fall back to default model if analysis fails
        return config.DEFAULT_MODEL

async def get_last_user_message(client, thread_id: str) -> Optional[str]:
    """
    Retrieve the last user message from a thread.
    
    Args:
        client: Database client
        thread_id: ID of the thread to get the message from
        
    Returns:
        The content of the last user message, or None if not found
    """
    try:
        # Query the database for the last user message in the thread
        result = await client.table('messages').select('content').eq('thread_id', thread_id).eq('type', 'user').order('created_at', desc=True).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            # Parse the message content from JSON
            import json
            message_data = json.loads(result.data[0]['content'])
            return message_data.get('content', '')
        
        return None
    except Exception as e:
        logger.error(f"Error retrieving last user message: {str(e)}")
        return None

# For testing purposes
async def test_prompt_analyzer():
    """Test the prompt analyzer with various types of prompts."""
    test_prompts = [
        "What's the weather like today?",
        "Write a Python function to calculate Fibonacci numbers",
        "Solve this equation: 3x^2 + 2x - 5 = 0",
        "Translate this text to French: 'Hello, how are you?'",
        "Create a function that calls the OpenAI API to generate images",
        "Research the impact of quantum computing on cryptography"
    ]
    
    print("\n=== PROMPT ANALYZER TEST ===")
    for prompt in test_prompts:
        model = await analyze_prompt_and_select_model(prompt)
        print(f"\nPrompt: {prompt[:50]}...")
        print(f"Selected model: {model}")
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_prompt_analyzer())
