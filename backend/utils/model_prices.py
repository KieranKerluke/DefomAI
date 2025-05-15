"""
Custom model pricing configuration for LiteLLM.

This module provides pricing information for OpenRouter models that aren't 
included in the default LiteLLM pricing configuration.
"""

from typing import Dict, Any
import litellm

# Define pricing for OpenRouter models (all set to zero since they're free)
CUSTOM_MODEL_PRICES = {
    # DeepSeek model
    "openrouter/deepseek/deepseek-chat-v3-0324:free": {
        "input_cost_per_token": 0.0,  # Free
        "output_cost_per_token": 0.0,  # Free
        "context_window": 32768,
    },
    # LLaMA model
    "openrouter/meta-llama/llama-3.1-8b-instruct:free": {
        "input_cost_per_token": 0.0,  # Free
        "output_cost_per_token": 0.0,  # Free
        "context_window": 128000,
    },
    # Qwen model
    "openrouter/qwen/qwen3-235b-a22b:free": {
        "input_cost_per_token": 0.0,  # Free
        "output_cost_per_token": 0.0,  # Free
        "context_window": 128000,
    },
    # Mistral model
    "openrouter/mistralai/mistral-7b-instruct:free": {
        "input_cost_per_token": 0.0,  # Free
        "output_cost_per_token": 0.0,  # Free
        "context_window": 32768,
    },
}

def register_custom_model_prices():
    """
    Register custom model pricing with LiteLLM.
    
    This function adds pricing information for OpenRouter models that
    aren't included in the default LiteLLM pricing configuration.
    """
    for model_name, pricing in CUSTOM_MODEL_PRICES.items():
        litellm.register_model(
            model=model_name,
            model_info=pricing
        )
