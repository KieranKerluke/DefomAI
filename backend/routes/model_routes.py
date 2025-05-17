"""
Model selection and feedback API endpoints.

This module provides endpoints for intelligent model selection and feedback collection
to improve AI model routing based on task type and performance metrics.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, validator

from utils.model_router.router import get_model_router, TaskType
from utils.config import config
from services.supabase import get_db_client

# Set up logging
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/model", tags=["model"])

class ModelSuggestionRequest(BaseModel):
    """
    Request model for getting model suggestions.
    
    This endpoint analyzes the input and suggests the most appropriate AI model
    based on the content and context of the prompt, while respecting user preferences.
    """
    prompt: str = Field(
        ...,
        description="The user's input text that will be processed by the AI model"
    )
    user_preference: Optional[str] = Field(
        None,
        description=(
            "The model ID that the user has selected as their preference. "
            "This will be used unless lock_preference is False and a better model is detected."
        ),
        examples=["openrouter/mistralai/mistral-7b-instruct:free"]
    )
    lock_preference: bool = Field(
        False,
        description=(
            "If True, the user's preferred model will always be used. "
            "If False, the system may suggest a different model if it's more suitable."
        )
    )
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        None,
        description=(
            "Previous messages in the conversation for better context understanding. "
            "Each message should have 'role' (user/assistant) and 'content' fields."
        )
    )
    user_id: Optional[str] = Field(
        None,
        description="Optional user ID for personalization and tracking"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "How do I implement quicksort in Python?",
                "user_preference": "openrouter/mistralai/mistral-7b-instruct",
                "lock_preference": False,
                "conversation_history": []
            }
        }

class ModelFeedbackRequest(BaseModel):
    """Request model for submitting model feedback."""
    model_id: str = Field(..., description="The model that was used")
    prompt: str = Field(..., description="The user's original prompt")
    response: str = Field(..., description="The model's response")
    rating: int = Field(
        ..., 
        ge=1, 
        le=5, 
        description="User rating (1-5) of the model's performance"
    )
    feedback: Optional[str] = Field(
        None, 
        description="Optional detailed feedback about the response"
    )
    task_type: Optional[str] = Field(
        None, 
        description="The detected task type if known"
    )
    
    @validator('task_type')
    def validate_task_type(cls, v):
        if v is not None and v not in [t.value for t in TaskType]:
            raise ValueError(f"Invalid task type. Must be one of: {[t.value for t in TaskType]}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "model_id": "openrouter/mistralai/mistral-7b-instruct",
                "prompt": "How do I implement quicksort in Python?",
                "response": "Here's how to implement quicksort in Python...",
                "rating": 5,
                "feedback": "The implementation was clear and efficient.",
                "task_type": "code"
            }
        }

class ModelPerformance(BaseModel):
    """Performance metrics for a specific model."""
    model_id: str = Field(..., description="The model identifier")
    success_rate: float = Field(..., description="Overall success rate (0.0 to 1.0)")
    task_success_rate: Optional[float] = Field(
        None,
        description="Success rate for the specific task type if available"
    )
    total_requests: int = Field(..., description="Total number of requests served by this model")

class ModelSuggestionResponse(BaseModel):
    """
    Detailed response for model suggestions including performance metrics and ranking.
    """
    # Core selection information
    model_id: str = Field(..., description="The selected model ID that should be used")
    reason: str = Field(..., description="Human-readable explanation for the model selection")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the selection (0.0 to 1.0)"
    )
    
    # Context information
    task_type: Optional[str] = Field(
        None,
        description="The detected task type (e.g., 'code', 'creative', 'reasoning')"
    )
    task_name: Optional[str] = Field(
        None,
        description="Human-readable name of the detected task type"
    )
    
    # User preference handling
    user_preference_respected: bool = Field(
        ...,
        description="Whether the user's preference was followed"
    )
    suggested_model: Optional[str] = Field(
        None,
        description="The model that was suggested by the system if different from selected"
    )
    
    # Performance information
    model_rank: Optional[int] = Field(
        None,
        description="Ranking of the selected model (1 being best)"
    )
    total_models_ranked: Optional[int] = Field(
        None,
        description="Total number of models that were ranked"
    )
    performance_comparison: Optional[Dict[str, Any]] = Field(
        None,
        description="Comparison with the best performing model if not selected"
    )
    
    # System information
    timestamp: str = Field(..., description="ISO 8601 timestamp of when the response was generated")
    latency_seconds: float = Field(..., description="Time taken to generate the response in seconds")
    
    # Available models with performance metrics
    available_models: List[ModelPerformance] = Field(
        ...,
        description="List of all available models with their performance metrics"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the model selection"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "model_id": "openrouter/mistralai/mistral-7b-instruct:free",
                "reason": "Selected based on task type and performance",
                "confidence": 0.92,
                "task_type": "code",
                "task_name": "Code Generation",
                "user_preference_respected": True,
                "suggested_model": "openrouter/deepseek/deepseek-chat:free",
                "model_rank": 2,
                "total_models_ranked": 4,
                "performance_comparison": {
                    "best_model": "openrouter/deepseek/deepseek-chat:free",
                    "relative_performance": 95.5
                },
                "timestamp": "2025-05-17T20:15:30.123456Z",
                "latency_seconds": 0.123,
                "available_models": [
                    {
                        "model_id": "openrouter/deepseek/deepseek-chat:free",
                        "success_rate": 0.95,
                        "task_success_rate": 0.97,
                        "total_requests": 1500
                    },
                    {
                        "model_id": "openrouter/mistralai/mistral-7b-instruct:free",
                        "success_rate": 0.93,
                        "task_success_rate": 0.92,
                        "total_requests": 2000
                    },
                    {
                        "model_id": "openrouter/meta-llama/llama-3.1-8b-instruct:free",
                        "success_rate": 0.89,
                        "task_success_rate": 0.85,
                        "total_requests": 1800
                    },
                    {
                        "model_id": "openrouter/qwen/qwen3-235b-a22b:free",
                        "success_rate": 0.91,
                        "task_success_rate": 0.88,
                        "total_requests": 1200
                    }
                ],
                "metadata": {
                    "version": "1.0.0",
                    "model_selection_strategy": "performance_based"
                }
            }
        }

@router.post(
    "/suggest",
    response_model=ModelSuggestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get model suggestion for a prompt",
    description="""
    Analyze the given prompt and conversation context to suggest the most 
    appropriate AI model to use for generating a response.
    
    This endpoint considers:
    - The content and context of the prompt
    - The user's model preference (if any)
    - Historical performance of models on similar tasks
    - The specific requirements of the detected task type
    
    The response includes detailed information about why a particular model
    was selected and how it compares to other available models.
    """
)
async def suggest_model(
    request: Request,
    suggestion_request: ModelSuggestionRequest,
    db_client = Depends(get_db_client)
) -> ModelSuggestionResponse:
    """
    Suggest an optimal model for the given prompt and context.
    
    This endpoint analyzes the prompt and returns the most appropriate
    AI model to use, along with detailed reasoning and performance metrics.
    
    Args:
        request: The HTTP request object
        suggestion_request: Contains the prompt and user preferences
        db_client: Database client for storing/retrieving model metrics
        
    Returns:
        ModelSuggestionResponse with detailed model selection information
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    start_time = datetime.utcnow()
    
    try:
        # Initialize model router with configuration and database client
        router = get_model_router(config, db_client)
        
        # Get model suggestion based on prompt and user preferences
        result = await router.select_model(
            prompt=suggestion_request.prompt,
            user_preference=suggestion_request.user_preference,
            lock_preference=suggestion_request.lock_preference,
            conversation_history=suggestion_request.conversation_history
        )
        
        # Add additional metadata to the response
        result['metadata'] = {
            'version': '1.0.0',
            'model_selection_strategy': 'performance_based',
            'user_id': suggestion_request.user_id,
            'request_id': str(uuid.uuid4()),
            'endpoint': str(request.url)
        }
        
        # Log the model selection for analytics
        if db_client:
            try:
                await db_client.table('model_selection_logs').insert({
                    'request_id': result['metadata']['request_id'],
                    'user_id': suggestion_request.user_id,
                    'selected_model': result['model_id'],
                    'suggested_model': result.get('suggested_model'),
                    'task_type': result.get('task_type'),
                    'confidence': result['confidence'],
                    'user_preference_respected': result['user_preference_respected'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'user_agent': request.headers.get('user-agent'),
                    'ip_address': request.client.host if request.client else None
                }).execute()
            except Exception as db_error:
                logger.error(f"Error logging model selection: {db_error}")
        
        return result
        
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.error(f"Error in model suggestion (ID: {error_id}): {str(e)}", exc_info=True)
        
        # Log the error for debugging
        if db_client:
            try:
                await db_client.table('model_selection_errors').insert({
                    'error_id': error_id,
                    'user_id': suggestion_request.user_id,
                    'error_message': str(e),
                    'timestamp': datetime.utcnow().isoformat(),
                    'user_agent': request.headers.get('user-agent'),
                    'ip_address': request.client.host if request.client else None,
                    'request_data': {
                        'prompt_preview': (suggestion_request.prompt or '')[:500],
                        'user_preference': suggestion_request.user_preference,
                        'lock_preference': suggestion_request.lock_preference
                    }
                }).execute()
            except Exception as log_error:
                logger.error(f"Failed to log error {error_id}: {log_error}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Failed to process model suggestion',
                'error_id': error_id,
                'message': 'An internal error occurred while selecting the model.'
            }
        )

@router.post(
    "/feedback",
    status_code=status.HTTP_200_OK,
    summary="Submit feedback about model performance",
    description="""
    Record user feedback about the quality of a model's response.
    This helps improve future model selection.
    """
)
async def model_feedback(
    request: Request,
    feedback_request: ModelFeedbackRequest,
    db_client = Depends(get_db_client)
) -> Dict[str, Any]:
    """
    Submit feedback about model performance for a given prompt.
    
    This feedback is used to improve future model selection.
    """
    try:
        router = get_model_router(config, db_client)
        
        # Record the feedback
        success = await router.record_feedback(
            model_id=feedback_request.model_id,
            prompt=feedback_request.prompt,
            response=feedback_request.response,
            rating=feedback_request.rating,
            feedback=feedback_request.feedback,
            task_type=TaskType(feedback_request.task_type) if feedback_request.task_type else None
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record feedback"
            )
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording feedback: {str(e)}"
        )

# Include these routes in your main FastAPI app
# from .routes import model_routes
# app.include_router(model_routes.router, prefix="/api")
