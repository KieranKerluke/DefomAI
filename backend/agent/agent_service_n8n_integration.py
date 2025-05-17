"""
Agent Service n8n Integration

This module demonstrates how to integrate the n8n agent handler
with the main agent service.
"""

import logging
from typing import Dict, Any, List, Optional

from agent.n8n_agent_handler import N8nAgentHandler

logger = logging.getLogger(__name__)

def integrate_n8n_with_agent_service(agent_service):
    """
    Integrate n8n workflow capabilities with the agent service.
    
    Args:
        agent_service: The agent service to integrate with
        
    Returns:
        Updated agent service with n8n capabilities
    """
    # Create the n8n agent handler
    n8n_handler = N8nAgentHandler(agent_service)
    
    # Store the original process_message method
    original_process_message = agent_service.process_message
    
    # Define the new process_message method with n8n integration
    def process_message_with_n8n(message, conversation_history=None, **kwargs):
        """
        Process a message with n8n integration.
        
        Args:
            message: User message
            conversation_history: Conversation history
            **kwargs: Additional arguments
            
        Returns:
            Agent response
        """
        # Check if the message requires n8n workflow automation
        n8n_result = n8n_handler.process_message(message, conversation_history or [])
        
        if n8n_result:
            # This is an automation request that n8n can handle
            if n8n_result.get("needs_clarification", False):
                # We need more information from the user
                # Let the agent handle it with the n8n context
                agent_message = f"[N8N_AUTOMATION_CONTEXT] {n8n_result.get('message', '')}"
                return original_process_message(agent_message, conversation_history, **kwargs)
                
            # We have a complete n8n result
            return {
                "response": n8n_result.get("message", "I've processed your automation request."),
                "n8n_workflow_id": n8n_result.get("workflow_id"),
                "n8n_workflow_name": n8n_result.get("workflow_name"),
                "n8n_success": n8n_result.get("success", False)
            }
            
        # Not an automation request, use the original method
        return original_process_message(message, conversation_history, **kwargs)
        
    # Replace the process_message method
    agent_service.process_message = process_message_with_n8n
    
    logger.info("n8n workflow capabilities integrated with agent service")
    
    return agent_service

# Example usage:
"""
# Import your agent service
from agent.agent_service import AgentService

# Create the agent service
agent_service = AgentService()

# Integrate n8n workflow capabilities
agent_service = integrate_n8n_with_agent_service(agent_service)

# Now the agent service can handle automation requests using n8n
response = agent_service.process_message("Send an email to john@example.com every day at 9am with the subject 'Daily Report'")
"""
