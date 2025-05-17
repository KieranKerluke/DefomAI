"""
n8n Documentation Module

This module provides comprehensive documentation about n8n for the AI agent,
helping it understand how to use n8n effectively for workflow automation.
"""

# n8n Documentation
N8N_DOCUMENTATION = {
    "overview": """
    n8n is a fair-code licensed workflow automation platform that enables you to connect different services and automate tasks.
    It provides a visual workflow editor with a node-based approach, allowing you to create complex automations without coding.
    n8n can be self-hosted or used as a cloud service, and it supports both trigger-based and scheduled workflows.
    """,
    
    "key_concepts": {
        "workflow": """
        A workflow in n8n is a series of connected nodes that process data. Each workflow can be triggered manually, 
        on a schedule, or by external events (webhooks, database changes, etc.).
        """,
        
        "node": """
        Nodes are the building blocks of n8n workflows. Each node represents an action, service, or condition.
        There are different types of nodes:
        - Trigger nodes: Start workflows based on events or schedules
        - Regular nodes: Process data or perform actions
        - IF nodes: Add conditional logic to workflows
        """,
        
        "connections": """
        Connections link nodes together and define how data flows through the workflow.
        Each node can have multiple inputs and outputs, allowing for complex data routing.
        """,
        
        "parameters": """
        Parameters configure how nodes behave. Each node type has its own set of parameters.
        Parameters can be static values or expressions that reference data from previous nodes.
        """,
        
        "expressions": """
        n8n uses expressions to dynamically access and manipulate data. Expressions are enclosed in {{ }}.
        For example: {{ $json.data.email }} accesses the email field from the data object.
        """,
        
        "credentials": """
        Credentials store authentication information for services like APIs, databases, and email servers.
        They are stored securely and can be reused across workflows.
        """
    },
    
    "common_node_types": {
        "HTTP Request": """
        Makes HTTP requests to APIs and web services. Supports GET, POST, PUT, DELETE methods.
        Example parameters: URL, method, headers, query parameters, body.
        """,
        
        "Cron": """
        Triggers workflows on a schedule using cron syntax or predefined intervals.
        Example parameters: Trigger times (every hour, day, week, etc.).
        """,
        
        "Email": """
        Sends emails via SMTP. Can include attachments and HTML content.
        Example parameters: To, subject, body, attachments.
        """,
        
        "Telegram": """
        Sends messages to Telegram chats or channels.
        Example parameters: Chat ID, message text, parse mode.
        """,
        
        "Function": """
        Executes custom JavaScript code to transform data or add custom logic.
        Example parameter: JavaScript code to execute.
        """,
        
        "IF": """
        Adds conditional branching to workflows based on conditions.
        Example parameters: Condition (boolean expression).
        """,
        
        "Switch": """
        Routes data based on multiple conditions, similar to a switch statement.
        Example parameters: Value to evaluate, cases to match.
        """,
        
        "Set": """
        Sets values in the data object, useful for creating or modifying data.
        Example parameters: Values to set (key-value pairs).
        """,
        
        "Webhook": """
        Creates HTTP endpoints that can trigger workflows when called.
        Example parameters: HTTP method, authentication.
        """
    },
    
    "workflow_structure": {
        "nodes": """
        The nodes array contains all nodes in the workflow. Each node has:
        - id: Unique identifier
        - name: Display name
        - type: Node type (e.g., "n8n-nodes-base.HttpRequest")
        - typeVersion: Version of the node type
        - position: [x, y] coordinates in the editor
        - parameters: Configuration for the node
        """,
        
        "connections": """
        The connections object defines how nodes are connected. Structure:
        {
            "Node_ID": {
                "main": [
                    [
                        {
                            "node": "Target_Node_ID",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            }
        }
        """,
        
        "settings": """
        Workflow settings control behavior like error handling and execution mode.
        Common settings:
        - saveExecutionProgress: Whether to save execution data
        - saveManualExecutions: Whether to save manual execution data
        - executionTimeout: Maximum execution time
        - timezone: Timezone for scheduling
        """
    },
    
    "api_endpoints": {
        "GET /workflows": "Lists all workflows",
        "POST /workflows": "Creates a new workflow",
        "GET /workflows/{id}": "Gets a specific workflow",
        "PATCH /workflows/{id}": "Updates a workflow",
        "DELETE /workflows/{id}": "Deletes a workflow",
        "POST /workflows/{id}/activate": "Activates a workflow",
        "POST /workflows/{id}/deactivate": "Deactivates a workflow",
        "POST /workflows/{id}/run": "Executes a workflow manually",
        "GET /executions": "Lists workflow executions",
        "GET /executions/{id}": "Gets a specific execution",
        "GET /node-types": "Lists all available node types"
    },
    
    "best_practices": {
        "error_handling": """
        Use Error Trigger nodes to handle errors in workflows.
        Set up notifications for failed workflows.
        Use try/catch in Function nodes for custom error handling.
        """,
        
        "security": """
        Store sensitive data in credentials, not in workflow parameters.
        Use environment variables for configuration when possible.
        Limit webhook access with authentication when exposed to the internet.
        """,
        
        "performance": """
        Use batch processing for large datasets.
        Implement pagination for API requests with large result sets.
        Use the Split In Batches node to process data in smaller chunks.
        """,
        
        "organization": """
        Use meaningful names for workflows and nodes.
        Add descriptions to workflows and complex nodes.
        Group related workflows using tags.
        """
    },
    
    "common_use_cases": {
        "data_synchronization": """
        Sync data between different systems (CRM, database, spreadsheets).
        Example: Sync new Airtable records to a PostgreSQL database.
        """,
        
        "notifications": """
        Send alerts and notifications based on events or conditions.
        Example: Send Slack message when a GitHub issue is created.
        """,
        
        "data_processing": """
        Transform, filter, and enrich data from various sources.
        Example: Clean and normalize CSV data before importing to a CRM.
        """,
        
        "scheduled_reports": """
        Generate and send reports on a schedule.
        Example: Send daily email with website analytics data.
        """,
        
        "api_integrations": """
        Connect systems that don't have native integrations.
        Example: Post new Shopify orders to a custom API.
        """
    },
    
    "workflow_json_example": {
        "name": "Send Daily Weather Report",
        "nodes": [
            {
                "id": "node_1",
                "name": "Cron",
                "type": "n8n-nodes-base.Cron",
                "typeVersion": 1,
                "position": [250, 300],
                "parameters": {
                    "triggerTimes": {
                        "item": [
                            {
                                "mode": "everyDay",
                                "hour": "8",
                                "minute": "0"
                            }
                        ]
                    }
                }
            },
            {
                "id": "node_2",
                "name": "HTTP Request",
                "type": "n8n-nodes-base.HttpRequest",
                "typeVersion": 1,
                "position": [450, 300],
                "parameters": {
                    "url": "https://api.weatherapi.com/v1/forecast.json",
                    "method": "GET",
                    "authentication": "genericCredentialType",
                    "genericCredentialType": "weatherApiCredential",
                    "queryParameters": {
                        "parameters": [
                            {
                                "name": "q",
                                "value": "London"
                            },
                            {
                                "name": "days",
                                "value": "1"
                            }
                        ]
                    }
                }
            },
            {
                "id": "node_3",
                "name": "Send Email",
                "type": "n8n-nodes-base.EmailSend",
                "typeVersion": 1,
                "position": [650, 300],
                "parameters": {
                    "fromEmail": "reports@example.com",
                    "toEmail": "user@example.com",
                    "subject": "Daily Weather Report",
                    "text": "=Today's weather in London: {{ $node[\"HTTP Request\"].json[\"current\"][\"condition\"][\"text\"] }} with a temperature of {{ $node[\"HTTP Request\"].json[\"current\"][\"temp_c\"] }}°C"
                }
            }
        ],
        "connections": {
            "node_1": {
                "main": [
                    [
                        {
                            "node": "node_2",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            },
            "node_2": {
                "main": [
                    [
                        {
                            "node": "node_3",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            }
        },
        "active": True,
        "settings": {
            "saveManualExecutions": True,
            "timezone": "Europe/London"
        }
    }
}

def get_n8n_documentation():
    """
    Get the complete n8n documentation.
    
    Returns:
        Dictionary containing n8n documentation
    """
    return N8N_DOCUMENTATION

def get_documentation_section(section_key):
    """
    Get a specific section of the n8n documentation.
    
    Args:
        section_key: Key of the section to retrieve
        
    Returns:
        Documentation section or None if not found
    """
    return N8N_DOCUMENTATION.get(section_key)

def get_node_documentation(node_type):
    """
    Get documentation for a specific node type.
    
    Args:
        node_type: Name of the node type
        
    Returns:
        Node documentation or None if not found
    """
    return N8N_DOCUMENTATION.get("common_node_types", {}).get(node_type)

def generate_workflow_template(use_case, parameters=None):
    """
    Generate a basic workflow template for a specific use case.
    
    Args:
        use_case: Type of workflow to generate
        parameters: Optional parameters for customization
        
    Returns:
        Workflow template as a dictionary
    """
    parameters = parameters or {}
    
    templates = {
        "email_notification": {
            "name": "Email Notification",
            "nodes": [
                {
                    "id": "node_1",
                    "name": "Start",
                    "type": "n8n-nodes-base.Start",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {}
                },
                {
                    "id": "node_2",
                    "name": "Send Email",
                    "type": "n8n-nodes-base.EmailSend",
                    "typeVersion": 1,
                    "position": [450, 300],
                    "parameters": {
                        "fromEmail": parameters.get("fromEmail", "notifications@example.com"),
                        "toEmail": parameters.get("toEmail", "recipient@example.com"),
                        "subject": parameters.get("subject", "Notification"),
                        "text": parameters.get("body", "This is a notification.")
                    }
                }
            ],
            "connections": {
                "node_1": {
                    "main": [
                        [
                            {
                                "node": "node_2",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                }
            }
        },
        "scheduled_task": {
            "name": "Scheduled Task",
            "nodes": [
                {
                    "id": "node_1",
                    "name": "Cron",
                    "type": "n8n-nodes-base.Cron",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {
                        "triggerTimes": {
                            "item": [
                                {
                                    "mode": parameters.get("schedule_mode", "everyDay"),
                                    "hour": parameters.get("hour", "9"),
                                    "minute": parameters.get("minute", "0")
                                }
                            ]
                        }
                    }
                },
                {
                    "id": "node_2",
                    "name": "Execute Task",
                    "type": "n8n-nodes-base.Function",
                    "typeVersion": 1,
                    "position": [450, 300],
                    "parameters": {
                        "functionCode": parameters.get("code", "// Your task code here\nreturn items;")
                    }
                }
            ],
            "connections": {
                "node_1": {
                    "main": [
                        [
                            {
                                "node": "node_2",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                }
            }
        },
        "data_fetch": {
            "name": "Data Fetch",
            "nodes": [
                {
                    "id": "node_1",
                    "name": "Start",
                    "type": "n8n-nodes-base.Start",
                    "typeVersion": 1,
                    "position": [250, 300],
                    "parameters": {}
                },
                {
                    "id": "node_2",
                    "name": "HTTP Request",
                    "type": "n8n-nodes-base.HttpRequest",
                    "typeVersion": 1,
                    "position": [450, 300],
                    "parameters": {
                        "url": parameters.get("url", "https://api.example.com/data"),
                        "method": "GET",
                        "authentication": "none"
                    }
                }
            ],
            "connections": {
                "node_1": {
                    "main": [
                        [
                            {
                                "node": "node_2",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                }
            }
        }
    }
    
    return templates.get(use_case, {})

def get_node_parameters_schema(node_type):
    """
    Get the parameter schema for a specific node type.
    
    Args:
        node_type: Name of the node type
        
    Returns:
        Parameter schema or empty dict if not found
    """
    schemas = {
        "EmailSend": {
            "fromEmail": {
                "type": "string",
                "description": "Email address to send from",
                "required": True
            },
            "toEmail": {
                "type": "string",
                "description": "Email address to send to",
                "required": True
            },
            "subject": {
                "type": "string",
                "description": "Subject of the email",
                "required": True
            },
            "text": {
                "type": "string",
                "description": "Body of the email",
                "required": True
            }
        },
        "Cron": {
            "triggerTimes": {
                "type": "object",
                "description": "When to trigger the workflow",
                "required": True,
                "properties": {
                    "item": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "mode": {
                                    "type": "string",
                                    "enum": ["everyMinute", "everyHour", "everyDay", "everyWeek", "everyMonth", "custom"],
                                    "description": "How often to trigger"
                                },
                                "hour": {
                                    "type": "string",
                                    "description": "Hour to trigger (0-23)"
                                },
                                "minute": {
                                    "type": "string",
                                    "description": "Minute to trigger (0-59)"
                                }
                            }
                        }
                    }
                }
            }
        },
        "HttpRequest": {
            "url": {
                "type": "string",
                "description": "URL to make the request to",
                "required": True
            },
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "DELETE", "HEAD", "PATCH"],
                "description": "HTTP method to use",
                "required": True
            },
            "authentication": {
                "type": "string",
                "enum": ["none", "basicAuth", "headerAuth", "queryAuth", "oauth2"],
                "description": "Authentication type to use"
            }
        },
        "Telegram": {
            "chatId": {
                "type": "string",
                "description": "Chat ID to send the message to",
                "required": True
            },
            "text": {
                "type": "string",
                "description": "Text of the message to send",
                "required": True
            },
            "parseMode": {
                "type": "string",
                "enum": ["None", "MarkdownV2", "HTML"],
                "description": "Parse mode for the message"
            }
        }
    }
    
    return schemas.get(node_type, {})
