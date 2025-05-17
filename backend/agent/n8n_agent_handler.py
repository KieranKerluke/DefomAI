"""
n8n Agent Handler

This module integrates n8n workflow capabilities into the AI agent system,
allowing the agent to detect when to use n8n for automation tasks.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union

from utils.workflow_detector import analyze_automation_request
from agent.tools.n8n_workflow_tool import WorkflowRequest

logger = logging.getLogger(__name__)

class N8nAgentHandler:
    """Handler for integrating n8n workflows with the AI agent."""
    
    def __init__(self, agent_service):
        """
        Initialize the n8n agent handler.
        
        Args:
            agent_service: The agent service to integrate with
        """
        self.agent_service = agent_service
        
    def process_message(self, message: str, conversation_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Process a user message to determine if it requires n8n workflow automation.
        
        Args:
            message: User message
            conversation_history: Conversation history
            
        Returns:
            Workflow execution result or None if not an automation request
        """
        # Analyze the message for automation needs
        analysis = analyze_automation_request(message)
        
        if not analysis["is_automation"]:
            # Not an automation request, let the regular agent handle it
            return None
            
        logger.info(f"Detected automation request: {analysis}")
        
        if not analysis["workflow_type"]:
            # Automation request but couldn't determine the type
            # Let the agent handle it with a hint about automation
            return {
                "is_automation": True,
                "needs_clarification": True,
                "message": "I detected that you want to automate something, but I need more details about what type of automation you need."
            }
            
        # Check if we have all required parameters
        if analysis["missing_parameters"]:
            missing_params = ", ".join(analysis["missing_parameters"])
            return {
                "is_automation": True,
                "needs_clarification": True,
                "workflow_type": analysis["workflow_type"],
                "message": f"I can create a {analysis['workflow_type']} workflow for you, but I need more information: {missing_params}"
            }
            
        # We have enough information to create a workflow
        try:
            # Create a workflow request
            request = WorkflowRequest(
                intent=message,
                workflow_type=analysis["workflow_type"],
                parameters=analysis["parameters"],
                run_immediately=True
            )
            
            # Execute the workflow tool
            result = self.agent_service.execute_tool("n8n_workflow", request.dict())
            
            # Format the result for the user
            if result.get("created", False):
                workflow_name = result.get("workflow_name", "workflow")
                
                if result.get("execution", {}).get("success", False):
                    # Successful execution
                    execution_data = result.get("execution", {}).get("data", [])
                    
                    # Format the execution data for display
                    data_summary = self._format_execution_data(execution_data)
                    
                    return {
                        "is_automation": True,
                        "success": True,
                        "workflow_id": result.get("workflow_id"),
                        "workflow_name": workflow_name,
                        "message": f"I've created and executed the {workflow_name} for you. {data_summary}"
                    }
                else:
                    # Workflow created but execution failed
                    error = result.get("execution", {}).get("error", "Unknown error")
                    
                    return {
                        "is_automation": True,
                        "success": False,
                        "workflow_id": result.get("workflow_id"),
                        "workflow_name": workflow_name,
                        "message": f"I've created the {workflow_name}, but there was an error when executing it: {error}"
                    }
            else:
                # Failed to create workflow
                error = result.get("error", "Unknown error")
                
                return {
                    "is_automation": True,
                    "success": False,
                    "message": f"I couldn't create the workflow: {error}"
                }
                
        except Exception as e:
            logger.exception("Error processing automation request")
            
            return {
                "is_automation": True,
                "success": False,
                "message": f"There was an error processing your automation request: {str(e)}"
            }
            
    def _format_execution_data(self, execution_data: List[Dict[str, Any]]) -> str:
        """
        Format execution data for display to the user.
        
        Args:
            execution_data: Execution data from n8n
            
        Returns:
            Formatted string for display
        """
        if not execution_data:
            return "No data was returned from the execution."
            
        # For simple data types, just return the value
        if len(execution_data) == 1 and isinstance(execution_data[0], (str, int, float, bool)):
            return f"Result: {execution_data[0]}"
            
        # For more complex data, create a summary
        try:
            # Try to format as JSON for readability
            formatted_data = json.dumps(execution_data, indent=2)
            return f"Here's the result of the execution:\n\n```json\n{formatted_data}\n```"
        except:
            # Fallback to simple string representation
            return f"Result: {str(execution_data)}"
