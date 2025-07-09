import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)


class AdakingsWebSocketConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time communication in Adakings restaurant system.
    Handles order updates, menu changes, and system notifications.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.user_group_name = None
        self.heartbeat_task = None
        self.authenticated = False
        
    async def connect(self):
        """Accept WebSocket connection and authenticate user."""
        await self.accept()
        
        # Send connection acknowledgment
        await self.send(text_data=json.dumps({
            'type': 'connection_status',
            'status': 'connected',
            'message': 'WebSocket connection established'
        }))
        
        logger.info(f"WebSocket connection established from {self.scope['client']}")
        
        # Start heartbeat
        self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        logger.info(f"WebSocket disconnected with code: {close_code}")
        
        # Cancel heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            
        # Leave user group if authenticated
        if self.user_group_name and self.authenticated:
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            
        # Leave global broadcast group
        await self.channel_layer.group_discard(
            'broadcast',
            self.channel_name
        )
        
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'authenticate':
                await self.handle_authentication(data)
            elif message_type == 'heartbeat':
                await self.handle_heartbeat()
            elif message_type == 'subscribe':
                await self.handle_subscription(data)
            elif message_type == 'unsubscribe':
                await self.handle_unsubscription(data)
            else:
                await self.send_error('Unknown message type')
                
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON format')
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            await self.send_error('Internal server error')
            
    async def handle_authentication(self, data):
        """Authenticate user using JWT token."""
        token = data.get('token')
        
        if not token:
            await self.send_error('Authentication token required')
            return
            
        try:
            # Validate JWT token
            validated_token = UntypedToken(token)
            user_id = validated_token.get('user_id')
            
            # Get user from database
            user = await self.get_user_by_id(user_id)
            
            if user and user.is_active:
                self.user = user
                self.authenticated = True
                self.user_group_name = f"user_{user.id}"
                
                # Join user-specific group
                await self.channel_layer.group_add(
                    self.user_group_name,
                    self.channel_name
                )
                
                # Join global broadcast group
                await self.channel_layer.group_add(
                    'broadcast',
                    self.channel_name
                )
                
                await self.send(text_data=json.dumps({
                    'type': 'authentication_status',
                    'status': 'authenticated',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                }))
                
                logger.info(f"User {user.username} authenticated via WebSocket")
                
            else:
                await self.send_error('Invalid user or user is inactive')
                
        except (InvalidToken, TokenError):
            await self.send_error('Invalid or expired token')
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await self.send_error('Authentication failed')
            
    async def handle_heartbeat(self):
        """Handle heartbeat messages."""
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_response',
            'timestamp': asyncio.get_event_loop().time()
        }))
        
    async def handle_subscription(self, data):
        """Handle subscription to specific channels."""
        if not self.authenticated:
            await self.send_error('Authentication required for subscriptions')
            return
            
        channel_types = data.get('channels', [])
        
        for channel_type in channel_types:
            if channel_type == 'orders':
                await self.channel_layer.group_add(
                    'orders_updates',
                    self.channel_name
                )
            elif channel_type == 'menu':
                await self.channel_layer.group_add(
                    'menu_updates',
                    self.channel_name
                )
            elif channel_type == 'transactions':
                await self.channel_layer.group_add(
                    'transaction_updates',
                    self.channel_name
                )
                
        await self.send(text_data=json.dumps({
            'type': 'subscription_status',
            'status': 'subscribed',
            'channels': channel_types
        }))
        
    async def handle_unsubscription(self, data):
        """Handle unsubscription from specific channels."""
        if not self.authenticated:
            await self.send_error('Authentication required')
            return
            
        channel_types = data.get('channels', [])
        
        for channel_type in channel_types:
            if channel_type == 'orders':
                await self.channel_layer.group_discard(
                    'orders_updates',
                    self.channel_name
                )
            elif channel_type == 'menu':
                await self.channel_layer.group_discard(
                    'menu_updates',
                    self.channel_name
                )
            elif channel_type == 'transactions':
                await self.channel_layer.group_discard(
                    'transaction_updates',
                    self.channel_name
                )
                
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_status',
            'status': 'unsubscribed',
            'channels': channel_types
        }))
        
    async def heartbeat_loop(self):
        """Send periodic heartbeat to keep connection alive."""
        while True:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat',
                    'timestamp': asyncio.get_event_loop().time()
                }))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break
                
    async def send_error(self, message):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
        
    # Group message handlers
    async def order_update(self, event):
        """Handle order update notifications."""
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'payload': event['payload']
        }))
        
    async def menu_update(self, event):
        """Handle menu update notifications."""
        await self.send(text_data=json.dumps({
            'type': 'menu_update',
            'payload': event['payload']
        }))
        
    async def transaction_update(self, event):
        """Handle transaction update notifications."""
        await self.send(text_data=json.dumps({
            'type': 'transaction_update',
            'payload': event['payload']
        }))
        
    async def broadcast_message(self, event):
        """Handle broadcast messages."""
        await self.send(text_data=json.dumps({
            'type': 'broadcast',
            'payload': event['payload']
        }))
        
    async def user_notification(self, event):
        """Handle user-specific notifications."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'payload': event['payload']
        }))
        
    # Database operations
    @database_sync_to_async
    def get_user_by_id(self, user_id):
        """Get user by ID from database."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
