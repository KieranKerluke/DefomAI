"""
Workflow Detection Module

This module helps the AI agent determine when a user request
should be handled using n8n workflows for automation.
"""

import re
from typing import Dict, Any, List, Optional, Tuple, Set

# Patterns that indicate a user wants to automate something
AUTOMATION_PATTERNS = [
    r"automate",
    r"schedule",
    r"every (day|hour|week|month)",
    r"daily|hourly|weekly|monthly",
    r"repeat(ing|ed)?",
    r"recurring",
    r"periodically",
    r"at (\d{1,2}:\d{2}|\d{1,2} (am|pm))",
    r"send .* (email|message)",
    r"fetch|retrieve|get .* (data|information)",
    r"monitor",
    r"track",
    r"sync",
    r"backup",
    r"notify",
    r"alert",
    r"when .* happens",
    r"if .* then",
    r"connect .* to",
    r"integrate with",
    r"workflow",
    r"post to",
    r"publish",
]

# Map of workflow types to their detection patterns
WORKFLOW_TYPE_PATTERNS = {
    "email": [
        r"email",
        r"send .* email",
        r"mail",
        r"gmail",
        r"outlook",
        r"smtp",
    ],
    "telegram": [
        r"telegram",
        r"send .* message",
        r"chat",
        r"bot",
    ],
    "data_fetch": [
        r"fetch|retrieve|get .* data",
        r"api",
        r"http",
        r"request",
        r"download",
        r"scrape",
        r"extract",
        r"stock price",
        r"weather",
        r"news",
    ],
    "schedule": [
        r"schedule",
        r"every (day|hour|week|month)",
        r"daily|hourly|weekly|monthly",
        r"at (\d{1,2}:\d{2}|\d{1,2} (am|pm))",
        r"cron",
        r"recurring",
        r"periodically",
        r"repeat",
    ],
}

def is_automation_request(text: str) -> bool:
    """
    Determine if a user request is asking for automation.
    
    Args:
        text: User request text
        
    Returns:
        True if the request is for automation, False otherwise
    """
    text = text.lower()
    
    for pattern in AUTOMATION_PATTERNS:
        if re.search(pattern, text):
            return True
            
    return False

def detect_workflow_type(text: str) -> Optional[str]:
    """
    Detect the type of workflow needed for a user request.
    
    Args:
        text: User request text
        
    Returns:
        Workflow type or None if no specific type is detected
    """
    text = text.lower()
    
    # Count matches for each workflow type
    type_scores = {}
    
    for workflow_type, patterns in WORKFLOW_TYPE_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, text)
            score += len(matches)
        
        type_scores[workflow_type] = score
    
    # Find the workflow type with the highest score
    if not type_scores:
        return None
        
    max_score = max(type_scores.values())
    if max_score == 0:
        return None
        
    # Get all types with the max score
    top_types = [t for t, s in type_scores.items() if s == max_score]
    
    # If there's a tie, prefer more specific workflow types
    if len(top_types) > 1:
        priority_order = ["email", "telegram", "data_fetch", "schedule"]
        for workflow_type in priority_order:
            if workflow_type in top_types:
                return workflow_type
                
    return top_types[0] if top_types else None

def extract_workflow_parameters(text: str, workflow_type: str) -> Dict[str, Any]:
    """
    Extract parameters for a workflow from user text.
    
    Args:
        text: User request text
        workflow_type: Type of workflow
        
    Returns:
        Dictionary of parameters
    """
    text = text.lower()
    params = {}
    
    if workflow_type == "email":
        # Extract email parameters
        to_match = re.search(r"to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
        if to_match:
            params["toEmail"] = to_match.group(1)
            
        subject_match = re.search(r"subject\s+[\"'](.+?)[\"']", text)
        if subject_match:
            params["subject"] = subject_match.group(1)
        else:
            # Try to find subject without quotes
            subject_match = re.search(r"subject\s+(.+?)(\s+with|\s+body|\s+content|$)", text)
            if subject_match:
                params["subject"] = subject_match.group(1).strip()
                
        body_match = re.search(r"body\s+[\"'](.+?)[\"']", text)
        if body_match:
            params["body"] = body_match.group(1)
        else:
            # Try to find content/message
            body_match = re.search(r"(content|message|body)\s+(.+?)(\s+to|\s+every|\s+at|$)", text)
            if body_match:
                params["body"] = body_match.group(2).strip()
                
    elif workflow_type == "telegram":
        # Extract Telegram parameters
        message_match = re.search(r"message\s+[\"'](.+?)[\"']", text)
        if message_match:
            params["message"] = message_match.group(1)
        else:
            # Try to find message without quotes
            message_match = re.search(r"message\s+(.+?)(\s+to|\s+every|\s+at|$)", text)
            if message_match:
                params["message"] = message_match.group(1).strip()
                
    elif workflow_type == "data_fetch":
        # Extract data fetch parameters
        url_match = re.search(r"(from|url)\s+(https?://\S+)", text)
        if url_match:
            params["url"] = url_match.group(2)
            
    elif workflow_type == "schedule":
        # Extract schedule parameters
        
        # Check for daily/weekly/monthly
        if "daily" in text or "every day" in text:
            params["schedule_mode"] = "everyDay"
        elif "weekly" in text or "every week" in text:
            params["schedule_mode"] = "everyWeek"
        elif "monthly" in text or "every month" in text:
            params["schedule_mode"] = "everyMonth"
        else:
            params["schedule_mode"] = "everyX"
            
        # Extract time
        time_match = re.search(r"at\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?", text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or "0")
            
            # Handle am/pm
            if time_match.group(3) == "pm" and hour < 12:
                hour += 12
            elif time_match.group(3) == "am" and hour == 12:
                hour = 0
                
            params["hour"] = str(hour)
            params["minute"] = str(minute)
            
        # Extract day of week
        days_of_week = {
            "monday": "1", "tuesday": "2", "wednesday": "3", 
            "thursday": "4", "friday": "5", "saturday": "6", "sunday": "0"
        }
        
        for day, value in days_of_week.items():
            if day in text:
                params["day_of_week"] = value
                break
                
    return params

def analyze_automation_request(text: str) -> Dict[str, Any]:
    """
    Analyze a user request for automation needs.
    
    Args:
        text: User request text
        
    Returns:
        Analysis results including workflow type and parameters
    """
    if not is_automation_request(text):
        return {
            "is_automation": False
        }
        
    workflow_type = detect_workflow_type(text)
    
    if not workflow_type:
        return {
            "is_automation": True,
            "workflow_type": None,
            "confidence": 0.5
        }
        
    parameters = extract_workflow_parameters(text, workflow_type)
    
    # Calculate confidence based on parameter extraction
    param_count = len(parameters)
    expected_params = {
        "email": 3,  # toEmail, subject, body
        "telegram": 1,  # message
        "data_fetch": 1,  # url
        "schedule": 3,  # schedule_mode, hour, minute
    }
    
    confidence = min(1.0, param_count / expected_params.get(workflow_type, 1))
    
    return {
        "is_automation": True,
        "workflow_type": workflow_type,
        "parameters": parameters,
        "confidence": confidence,
        "missing_parameters": [
            param for param in get_required_parameters(workflow_type) 
            if param not in parameters
        ]
    }

def get_required_parameters(workflow_type: str) -> List[str]:
    """
    Get the required parameters for a workflow type.
    
    Args:
        workflow_type: Type of workflow
        
    Returns:
        List of required parameter names
    """
    if workflow_type == "email":
        return ["toEmail", "subject", "body"]
    elif workflow_type == "telegram":
        return ["message"]
    elif workflow_type == "data_fetch":
        return ["url"]
    elif workflow_type == "schedule":
        return ["schedule_mode", "hour", "minute"]
    else:
        return []
