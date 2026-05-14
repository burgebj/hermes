"""Tool schemas for the DAM plugin (OpenAI function-calling format)."""

DAM_SEARCH = {
    "name": "dam_search",
    "description": (
        "Semantic search across conversation messages using neural pattern completion. "
        "Finds messages with similar meaning even when exact words differ."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query.",
            },
            "limit": {
                "type": "integer",
                "description": "Max results (default 10).",
            },
        },
        "required": ["query"],
    },
}

DAM_RECALL = {
    "name": "dam_recall",
    "description": "Find messages similar to a specific message by ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "message_id": {
                "type": "integer",
                "description": "Message ID to find similar messages for.",
            },
            "limit": {
                "type": "integer",
                "description": "Max results (default 5).",
            },
        },
        "required": ["message_id"],
    },
}

DAM_COMPOSE = {
    "name": "dam_compose",
    "description": (
        "Compositional search: find messages matching combinations of concepts "
        "with AND/OR/NOT."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Concepts to compose (at least 2 required).",
            },
            "operation": {
                "type": "string",
                "enum": ["AND", "OR", "NOT"],
                "description": "How to combine concepts (default AND).",
            },
            "limit": {
                "type": "integer",
                "description": "Max results (default 10).",
            },
        },
        "required": ["queries"],
    },
}

DAM_STATUS = {
    "name": "dam_status",
    "description": "Show Dense Associative Memory network status and statistics.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}
