"""
n8n API Client for AI Agent Integration

This module provides a client for interacting with the n8n API,
allowing the AI agent to create, activate, and execute workflows.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class N8nClient:
    """Client for interacting with the n8n API."""
    
    def __init__(self, base_url: str = "http://localhost:5678", api_key: Optional[str] = None):
        """
        Initialize the n8n client.
        
        Args:
            base_url: Base URL of the n8n instance
            api_key: API key for authentication (defaults to N8N_API_KEY env var)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.getenv("N8N_API_KEY")
        
        if not self.api_key:
            logger.warning("No n8n API key provided. Authentication will fail.")
            
    @property
    def headers(self) -> Dict[str, str]:
        """Get the headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the n8n API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            API response as a dictionary
            
        Raises:
            Exception: If the request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            )
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except RequestException as e:
            logger.error(f"n8n API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise Exception(f"n8n API request failed: {str(e)}")
            
    # Workflow Management
    
    def get_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows."""
        return self._make_request("GET", "/workflows")
        
    def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new workflow.
        
        Args:
            workflow_data: Workflow definition
            
        Returns:
            Created workflow data
        """
        return self._make_request("POST", "/workflows", data=workflow_data)
        
    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get a workflow by ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow data
        """
        return self._make_request("GET", f"/workflows/{workflow_id}")
        
    def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a workflow.
        
        Args:
            workflow_id: Workflow ID
            workflow_data: Updated workflow definition
            
        Returns:
            Updated workflow data
        """
        return self._make_request("PATCH", f"/workflows/{workflow_id}", data=workflow_data)
        
    def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Delete a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Response data
        """
        return self._make_request("DELETE", f"/workflows/{workflow_id}")
        
    def activate_workflow(self, workflow_id: str, activate: bool = True) -> Dict[str, Any]:
        """
        Activate or deactivate a workflow.
        
        Args:
            workflow_id: Workflow ID
            activate: Whether to activate (True) or deactivate (False)
            
        Returns:
            Response data
        """
        endpoint = f"/workflows/{workflow_id}/activate" if activate else f"/workflows/{workflow_id}/deactivate"
        return self._make_request("POST", endpoint)
        
    def execute_workflow(self, workflow_id: str, execution_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            workflow_id: Workflow ID
            execution_data: Data to pass to the workflow execution
            
        Returns:
            Execution data
        """
        return self._make_request("POST", f"/workflows/{workflow_id}/run", data=execution_data or {})
        
    # Node Types
    
    def get_node_types(self) -> List[Dict[str, Any]]:
        """
        Get all available node types.
        
        Returns:
            List of node types
        """
        return self._make_request("GET", "/node-types")
        
    def get_node_type(self, node_type: str) -> Dict[str, Any]:
        """
        Get a specific node type.
        
        Args:
            node_type: Node type name
            
        Returns:
            Node type data
        """
        return self._make_request("GET", f"/node-types/{node_type}")
        
    # Executions
    
    def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Get execution details.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution data
        """
        return self._make_request("GET", f"/executions/{execution_id}")
        
    def get_executions(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get executions, optionally filtered by workflow ID.
        
        Args:
            workflow_id: Optional workflow ID to filter by
            
        Returns:
            List of executions
        """
        params = {"workflowId": workflow_id} if workflow_id else None
        return self._make_request("GET", "/executions", params=params)
        
    # Workflow Generation Helpers
    
    def generate_workflow_json(self, intent: str, nodes_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a workflow JSON from user intent and node configurations.
        
        Args:
            intent: User's intent description
            nodes_config: List of node configurations
            
        Returns:
            Workflow JSON
        """
        # Create a basic workflow structure
        workflow = {
            "name": f"AI Generated: {intent[:50]}",
            "nodes": [],
            "connections": {},
            "active": False,
            "settings": {
                "saveManualExecutions": True,
                "callerPolicy": "workflowsFromSameOwner"
            },
            "tags": ["ai-generated"],
            "pinData": {}
        }
        
        # Add nodes
        node_ids = {}
        for i, node_config in enumerate(nodes_config):
            node_type = node_config.get("type")
            node_name = node_config.get("name", f"{node_type} {i+1}")
            
            node = {
                "id": f"node_{i+1}",
                "name": node_name,
                "type": node_type,
                "typeVersion": node_config.get("typeVersion", 1),
                "position": node_config.get("position", [i * 200, i * 100]),
                "parameters": node_config.get("parameters", {})
            }
            
            workflow["nodes"].append(node)
            node_ids[node_name] = f"node_{i+1}"
            
        # Add connections based on the order of nodes
        for i in range(len(nodes_config) - 1):
            source_id = f"node_{i+1}"
            target_id = f"node_{i+2}"
            
            if source_id not in workflow["connections"]:
                workflow["connections"][source_id] = {}
                
            if "main" not in workflow["connections"][source_id]:
                workflow["connections"][source_id]["main"] = []
                
            workflow["connections"][source_id]["main"].append([
                {
                    "node": target_id,
                    "type": "main",
                    "index": 0
                }
            ])
            
        return workflow
