from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import json
import structlog
from typing import Optional

from ....core.database import get_db
from ....core.auth import get_user_from_token
from ....core.auth_dependency import get_current_user
from ....core.websocket import connection_manager, WebSocketHandler
from ....models.user import User

logger = structlog.get_logger()
router = APIRouter()


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time chat"""
    user = None
    user_id = None
    
    try:
        # Authenticate user
        if not token:
            await websocket.close(code=4001, reason="Authentication token required")
            return
            
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Invalid authentication token")
            return
            
        user_id = str(user.id)
        
        # Accept connection
        await connection_manager.connect(websocket, user_id)
        
        # Create message handler
        handler = WebSocketHandler(db, user, websocket)
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            'type': 'connected',
            'user_id': user_id,
            'message': 'Connected to Joulaa Chat'
        }))
        
        logger.info(
            "WebSocket chat connection established",
            user_id=user_id,
            username=user.username
        )
        
        # Listen for messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle message
                await handler.handle_message(message_data)
                
            except WebSocketDisconnect:
                logger.info(
                    "WebSocket chat disconnected normally",
                    user_id=user_id
                )
                break
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                }))
                
            except Exception as e:
                logger.error(
                    "Error in WebSocket chat loop",
                    user_id=user_id,
                    error=str(e),
                    exc_info=True
                )
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': 'Internal server error'
                }))
                
    except WebSocketDisconnect:
        logger.info(
            "WebSocket chat disconnected during setup",
            user_id=user_id
        )
        
    except Exception as e:
        logger.error(
            "Error in WebSocket chat endpoint",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        
    finally:
        # Clean up connection
        if user_id:
            connection_manager.disconnect(websocket, user_id)
            
            
@router.get("/connections")
async def get_active_connections(
    current_user: User = Depends(get_current_user)
):
    """Get information about active WebSocket connections (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
        
    total_connections = sum(
        len(connections) 
        for connections in connection_manager.active_connections.values()
    )
    
    total_conversations = len(connection_manager.conversation_participants)
    
    return {
        'total_users_connected': len(connection_manager.active_connections),
        'total_connections': total_connections,
        'active_conversations': total_conversations,
        'connection_details': {
            user_id: len(connections)
            for user_id, connections in connection_manager.active_connections.items()
        }
    }
