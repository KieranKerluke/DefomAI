"""
Dynamic AI Model Router for DefomAI

This module provides intelligent model selection based on request context,
user preferences, and performance metrics.
"""
"""
Model Router for DefomAI

This module provides intelligent model selection based on request context,
user preferences, and performance metrics.
"""
from typing import Dict, Any, Optional, List, Tuple
import logging
import re
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskType(str, Enum):
    """Different types of tasks that models can handle."""
    CODE = "code"
    CREATIVE = "creative"
    REASONING = "reasoning"
    GENERAL = "general"

@dataclass
class ModelSelection:
    """Represents a model selection result with metadata."""
    model_id: str
    reason: str
    confidence: float
    user_preference_respected: bool
    task_type: Optional[TaskType] = None
    suggested_model: Optional[str] = None

class ModelRouter:
    """
    Handles intelligent routing of requests to the most appropriate AI model
    based on the request content, user preferences, and performance metrics.
    """
    def __init__(self, config, db_client=None):
        self.config = config
        self.db_client = db_client
        
        # Available models
        self.available_models = [
            "openrouter/deepseek/deepseek-chat:free",
            "openrouter/meta-llama/llama-3.1-8b-instruct:free", 
            "openrouter/qwen/qwen3-235b-a22b:free",
            "openrouter/mistralai/mistral-7b-instruct:free"
        ]
        
        # Default model mappings for different task types
        self.model_mappings = {
            TaskType.CODE: "openrouter/deepseek/deepseek-chat:free",
            TaskType.CREATIVE: "openrouter/meta-llama/llama-3.1-8b-instruct:free",
            TaskType.REASONING: "openrouter/qwen/qwen3-235b-a22b:free",
            TaskType.GENERAL: "openrouter/mistralai/mistral-7b-instruct:free"
        }
        
        # Patterns for task detection
        self.task_patterns = {
            TaskType.CODE: [
                r"def\s+\w+\s*\(", 
                r"function\s+\w+\s*\(", 
                r"class\s+\w+",
                r"import\s+\w+", 
                r"from\s+\w+\s+import", 
                r"console\\.log",
                r"print\\(", 
                r"git\s+", 
                r"docker\s+", 
                r"python\s+", 
                r"javascript",
                r"typescript", 
                r"react", 
                r"vue", 
                r"angular", 
                r"html", 
                r"css",
                r"algorithm", 
                r"data structure", 
                r"how to (write|implement|create).*code"
            ],
            TaskType.CREATIVE: [
                r"write (a|an|the)",
                r"story",
                r"poem",
                r"essay",
                r"article",
                r"blog post",
                r"creative"
            ],
            TaskType.REASONING: [
                r"why",
                r"how (does|do|can|should|would|will)",
                r"explain",
                r"analyze",
                r"compare",
                r"contrast",
                r"what are the (pros|cons|advantages|disadvantages)"
            ]
        }
        
        # Initialize performance metrics
        self.model_metrics = {}
        self._initialize_metrics()
        
        # Load model performance data from database if available
        self._load_model_performance()

    def _initialize_metrics(self):
        """Initialize performance metrics for all models."""
        for model_id in set(self.model_mappings.values()):
            self.model_metrics[model_id] = {
                'total_requests': 0,
                'successful_responses': 0,
                'total_latency': 0.0,
                'task_success': {task_type: 0 for task_type in TaskType}
            }
    
    def _load_model_performance(self):
        """Load historical model performance from database."""
        if not self.db_client:
            return
            
        try:
            # This is a placeholder - implement actual database query
            # results = self.db_client.query("SELECT * FROM model_performance")
            # for row in results:
            #     self.model_metrics[row.model_id] = row.metrics
            pass
        except Exception as e:
            logger.error(f"Error loading model performance: {e}")
    
    def _save_model_performance(self, model_id: str, success: bool, latency: float, task_type: TaskType = None):
        """Update and save model performance metrics."""
        if model_id not in self.model_metrics:
            self.model_metrics[model_id] = {
                'total_requests': 0,
                'successful_responses': 0,
                'total_latency': 0.0,
                'task_success': {t: 0 for t in TaskType}
            }
            
        metrics = self.model_metrics[model_id]
        metrics['total_requests'] += 1
        metrics['total_latency'] += latency
        
        if success:
            metrics['successful_responses'] += 1
            if task_type:
                metrics['task_success'][task_type] = metrics['task_success'].get(task_type, 0) + 1
        
        # Save to database in the background
        if self.db_client:
            try:
                # This is a placeholder - implement actual database update
                # self.db_client.execute(
                #     """
                #     INSERT INTO model_performance (model_id, metrics)
                #     VALUES (:model_id, :metrics)
                #     ON CONFLICT (model_id) DO UPDATE
                #     SET metrics = EXCLUDED.metrics
                #     """,
                #     {"model_id": model_id, "metrics": metrics}
                # )
                pass
            except Exception as e:
                logger.error(f"Error saving model performance: {e}")
    
    def _detect_task_type(self, prompt: str) -> Tuple[TaskType, float]:
        """
        Detect the most likely task type for the given prompt.
        
        Returns:
            Tuple of (detected_task_type, confidence_score)
        """
        if not prompt.strip():
            return TaskType.GENERAL, 0.5
            
        prompt_lower = prompt.lower()
        
        # Check for each task type
        task_scores = {}
        
        # Score each task type based on pattern matches
        for task_type, patterns in self.task_patterns.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, prompt_lower, re.IGNORECASE))
            task_scores[task_type] = matches / max(1, len(patterns))
        
        # Get the task with highest score
        if task_scores:
            best_task = max(task_scores.items(), key=lambda x: x[1])
            if best_task[1] > 0.1:  # Minimum confidence threshold
                return best_task
        
        # Default to general if no strong match
        return TaskType.GENERAL, 0.5
    
    def _get_model_performance_ranking(self, task_type: Optional[TaskType] = None) -> List[Dict[str, Any]]:
        """
        Get models ranked by performance for a specific task type.
        
        Args:
            task_type: Optional task type to filter performance
            
        Returns:
            List of models with performance metrics, sorted by success rate
        """
        ranked_models = []
        
        for model_id in self.available_models:
            metrics = self.model_metrics.get(model_id, {
                'total_requests': 0,
                'successful_responses': 0,
                'task_success': {}
            })
            
            # Calculate success rate
            success_rate = (
                metrics['successful_responses'] / metrics['total_requests']
                if metrics['total_requests'] > 0 else 0.5  # Default to 50% for new models
            )
            
            # If task-specific metrics are available, use them
            if task_type and task_type in metrics['task_success']:
                task_requests = sum(metrics['task_success'].values())
                task_success = metrics['task_success'][task_type]
                task_success_rate = task_success / task_requests if task_requests > 0 else success_rate
            else:
                task_success_rate = success_rate
            
            ranked_models.append({
                'model_id': model_id,
                'success_rate': success_rate,
                'task_success_rate': task_success_rate,
                'total_requests': metrics['total_requests']
            })
        
        # Sort by task-specific success rate, then by overall success rate
        return sorted(
            ranked_models,
            key=lambda x: (x['task_success_rate'], x['success_rate'], x['total_requests']),
            reverse=True
        )
    
    async def select_model(
        self,
        prompt: str,
        user_preference: Optional[str] = None,
        lock_preference: bool = False,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Select the best model for the given prompt, considering user preferences.
        
        Implements a unified approach that:
        1. Respects user's locked preference if set
        2. Uses user's preference if provided (but not locked)
        3. Falls back to task-based model suggestion
        4. Ranks available models by performance for the task
        
        Args:
            prompt: User's input text
            user_preference: The model selected by the user (if any)
            lock_preference: Whether to force using the user's selection
            conversation_history: Previous messages in the conversation
            
        Returns:
            Dictionary containing model selection details
        """
        start_time = datetime.utcnow()
        
        try:
            # Level 1: Detect task type for context
            task_type, confidence = self._detect_task_type(prompt)
            
            # Level 2: Get ranked models for this task
            ranked_models = self._get_model_performance_ranking(task_type)
            
            # Level 3: Respect user's locked preference if set
            if lock_preference and user_preference and user_preference in self.available_models:
                return self._create_response(
                    model_id=user_preference,
                    reason="User has locked their model preference",
                    confidence=1.0,
                    user_preference_respected=True,
                    task_type=task_type,
                    start_time=start_time,
                    ranked_models=ranked_models
                )
            
            # Get the suggested model based on task type
            suggested_model = self.model_mappings.get(task_type, self.model_mappings[TaskType.GENERAL])
            
            # Level 4: If user has a preference (but not locked), use it but include suggestion
            if user_preference and user_preference in self.available_models:
                return self._create_response(
                    model_id=user_preference,
                    reason=(
                        f"Using user's preferred model. "
                        f"Recommended: {suggested_model} for {task_type.value} task"
                    ),
                    confidence=0.9,  # High confidence when respecting user choice
                    user_preference_respected=True,
                    task_type=task_type,
                    suggested_model=suggested_model,
                    start_time=start_time,
                    ranked_models=ranked_models
                )
            
            # Level 5: Use the highest ranked model for this task
            best_model = ranked_models[0]['model_id'] if ranked_models else suggested_model
            
            return self._create_response(
                model_id=best_model,
                reason=(
                    f"Task detected as '{task_type.value}' with confidence {confidence:.1f}. "
                    f"Selected best performing model for this task."
                ),
                confidence=confidence,
                user_preference_respected=False,
                task_type=task_type,
                start_time=start_time,
                ranked_models=ranked_models
            )
            
        except Exception as e:
            logger.error(f"Error in model selection: {e}", exc_info=True)
            # Fallback to default model on error
            return self._create_response(
                model_id=self.model_mappings[TaskType.GENERAL],
                reason=f"Error in model selection: {str(e)}",
                confidence=0.1,
                user_preference_respected=False,
                task_type=TaskType.GENERAL,
                start_time=start_time,
                ranked_models=[]
            )
    
    def _create_response(
        self,
        model_id: str,
        reason: str,
        confidence: float,
        user_preference_respected: bool,
        task_type: Optional[TaskType],
        start_time: datetime,
        suggested_model: Optional[str] = None,
        ranked_models: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Helper to create a consistent response format.
        
        Args:
            model_id: The selected model ID
            reason: Explanation for the model selection
            confidence: Confidence score (0.0 to 1.0)
            user_preference_respected: Whether user's preference was followed
            task_type: Detected task type
            start_time: When the selection process started
            suggested_model: The model that was suggested (if different from selected)
            ranked_models: List of all available models ranked by performance
            
        Returns:
            Dictionary with model selection details
        """
        end_time = datetime.utcnow()
        latency = (end_time - start_time).total_seconds()
        
        # Log the model selection
        task_name = getattr(task_type, 'value', 'unknown') if task_type else 'unknown'
        logger.info(
            f"Model selected: {model_id} for task '{task_name}' "
            f"(confidence: {confidence:.2f}, latency: {latency:.3f}s): {reason}"
        )
        
        # Update performance metrics
        self._save_model_performance(
            model_id=model_id,
            success=True,  # Assuming success for now
            latency=latency,
            task_type=task_type
        )
        
        # Prepare the base response
        response = {
            "model_id": model_id,
            "reason": reason,
            "confidence": confidence,
            "user_preference_respected": user_preference_respected,
            "task_type": task_type.value if task_type else None,
            "task_name": task_name,
            "suggested_model": suggested_model,
            "timestamp": end_time.isoformat(),
            "latency_seconds": round(latency, 4),
            "available_models": [
                {
                    "model_id": m['model_id'],
                    "success_rate": round(m['success_rate'], 4),
                    "task_success_rate": round(m.get('task_success_rate', 0), 4),
                    "total_requests": m['total_requests']
                }
                for m in (ranked_models or [])
            ]
        }
        
        # Add model ranking information if available
        if ranked_models:
            try:
                ranked_model_ids = [m['model_id'] for m in ranked_models]
                response['model_rank'] = ranked_model_ids.index(model_id) + 1
                response['total_models_ranked'] = len(ranked_models)
                
                # Add performance comparison if we have more than one model
                if len(ranked_models) > 1:
                    selected_metrics = next(
                        (m for m in ranked_models if m['model_id'] == model_id),
                        None
                    )
                    if selected_metrics:
                        best_model = ranked_models[0]
                        if model_id != best_model['model_id']:
                            response['performance_comparison'] = {
                                "best_model": best_model['model_id'],
                                "relative_performance": round(
                                    selected_metrics['task_success_rate'] / 
                                    best_model['task_success_rate'] * 100, 
                                    1
                                )
                            }
            except Exception as e:
                logger.warning(f"Error adding ranking info to response: {e}")
        
        return response
    
    async def record_feedback(
        self,
        model_id: str,
        prompt: str,
        response: str,
        rating: int,
        feedback: Optional[str] = None,
        task_type: Optional[TaskType] = None
    ) -> bool:
        """
        Record user feedback on model performance.
        
        Args:
            model_id: The model that was used
            prompt: The user's original prompt
            response: The model's response
            rating: User rating (1-5)
            feedback: Optional detailed feedback
            task_type: The detected task type
            
        Returns:
            bool: True if feedback was recorded successfully
        """
        try:
            if self.db_client:
                # This is a placeholder - implement actual database update
                # await self.db_client.execute(
                #     """
                #     INSERT INTO model_feedback 
                #     (model_id, prompt, response, rating, feedback, task_type, created_at)
                #     VALUES (:model_id, :prompt, :response, :rating, :feedback, :task_type, NOW())
                #     """,
                #     {
                #         "model_id": model_id,
                #         "prompt": prompt,
                #         "response": response,
                #         "rating": rating,
                #         "feedback": feedback,
                #         "task_type": task_type.value if task_type else None
                #     }
                # )
                pass
                
            # Update success rate based on rating
            if rating >= 4:  # Consider 4-5 star ratings as successful
                self._save_model_performance(model_id, True, 0, task_type)
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return False
        task_type, rule_confidence = self._rule_based_detection(prompt)
        
        # High confidence rule match
        if rule_confidence > 0.8:
            model = self._get_model_for_task(task_type)
            return ModelSelection(
                model_id=model,
                reason="rule_based_detection",
                confidence=rule_confidence,
                task_type=task_type
            ).__dict__
            
        # Level 3: LLM-based classification if needed
        if rule_confidence < 0.5 or not task_type:
            task_type, llm_confidence = await self._llm_based_classification(prompt)
            model = self._get_model_for_task(task_type)
            
            if user_preference and llm_confidence < 0.7:
                return ModelSelection(
                    model_id=user_preference,
                    reason="user_preference_with_low_confidence_detection",
                    confidence=llm_confidence,
                    task_type=task_type,
                    suggested_model=model
                ).__dict__
                
            return ModelSelection(
                model_id=model,
                reason="llm_based_classification",
                confidence=llm_confidence,
                task_type=task_type
            ).__dict__
            
        # Use rule-based result with suggestion if applicable
        model = self._get_model_for_task(task_type)
        
        if user_preference and user_preference != model and rule_confidence < 0.9:
            return ModelSelection(
                model_id=user_preference,
                reason="user_preference_with_suggestion",
                confidence=rule_confidence,
                task_type=task_type,
                suggested_model=model
            ).__dict__
            
        return ModelSelection(
            model_id=model,
            reason="rule_based_detection",
            confidence=rule_confidence,
            task_type=task_type
        ).__dict__
        
    def _rule_based_detection(self, prompt: str) -> Tuple[Optional[str], float]:
        """
        Detect task type using rule-based patterns.
        
        Returns:
            Tuple of (task_type, confidence_score)
        """
        prompt_lower = prompt.lower()
        
        # Simple keyword matching patterns
        patterns = {
            "code": [
                (r'\b(code|program|function|class|def\s+\w+\s*\(|import\s+\w+|print\()', 0.8),
                (r'\b(html|css|javascript|python|java|c\+\+|c#|go|rust|ruby|php|sql)\b', 0.9),
                (r'\b(debug|fix|error|exception|bug|issue)\b', 0.7),
            ],
            "creative": [
                (r'\b(write|create|compose|story|poem|essay|article|blog|narrative|plot|character)\b', 0.7),
                (r'\b(imagine|describe|what if|suppose|pretend|story about)\b', 0.8),
            ],
            "reasoning": [
                (r'\b(solve|calculate|reason|logic|puzzle|riddle|math|equation|proof|theorem)\b', 0.8),
                (r'\b(why|how|what causes|explain|analyze|compare|contrast|pros and cons)\b', 0.7),
            ],
            "translation": [
                (r'\b(translate|in \w+\s*\?*$|from \w+ to \w+|en français|en español|auf Deutsch|in italiano)\b', 0.9),
            ],
            "summarization": [
                (r'\b(summarize|summary|brief|tl;?dr|too long didn[\'\"]?t read|key points|main ideas)\b', 0.9),
                (r'\b(shorten|condense|simplify|in a nutshell|in brief|in short|to sum up)\b', 0.7),
            ]
        }
        
        # Check each task type pattern
        best_match = (None, 0.0)
        for task_type, task_patterns in patterns.items():
            for pattern, confidence in task_patterns:
                if re.search(pattern, prompt_lower, re.IGNORECASE):
                    if confidence > best_match[1]:
                        best_match = (task_type, confidence)
                        # Early exit if we have high confidence
                        if confidence >= 0.9:
                            return best_match
        
        return best_match

    async def _llm_based_classification(self, prompt: str) -> Tuple[Optional[str], float]:
        """
        Use LLM to classify the task type.
        
        Returns:
            Tuple of (task_type, confidence_score)
        """
        # TODO: Implement actual LLM classification
        # For now, return a default value
        return ("general", 0.7)
    
    def _get_model_for_task(self, task_type: Optional[str]) -> str:
        """Get the recommended model for a given task type."""
        model_mapping = {
            "code": "openrouter/deepseek/deepseek-chat-v3-0324",
            "creative": "openrouter/mistralai/mistral-7b-instruct",
            "reasoning": "openrouter/meta-llama/llama-3.1-8b-instruct",
            "translation": "openrouter/qwen/qwen3-235b-a22b",
            "summarization": "openrouter/mistralai/mistral-7b-instruct"
        }
        return model_mapping.get(task_type or "general", "openrouter/mistralai/mistral-7b-instruct")
    
    def _load_task_models(self) -> Dict[str, Any]:
        """Load task-to-model mapping configuration."""
        # TODO: Load from database or config
        return {}

# Singleton instance
model_router = None

def get_model_router(config: Any, db_client: Any):
    """Get or create the singleton model router instance."""
    global model_router
    if model_router is None:
        model_router = ModelRouter(config, db_client)
    return model_router
