"""
LLM API interface for making calls to various language models.

This module provides a unified interface for making API calls to different LLM providers
(OpenAI, Anthropic, Groq, etc.) using LiteLLM. It includes support for:
- Streaming responses
- Tool calls and function calling
- Retry logic with exponential backoff
- Model-specific configurations
- Comprehensive error handling and logging
"""

from typing import Union, Dict, Any, Optional, AsyncGenerator, List
import os
import json
import asyncio
from openai import OpenAIError
import litellm
from utils.logger import logger
from utils.config import config
from utils.model_prices import register_custom_model_prices
from datetime import datetime
import traceback

# Constants
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 30
RETRY_DELAY = 5

# litellm.set_verbose=True
litellm.modify_params=True

# Default OpenRouter models from config
DEFAULT_OPENROUTER_MODELS = {
    "deepseek": config.OPENROUTER_DEEPSEEK_MODEL,
    "llama": config.OPENROUTER_LLAMA_MODEL,
    "qwen": config.OPENROUTER_QWEN_MODEL,
    "mistral": config.OPENROUTER_MISTRAL_MODEL
}

# Default model to use when none is specified
DEFAULT_MODEL = config.DEFAULT_MODEL

# Constants
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 30
RETRY_DELAY = 5

class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass

class LLMRetryError(LLMError):
    """Exception raised when retries are exhausted."""
    pass

def setup_api_keys() -> None:
    """Set up API keys from environment variables."""
    # We're only using OpenRouter now
    if config.OPENROUTER_API_KEY:
        logger.debug("OpenRouter API key is set")
        
        # Set up OpenRouter API base if configured
        if config.OPENROUTER_API_BASE:
            os.environ['OPENROUTER_API_BASE'] = config.OPENROUTER_API_BASE
            logger.debug(f"Set OPENROUTER_API_BASE to {config.OPENROUTER_API_BASE}")
    else:
        logger.warning("No OpenRouter API key found - LLM functionality will not work properly")

async def handle_error(error: Exception, attempt: int, max_attempts: int) -> None:
    """Handle API errors with appropriate delays and logging."""
    delay = RATE_LIMIT_DELAY if isinstance(error, litellm.exceptions.RateLimitError) else RETRY_DELAY
    logger.warning(f"Error on attempt {attempt + 1}/{max_attempts}: {str(error)}")
    logger.debug(f"Waiting {delay} seconds before retry...")
    await asyncio.sleep(delay)

def get_model_for_task(task_type: str) -> str:
    """
    Select the appropriate model based on the task type.
    
    Args:
        task_type: The type of task to perform (chat, code, summarization, etc.)
        
    Returns:
        The full model path for the appropriate model for this task
    """
    task_type = task_type.lower()
    logger.info(f"Selecting model for task type: {task_type}")
    
    # Basic conversation
    if task_type in ['chat', 'conversation', 'qa', 'question']:
        logger.info(f"Using chat model: {config.MODEL_FOR_CHAT}")
        return config.MODEL_FOR_CHAT
        
    # Complex dialogue
    elif task_type in ['complex_dialogue', 'deep_conversation', 'multi_turn']:
        logger.info(f"Using complex dialogue model: {config.MODEL_FOR_COMPLEX_DIALOGUE}")
        return config.MODEL_FOR_COMPLEX_DIALOGUE
        
    # Summarization
    elif task_type in ['summarize', 'summarization', 'summary']:
        logger.info(f"Using summarization model: {config.MODEL_FOR_SUMMARIZATION}")
        return config.MODEL_FOR_SUMMARIZATION
        
    # Code generation
    elif task_type in ['code', 'coding', 'programming', 'generate_code']:
        logger.info(f"Using code model: {config.MODEL_FOR_CODE}")
        return config.MODEL_FOR_CODE
        
    # Code fixing
    elif task_type in ['fix_code', 'debug', 'refactor']:
        logger.info(f"Using code fix model: {config.MODEL_FOR_CODE_FIX}")
        return config.MODEL_FOR_CODE_FIX
        
    # Math reasoning
    elif task_type in ['math', 'logic', 'reasoning', 'calculation']:
        logger.info(f"Using math model: {config.MODEL_FOR_MATH}")
        return config.MODEL_FOR_MATH
        
    # Multilingual
    elif task_type in ['multilingual', 'translation', 'language']:
        logger.info(f"Using multilingual model: {config.MODEL_FOR_MULTILINGUAL}")
        return config.MODEL_FOR_MULTILINGUAL
        
    # Tool use
    elif task_type in ['tool_use', 'api', 'function_call', 'agent']:
        logger.info(f"Using tool use model: {config.MODEL_FOR_TOOL_USE}")
        return config.MODEL_FOR_TOOL_USE
        
    # Fast responses
    elif task_type in ['fast', 'quick', 'lightweight']:
        logger.info(f"Using fast response model: {config.MODEL_FOR_FAST_RESPONSE}")
        return config.MODEL_FOR_FAST_RESPONSE
        
    # Complex tasks
    elif task_type in ['complex', 'research', 'detailed', 'legal']:
        logger.info(f"Using complex tasks model: {config.MODEL_FOR_COMPLEX_TASKS}")
        return config.MODEL_FOR_COMPLEX_TASKS
        
    # Weather questions - Use tool-optimized model
    elif task_type in ['weather', 'forecast', 'temperature']:
        logger.info(f"Using weather model (tool-optimized): {config.MODEL_FOR_TOOL_USE}")
        return config.MODEL_FOR_TOOL_USE
        
    # Data analysis - Use math-optimized model
    elif task_type in ['data_analysis', 'data', 'statistics', 'visualization']:
        logger.info(f"Using data analysis model: {config.MODEL_FOR_MATH}")
        return config.MODEL_FOR_MATH
        
    # Creative tasks - Use summarization model (good at text generation)
    elif task_type in ['creative', 'writing', 'story', 'content']:
        logger.info(f"Using creative writing model: {config.MODEL_FOR_SUMMARIZATION}")
        return config.MODEL_FOR_SUMMARIZATION
        
    # Default fallback
    else:
        logger.info(f"No specific model for task type '{task_type}', using default: {config.DEFAULT_MODEL}")
        return config.DEFAULT_MODEL

def get_openrouter_model(model_name: str) -> str:
    """
    Map model names to OpenRouter models or return the original if it's already an OpenRouter model.
    
    This function allows users to specify a simple model name like "deepseek" and get the full OpenRouter path.
    If the model name already starts with "openrouter/", it's returned as is.
    """
    if model_name.startswith("openrouter/"):
        return model_name
        
    # Check if it's one of our default models
    if model_name in DEFAULT_OPENROUTER_MODELS:
        return DEFAULT_OPENROUTER_MODELS[model_name]
    
    # If it's a known provider but not fully qualified, prepend openrouter/
    known_providers = ["deepseek", "meta-llama", "qwen", "mistralai"]
    for provider in known_providers:
        if model_name.startswith(f"{provider}/"):
            return f"openrouter/{model_name}"
    
    # If not found, return the default model
    logger.warning(f"Unknown model: {model_name}, using default: {DEFAULT_MODEL}")
    return DEFAULT_MODEL

def prepare_params(
    messages: List[Dict[str, Any]],
    model_name: str = DEFAULT_MODEL,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    response_format: Optional[Any] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    stream: bool = False,
    top_p: Optional[float] = None,
    model_id: Optional[str] = None,
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = 'low'
) -> Dict[str, Any]:
    """Prepare parameters for the API call."""
    # Map to OpenRouter model if needed
    model_name = get_openrouter_model(model_name)
    
    params = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "response_format": response_format,
        "top_p": top_p,
        "stream": stream,
    }

    if api_key:
        params["api_key"] = api_key
    if api_base:
        params["api_base"] = api_base
    if model_id:
        params["model_id"] = model_id

    # Handle token limits
    # For free tier, we need to be careful about token limits
    # Default to a reasonable limit if not specified
    if max_tokens is None:
        # Set a conservative default for free tier (2000 tokens)
        max_tokens = 2000
        logger.debug(f"No max_tokens specified, using default of {max_tokens} for free tier")
    else:
        # Cap max_tokens to a reasonable limit for free tier
        if max_tokens > 4000:
            logger.warning(f"Requested max_tokens {max_tokens} exceeds free tier recommendation, capping at 4000")
            max_tokens = 4000
            
    # Set the max_tokens parameter
    params["max_tokens"] = max_tokens

    # Add tools if provided
    if tools:
        params.update({
            "tools": tools,
            "tool_choice": tool_choice
        })
        logger.debug(f"Added {len(tools)} tools to API parameters")

    # Add OpenRouter-specific parameters
    if model_name.startswith("openrouter/"):
        logger.debug(f"Preparing OpenRouter parameters for model: {model_name}")

        # Add optional site URL and app name from config
        site_url = config.OR_SITE_URL
        app_name = config.OR_APP_NAME
        if site_url or app_name:
            extra_headers = params.get("extra_headers", {})
            if site_url:
                extra_headers["HTTP-Referer"] = site_url
            if app_name:
                extra_headers["X-Title"] = app_name
            params["extra_headers"] = extra_headers
            logger.debug(f"Added OpenRouter site URL and app name to headers")

    # No Anthropic-specific code needed anymore
    return params

async def make_llm_api_call(
    messages: List[Dict[str, Any]] = None,
    model_name: str = DEFAULT_MODEL,
    task_type: Optional[str] = None,
    response_format: Optional[Any] = None,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    stream: bool = False,
    top_p: Optional[float] = None,
    model_id: Optional[str] = None,
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = 'low'
) -> Union[Dict[str, Any], AsyncGenerator]:
    """
    Make an API call to a language model using LiteLLM with OpenRouter.

    Args:
        messages: List of message dictionaries for the conversation
        model_name: Name of the model to use (e.g., "deepseek", "llama", "qwen", "mistral",
                   or full paths like "openrouter/deepseek/deepseek-chat")
        task_type: Type of task being performed, which will automatically select the optimal model.
                  Options include: 'chat', 'complex_dialogue', 'summarization', 'code', 'fix_code',
                  'math', 'multilingual', 'tool_use', 'fast', 'complex'.
                  If provided, this overrides the model_name parameter.
        response_format: Desired format for the response
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in the response
        tools: List of tool definitions for function calling
        tool_choice: How to select tools ("auto" or "none")
        api_key: Override default API key
        api_base: Override default API base URL
        stream: Whether to stream the response
        top_p: Top-p sampling parameter
        model_id: Optional model ID (not used with OpenRouter)
        enable_thinking: Whether to enable thinking (not used with OpenRouter)
        reasoning_effort: Level of reasoning effort (not used with OpenRouter)

    Returns:
        Union[Dict[str, Any], AsyncGenerator]: API response or stream

    Raises:
        LLMRetryError: If API call fails after retries
        LLMError: For other API-related errors
    """
    # Set default messages if none provided
    if messages is None:
        messages = [{"role": "user", "content": "Hello, can you give me a quick test response?"}]
    
    # If task_type is provided, select the appropriate model for the task
    if task_type is not None:
        task_specific_model = get_model_for_task(task_type)
        logger.info(f"Task type '{task_type}' detected, using model: {task_specific_model}")
        model_name = task_specific_model
        
    # debug <timestamp>.json messages
    logger.info(f"Making LLM API call to model: {model_name} (Thinking: {enable_thinking}, Effort: {reasoning_effort})")
    logger.info(f"📡 API Call: Using model {model_name}")
    params = prepare_params(
        messages=messages,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        tools=tools,
        tool_choice=tool_choice,
        api_key=api_key,
        api_base=api_base,
        stream=stream,
        top_p=top_p,
        model_id=model_id,
        enable_thinking=enable_thinking,
        reasoning_effort=reasoning_effort
    )
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            logger.debug(f"Attempt {attempt + 1}/{MAX_RETRIES}")
            # logger.debug(f"API request parameters: {json.dumps(params, indent=2)}")

            response = await litellm.acompletion(**params)
            logger.debug(f"Successfully received API response from {model_name}")
            logger.debug(f"Response: {response}")
            return response

        except (litellm.exceptions.RateLimitError, OpenAIError, json.JSONDecodeError) as e:
            last_error = e
            await handle_error(e, attempt, MAX_RETRIES)

        except Exception as e:
            logger.error(f"Unexpected error during API call: {str(e)}", exc_info=True)
            raise LLMError(f"API call failed: {str(e)}")

    error_msg = f"Failed to make API call after {MAX_RETRIES} attempts"
    if last_error:
        error_msg += f". Last error: {str(last_error)}"
    logger.error(error_msg, exc_info=True)
    raise LLMRetryError(error_msg)

# Initialize API keys and register custom model pricing on module import
setup_api_keys()
register_custom_model_prices()

# Test code for OpenRouter integration
async def test_openrouter():
    """Test the OpenRouter integration with a simple query."""
    test_messages = [
        {"role": "user", "content": "Hello, can you give me a quick test response?"}
    ]

    try:
        # Test with deepseek model
        print("\n--- Testing deepseek model ---")
        response = await make_llm_api_call(
            model_name="openrouter/deepseek/deepseek-chat",
            messages=test_messages,
            temperature=0.7,
            max_tokens=100
        )
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")

        # Test with Llama 3.1 model
        print("\n--- Testing Llama 3.1 model ---")
        response = await make_llm_api_call(
            model_name="openrouter/meta-llama/llama-3.1-8b-instruct",
            messages=test_messages,
            temperature=0.7,
            max_tokens=100
        )
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")

        # Test with Qwen model
        print("\n--- Testing Qwen model ---")
        response = await make_llm_api_call(
            model_name="openrouter/qwen/qwen3-235b-a22b",
            messages=test_messages,
            temperature=0.7,
            max_tokens=100
        )
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")

        # Test with Mistral model
        print("\n--- Testing Mistral model ---")
        response = await make_llm_api_call(
            model_name="openrouter/mistralai/mistral-7b-instruct",
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

# Bedrock testing removed as we're only using OpenRouter models now

async def test_all_openrouter_models():
    """Test all the specified OpenRouter models."""
    models = [
        "openrouter/deepseek/deepseek-chat:free",
        "openrouter/meta-llama/llama-3.1-8b-instruct:free",
        "openrouter/qwen/qwen3-235b-a22b:free",
        "openrouter/mistralai/mistral-7b-instruct:free"
    ]
    
    test_messages = [
        {"role": "user", "content": "Hello, can you give me a quick test response?"}
    ]
    
    results = {}
    
    for model in models:
        try:
            print(f"\n--- Testing {model} ---")
            response = await make_llm_api_call(
                model_name=model,
                messages=test_messages,
                temperature=0.7,
                max_tokens=100
            )
            print(f"Response: {response.choices[0].message.content}")
            print(f"Model used: {response.model}")
            results[model] = True
        except Exception as e:
            print(f"Error testing {model}: {str(e)}")
            results[model] = False
    
    return all(results.values())

if __name__ == "__main__":
    import asyncio

    # Test OpenRouter models instead of Bedrock
    test_success = asyncio.run(test_all_openrouter_models())

    if test_success:
        print("\n✅ All OpenRouter models tested successfully!")
    else:
        print("\n❌ Some OpenRouter model tests failed!")
