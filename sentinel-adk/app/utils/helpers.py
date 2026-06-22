import json
import os

def load_json_data(filepath: str):
    """Utility to load a json file from the data dictionary."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {}

def format_response(data: dict, status: str = "success") -> dict:
    """Standardizes the response dictionary."""
    return {
        "status": status,
        "data": data
    }
