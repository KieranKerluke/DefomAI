"""
n8n Workflow Tool for AI Agent

This tool allows the AI agent to create, activate, and execute n8n workflows
based on user intent, extending the agent's capabilities for automation tasks.
"""

import json
import time
from typing import Dict, Any, List, Optional, Union, Tuple
import logging
from pydantic import BaseModel, Field

from utils.n8n_client import N8nClient
from agent.base_tool import BaseTool
from agent.tool_registry import register_tool

logger = logging.getLogger(__name__)

class WorkflowRequest(BaseModel):
    """Request model for workflow creation and execution."""
    intent: str = Field(..., description="User's intent for the workflow")
    workflow_type: str = Field(..., description="Type of workflow to create (email, telegram, data_fetch, etc.)")
    parameters: Dict[str, Any] = Field(default={}, description="Parameters for the workflow")
    run_immediately: bool = Field(default=True, description="Whether to run the workflow immediately after creation")

class N8nWorkflowTool(BaseTool):
    """Tool for creating and executing n8n workflows."""
    
    name = "n8n_workflow"
    description = "Create and execute n8n workflows for automation tasks"
    
    def __init__(self):
        """Initialize the n8n workflow tool."""
        super().__init__()
        self.client = N8nClient()
        self.workflow_templates = self._load_workflow_templates()
        
    def _load_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load workflow templates for common automation tasks.
        
        Returns:
            Dictionary of workflow templates by type
        """
        # In a real implementation, these would be loaded from a file or database
        # For now, we'll define a few basic templates inline
        return {
            "email": {
                "description": "Send emails on a schedule or trigger",
                "nodes": [
                    {
                        "type": "n8n-nodes-base.Start",
                        "name": "Start",
                        "parameters": {}
                    },
                    {
                        "type": "n8n-nodes-base.EmailSend",
                        "name": "Send Email",
                        "parameters": {
                            "fromEmail": "{{$parameters.fromEmail}}",
                            "toEmail": "{{$parameters.toEmail}}",
                            "subject": "{{$parameters.subject}}",
                            "text": "{{$parameters.body}}"
                        }
                    }
                ]
            },
            "telegram": {
                "description": "Send messages to Telegram",
                "nodes": [
                    {
                        "type": "n8n-nodes-base.Start",
                        "name": "Start",
                        "parameters": {}
                    },
                    {
                        "type": "n8n-nodes-base.Telegram",
                        "name": "Telegram",
                        "parameters": {
                            "chatId": "{{$parameters.chatId}}",
                            "text": "{{$parameters.message}}"
                        }
                    }
                ]
            },
            "data_fetch": {
                "description": "Fetch data from an API",
                "nodes": [
                    {
                        "type": "n8n-nodes-base.Start",
                        "name": "Start",
                        "parameters": {}
                    },
                    {
                        "type": "n8n-nodes-base.HttpRequest",
                        "name": "HTTP Request",
                        "parameters": {
                            "url": "{{$parameters.url}}",
                            "method": "GET",
                            "authentication": "none"
                        }
                    }
                ]
            },
            "schedule": {
                "description": "Run a task on a schedule",
                "nodes": [
                    {
                        "type": "n8n-nodes-base.Cron",
                        "name": "Cron",
                        "parameters": {
                            "triggerTimes": {
                                "item": [
                                    {
                                        "mode": "{{$parameters.schedule_mode}}",
                                        "hour": "{{$parameters.hour}}",
                                        "minute": "{{$parameters.minute}}",
                                        "dayOfMonth": "{{$parameters.day_of_month}}",
                                        "dayOfWeek": "{{$parameters.day_of_week}}"
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        }
        
    def _customize_workflow_template(self, workflow_type: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Customize a workflow template with user parameters.
        
        Args:
            workflow_type: Type of workflow to customize
            parameters: Parameters for customization
            
        Returns:
            List of customized node configurations
        """
        if workflow_type not in self.workflow_templates:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
            
        template = self.workflow_templates[workflow_type]
        nodes = template["nodes"]
        
        # Deep copy the nodes to avoid modifying the template
        import copy
        nodes_copy = copy.deepcopy(nodes)
        
        # Replace parameter placeholders with actual values
        for node in nodes_copy:
            if "parameters" in node:
                for param_key, param_value in node["parameters"].items():
                    if isinstance(param_value, str) and "{{$parameters." in param_value:
                        # Extract the parameter name from the placeholder
                        param_name = param_value.replace("{{$parameters.", "").replace("}}", "")
                        if param_name in parameters:
                            node["parameters"][param_key] = parameters[param_name]
                            
        return nodes_copy
        
    def _wait_for_execution(self, execution_id: str, max_wait_seconds: int = 30) -> Dict[str, Any]:
        """
        Wait for a workflow execution to complete.
        
        Args:
            execution_id: Execution ID
            max_wait_seconds: Maximum time to wait in seconds
            
        Returns:
            Execution data
        """
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            execution = self.client.get_execution(execution_id)
            status = execution.get("status")
            
            if status in ["success", "error", "crashed", "canceled"]:
                return execution
                
            time.sleep(1)
            
        return {"status": "timeout", "message": f"Execution did not complete within {max_wait_seconds} seconds"}
        
    def _extract_execution_results(self, execution: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract useful results from a workflow execution.
        
        Args:
            execution: Execution data
            
        Returns:
            Extracted results
        """
        if execution.get("status") != "success":
            return {
                "success": False,
                "status": execution.get("status", "unknown"),
                "error": execution.get("error", {}).get("message", "Unknown error")
            }
            
        # Extract data from the last node
        data = execution.get("data", {})
        result_data = data.get("resultData", {})
        
        # Get the last node's output
        run_data = result_data.get("runData", {})
        if not run_data:
            return {"success": True, "data": None}
            
        # Find the last node
        last_node_name = list(run_data.keys())[-1]
        last_node_data = run_data[last_node_name]
        
        # Get the last output
        if not last_node_data:
            return {"success": True, "data": None}
            
        last_output = last_node_data[-1]
        output_data = last_output.get("data", {}).get("main", [[]])[0]
        
        return {
            "success": True,
            "node": last_node_name,
            "data": output_data
        }
        
    def _create_workflow_from_intent(self, intent: str, workflow_type: str, parameters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Create a workflow based on user intent.
        
        Args:
            intent: User's intent description
            workflow_type: Type of workflow to create
            parameters: Parameters for the workflow
            
        Returns:
            Tuple of (workflow_id, workflow_data)
        """
        # Customize the workflow template
        nodes_config = self._customize_workflow_template(workflow_type, parameters)
        
        # Generate the workflow JSON
        workflow_json = self.client.generate_workflow_json(intent, nodes_config)
        
        # Create the workflow
        created_workflow = self.client.create_workflow(workflow_json)
        
        return created_workflow["id"], created_workflow
        
    def execute(self, request: WorkflowRequest) -> Dict[str, Any]:
        """
        Execute the tool with the given request.
        
        Args:
            request: Workflow request
            
        Returns:
            Tool execution result
        """
        try:
            # Create the workflow
            workflow_id, workflow_data = self._create_workflow_from_intent(
                request.intent,
                request.workflow_type,
                request.parameters
            )
            
            result = {
                "workflow_id": workflow_id,
                "workflow_name": workflow_data.get("name", "Unknown"),
                "created": True
            }
            
            # Run the workflow if requested
            if request.run_immediately:
                # Activate the workflow
                self.client.activate_workflow(workflow_id)
                
                # Execute the workflow
                execution = self.client.execute_workflow(workflow_id)
                execution_id = execution.get("id")
                
                if execution_id:
                    # Wait for execution to complete
                    execution_result = self._wait_for_execution(execution_id)
                    
                    # Extract useful results
                    result["execution"] = self._extract_execution_results(execution_result)
                    result["execution_id"] = execution_id
                    result["status"] = execution_result.get("status")
                else:
                    result["execution"] = {"success": False, "error": "Failed to start execution"}
                    
            return result
            
        except Exception as e:
            logger.exception("Error executing n8n workflow tool")
            return {
                "error": str(e),
                "created": False
            }

# Register the tool
register_tool(N8nWorkflowTool())
