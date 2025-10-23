import json
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException
from typing import Optional

app = FastAPI(title='MCP Demo Server')

@app.get('/health')
async def health():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

@app.post('/api/context')
async def get_context(
    query: dict,
    x_api_key: Optional[str] = Header(None)
):
    if x_api_key != 'demo-key-change-in-production':
        raise HTTPException(status_code=401, detail='Invalid API key')

    # Simulate MCP context retrieval
    context = {
        'query': query.get('text', ''),
        'timestamp': datetime.now().isoformat(),
        'context_items': [
            {
                'source': 'knowledge_base',
                'content': 'This is simulated context from MCP',
                'relevance': 0.95
            },
            {
                'source': 'documents',
                'content': 'Additional context information',
                'relevance': 0.87
            }
        ],
        'metadata': {
            'model': 'mcp-demo-v1',
            'tokens_used': 150
        }
    }
    return context

@app.post('/api/execute')
async def execute_action(
    action: dict,
    x_api_key: Optional[str] = Header(None)
):
    if x_api_key != 'demo-key-change-in-production':
        raise HTTPException(status_code=401, detail='Invalid API key')

    # Simulate MCP action execution
    result = {
        'action': action.get('type', 'unknown'),
        'status': 'completed',
        'timestamp': datetime.now().isoformat(),
        'result': {
            'success': True,
            'message': f"Action {action.get('type')} executed successfully",
            'data': action.get('parameters', {})
        }
    }
    return result
