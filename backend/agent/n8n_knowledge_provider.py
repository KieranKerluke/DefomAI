"""
n8n Knowledge Provider

This module provides n8n knowledge to the AI agent, helping it understand
how to create and use n8n workflows effectively.
"""

import logging
from typing import Dict, Any, List, Optional, Union

from utils.n8n_documentation import (
    get_n8n_documentation,
    get_documentation_section,
    get_node_documentation,
    generate_workflow_template,
    get_node_parameters_schema
)

logger = logging.getLogger(__name__)

class N8nKnowledgeProvider:
    """Provider for n8n knowledge to the AI agent."""
    
    def __init__(self):
        """Initialize the n8n knowledge provider."""
        self.documentation = get_n8n_documentation()
        
    def get_n8n_overview(self) -> str:
        """
        Get an overview of n8n.
        
        Returns:
            Overview of n8n
        """
        return self.documentation.get("overview", "")
        
    def get_node_types(self) -> Dict[str, str]:
        """
        Get information about common node types.
        
        Returns:
            Dictionary of node types and their descriptions
        """
        return self.documentation.get("common_node_types", {})
        
    def get_workflow_structure(self) -> Dict[str, str]:
        """
        Get information about workflow structure.
        
        Returns:
            Dictionary of workflow structure components and their descriptions
        """
        return self.documentation.get("workflow_structure", {})
        
    def get_best_practices(self) -> Dict[str, str]:
        """
        Get best practices for n8n workflows.
        
        Returns:
            Dictionary of best practices categories and their descriptions
        """
        return self.documentation.get("best_practices", {})
        
    def get_workflow_example(self) -> Dict[str, Any]:
        """
        Get an example workflow.
        
        Returns:
            Example workflow as a dictionary
        """
        return self.documentation.get("workflow_json_example", {})
        
    def get_node_parameters(self, node_type: str) -> Dict[str, Any]:
        """
        Get parameters for a specific node type.
        
        Args:
            node_type: Type of node
            
        Returns:
            Dictionary of parameters and their schemas
        """
        return get_node_parameters_schema(node_type)
        
    def generate_workflow_for_use_case(self, use_case: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a workflow template for a specific use case.
        
        Args:
            use_case: Type of workflow to generate
            parameters: Optional parameters for customization
            
        Returns:
            Workflow template as a dictionary
        """
        return generate_workflow_template(use_case, parameters)
        
    def get_knowledge_for_task(self, task_description: str) -> Dict[str, Any]:
        """
        Get relevant n8n knowledge for a specific task.
        
        Args:
            task_description: Description of the task
            
        Returns:
            Dictionary of relevant knowledge
        """
        # Extract key terms from the task description
        task_lower = task_description.lower()
        
        knowledge = {
            "overview": self.get_n8n_overview(),
            "relevant_nodes": [],
            "workflow_structure": self.get_workflow_structure(),
            "example_workflows": []
        }
        
        # Check for email-related tasks
        if any(term in task_lower for term in ["email", "mail", "gmail", "outlook", "smtp"]):
            knowledge["relevant_nodes"].append({
                "name": "Email",
                "description": get_node_documentation("Email"),
                "parameters": self.get_node_parameters("EmailSend")
            })
            knowledge["example_workflows"].append(
                self.generate_workflow_for_use_case("email_notification")
            )
            
        # Check for scheduling-related tasks
        if any(term in task_lower for term in ["schedule", "cron", "every day", "daily", "weekly", "monthly", "recurring"]):
            knowledge["relevant_nodes"].append({
                "name": "Cron",
                "description": get_node_documentation("Cron"),
                "parameters": self.get_node_parameters("Cron")
            })
            knowledge["example_workflows"].append(
                self.generate_workflow_for_use_case("scheduled_task")
            )
            
        # Check for HTTP/API-related tasks
        if any(term in task_lower for term in ["http", "api", "request", "fetch", "data", "get"]):
            knowledge["relevant_nodes"].append({
                "name": "HTTP Request",
                "description": get_node_documentation("HTTP Request"),
                "parameters": self.get_node_parameters("HttpRequest")
            })
            knowledge["example_workflows"].append(
                self.generate_workflow_for_use_case("data_fetch")
            )
            
        # Check for Telegram-related tasks
        if any(term in task_lower for term in ["telegram", "message", "chat", "bot"]):
            knowledge["relevant_nodes"].append({
                "name": "Telegram",
                "description": get_node_documentation("Telegram"),
                "parameters": self.get_node_parameters("Telegram")
            })
            
        return knowledge
        
    def enrich_agent_context(self, agent_context: Dict[str, Any], task_description: str) -> Dict[str, Any]:
        """
        Enrich the agent context with n8n knowledge.
        
        Args:
            agent_context: Current agent context
            task_description: Description of the task
            
        Returns:
            Enriched agent context
        """
        n8n_knowledge = self.get_knowledge_for_task(task_description)
        
        # Add n8n knowledge to the agent context
        agent_context["n8n_knowledge"] = n8n_knowledge
        
        return agent_context
