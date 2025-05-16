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
    "complex": "Research, detailed analysis, legal tasks, or specialized knowledge",
    "weather": "Weather forecasts, current conditions, or climate information",
    "data_analysis": "Analyzing, visualizing, or interpreting data and statistics",
    "creative": "Creative writing, storytelling, or content generation"
}

async def analyze_prompt_and_select_model(prompt: str) -> str:
    """
    Use a fast model to analyze the prompt and determine the best model to use.
    Also applies rule-based pattern matching for precise model selection.
    
    Args:
        prompt: The user's input prompt
        
    Returns:
        The appropriate model name for this prompt
    """
    # First, try rule-based pattern matching for precise detection
    task_type = rule_based_task_detection(prompt)
    if task_type:
        logger.info(f"Rule-based detection classified prompt as '{task_type}'")
        return get_model_for_task(task_type)
    
    # If rule-based detection didn't work, use the LLM for classification
    logger.info("Using LLM for prompt classification")
    
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
- For weather forecasts or current conditions, use 'weather'
- For data analysis or visualization tasks, use 'data_analysis'
- For creative writing or content generation, use 'creative'

Specific pattern matching:
- If the prompt contains phrases like "weather", "temperature", "forecast", "sunny", "rainy", "cloudy", or city names followed by "weather", classify as 'weather'
- If the prompt asks about code debugging or fixing errors, classify as 'fix_code' not 'code'
- If the prompt contains phrases like "write a function", "code", "program", "algorithm", "implement", or mentions programming languages like "Python", "JavaScript", "Java", "C++", classify as 'code'
- If the prompt asks to create, write, or implement any kind of function, algorithm, or program, classify as 'code'

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

def rule_based_task_detection(prompt: str) -> str:
    """
    Apply rule-based pattern matching to precisely detect the task type.
    
    Args:
        prompt: The user's input prompt
        
    Returns:
        The detected task type or None if no clear match
    """
    prompt_lower = prompt.lower()
    
    # Code detection patterns
    code_patterns = [
        "write a function", "create a function", "implement a function",
        "write a program", "create a program", "implement a program",
        "write an algorithm", "create an algorithm", "implement an algorithm",
        "write code", "generate code", "code example",
        "in python", "in javascript", "in java", "in c++", "in typescript",
        "function that", "class that", "algorithm for", "code for",
        "programming", "software development", "coding"
    ]
    
    # Code fixing patterns
    code_fix_patterns = [
        "debug", "fix", "error", "not working", "doesn't work", "isn't working",
        "bug", "issue", "problem with", "fix the code", "improve the code",
        "optimize", "refactor", "clean up", "improve performance",
        "code review", "review this code"
    ]
    
    # Math patterns
    math_patterns = [
        "solve", "equation", "calculate", "computation", "formula",
        "math", "mathematics", "arithmetic", "algebra", "calculus",
        "trigonometry", "geometry", "statistics", "probability",
        "x =", "y =", "find the value", "compute", "evaluate",
        "factorial", "logarithm", "exponent", "square root", "derivative",
        "integral", "summation", "product", "series", "function"
    ]
    
    # Weather patterns
    weather_patterns = [
        "weather", "temperature", "forecast", "humidity", "precipitation",
        "sunny", "rainy", "cloudy", "snowy", "windy", "storm", "climate",
        "meteorological", "atmospheric", "weather in", "weather for",
        "weather forecast", "weather report", "weather update",
        "how hot", "how cold", "will it rain", "will it snow"
    ]
    
    # Summarization patterns
    summarization_patterns = [
        "summarize", "summary", "summarization", "condense", "shorten",
        "tldr", "brief overview", "key points", "main ideas", "gist",
        "synopsis", "abstract", "executive summary", "recap", "outline"
    ]
    
    # Multilingual patterns
    multilingual_patterns = [
        "translate", "translation", "in spanish", "in french", "in german",
        "in chinese", "in japanese", "in russian", "in arabic", "in hindi",
        "from english to", "from spanish to", "language", "linguistic",
        "grammar", "vocabulary", "phrase", "idiom", "expression"
    ]
    
    # Tool use patterns
    tool_use_patterns = [
        "api", "function call", "tool", "integration", "connect to",
        "fetch data", "retrieve data", "get data from", "use the api",
        "database", "query", "request", "endpoint", "service",
        "webhook", "automation", "workflow", "pipeline"
    ]
    
    # Complex dialogue patterns
    complex_dialogue_patterns = [
        "conversation", "dialogue", "discussion", "debate", "argument",
        "negotiation", "interview", "consultation", "counseling", "therapy",
        "roleplay", "scenario", "situation", "case study", "hypothetical"
    ]
    
    # Data analysis patterns
    data_analysis_patterns = [
        "analyze data", "data analysis", "visualization", "chart", "graph",
        "plot", "dashboard", "metrics", "kpi", "analytics", "insights",
        "trends", "patterns", "correlations", "regression", "clustering",
        "classification", "prediction", "forecast", "projection"
    ]
    
    # Creative patterns
    creative_patterns = [
        "story", "poem", "essay", "article", "blog post", "content",
        "creative", "imaginative", "fiction", "narrative", "tale",
        "write a story", "write a poem", "write an essay", "write an article",
        "generate content", "content creation", "copywriting"
    ]
    
    # Market research patterns
    market_research_patterns = [
        "market research", "market analysis", "industry analysis", "competitive analysis",
        "market size", "market share", "market trends", "market growth",
        "competitor analysis", "swot analysis", "pestle analysis", "porter's five forces",
        "analyze the market", "research the industry", "market report", "industry report",
        "market overview", "industry overview", "market landscape", "industry landscape",
        "market players", "key players", "major companies", "competitors",
        "market opportunities", "market challenges", "market threats", "market drivers",
        "market forecast", "market projection", "market outlook", "industry outlook",
        "generate report", "create report", "pdf report", "market pdf"
    ]
    
    # Check for code fixing first (more specific than code)
    for pattern in code_fix_patterns:
        if pattern in prompt_lower:
            return "fix_code"
    
    # Check for code
    for pattern in code_patterns:
        if pattern in prompt_lower:
            return "code"
    
    # Check for math
    for pattern in math_patterns:
        if pattern in prompt_lower:
            return "math"
    
    # Check for weather
    for pattern in weather_patterns:
        if pattern in prompt_lower:
            return "weather"
    
    # Check for summarization
    for pattern in summarization_patterns:
        if pattern in prompt_lower:
            return "summarization"
    
    # Check for multilingual
    for pattern in multilingual_patterns:
        if pattern in prompt_lower:
            return "multilingual"
    
    # Check for tool use
    for pattern in tool_use_patterns:
        if pattern in prompt_lower:
            return "tool_use"
    
    # Check for complex dialogue
    for pattern in complex_dialogue_patterns:
        if pattern in prompt_lower:
            return "complex_dialogue"
    
    # Check for data analysis
    for pattern in data_analysis_patterns:
        if pattern in prompt_lower:
            return "data_analysis"
    
    # Check for creative
    for pattern in creative_patterns:
        if pattern in prompt_lower:
            return "creative"
            
    # Check for market research
    for pattern in market_research_patterns:
        if pattern in prompt_lower:
            return "market_research"
    
    # No clear match found
    return None

async def test_prompt_analyzer():
    """Test function for the prompt analyzer."""
    test_prompts = [
        "What's the weather like today?",
        "Write a Python function to calculate the factorial of a number.",
        "Solve this equation: 3x^2 + 5x - 2 = 0",
        "Translate this sentence to French: 'Hello, how are you?'",
        "Can you help me analyze this sales data and create a visualization?",
        "What are the latest developments in quantum computing?",
        "Summarize this article for me.",
        "Can you help me debug this code?",
        "Use the API to fetch the latest stock prices.",
        "Tell me a joke."
    ]
    
    print("\n=== PROMPT ANALYZER TEST ===\n")
    for prompt in test_prompts:
        # Test rule-based detection first
        rule_based_result = rule_based_task_detection(prompt)
        print(f"Prompt: {prompt}")
        print(f"Rule-based detection: {rule_based_result}")
        
        # Test full model selection
        model = await analyze_prompt_and_select_model(prompt)
        print(f"Selected model: {model}\n")
    
    print("=== TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_prompt_analyzer())
