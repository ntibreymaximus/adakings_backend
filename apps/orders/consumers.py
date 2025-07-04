import json
import logging
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import Order
from .serializers import OrderSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


class OrderConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time order updates.
    Handles authentication via JWT tokens and broadcasts order changes.
    """

    async def connect(self):
        """Accept WebSocket connection and authenticate user."""
        try:
            # Get token from query string
            query_string = self.scope.get('query_string', b'').decode('utf-8')
            if not query_string or not query_string.startswith('token='):
                logger.warning("WebSocket connection attempted without valid token")
                await self.close(code=4001)  # Unauthorized
                return
                
            token = query_string.split('token=')[1].split('&')[0]  # Handle multiple query params
            if not token:
                logger.warning("WebSocket connection attempted with empty token")
                await self.close(code=4001)  # Unauthorized
                return

            # Authenticate user
            user = await self.authenticate_token(token)
            if not user:
                logger.warning("WebSocket connection attempted with invalid token")
                await self.close(code=4001)  # Unauthorized
                return

            self.user = user
            self.group_name = 'orders'
            self.heartbeat_task = None

            # Join the orders group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            await self.accept()
            
            # Start heartbeat to detect broken connections
            self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
            
            # Send initial data
            await self.send_initial_orders()
            
            logger.info(f"WebSocket connected for user: {user.username}")

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            try:
                await self.close(code=4000)  # Bad request
            except Exception:
                pass  # Connection might already be closed

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Cancel heartbeat task
            if hasattr(self, 'heartbeat_task') and self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # Leave the group
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
            
            if hasattr(self, 'user'):
                logger.info(f"WebSocket disconnected for user: {self.user.username}, close_code: {close_code}")
            else:
                logger.info(f"WebSocket disconnected, close_code: {close_code}")
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'request_orders':
                await self.send_initial_orders()
            elif message_type == 'ping':
                await self.safe_send({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                })
            elif message_type == 'heartbeat':
                await self.safe_send({
                    'type': 'heartbeat_ack',
                    'timestamp': data.get('timestamp')
                })
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in WebSocket")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            # Don't close connection for non-critical errors

    async def send_initial_orders(self):
        """Send initial orders data to the client."""
        try:
            orders = await self.get_orders()
            await self.safe_send({
                'type': 'data_update',
                'data': orders
            })
        except Exception as e:
            logger.error(f"Error sending initial orders: {e}")

    async def order_created(self, event):
        """Handle order created event."""
        await self.safe_send({
            'type': 'item_created',
            'item': event['order']
        })

    async def order_updated(self, event):
        """Handle order updated event."""
        await self.safe_send({
            'type': 'item_updated',
            'item': event['order']
        })

    async def order_deleted(self, event):
        """Handle order deleted event."""
        await self.safe_send({
            'type': 'item_deleted',
            'item_id': event['order_id']
        })

    @database_sync_to_async
    def authenticate_token(self, token):
        """Authenticate user using JWT token."""
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
            return user if user.is_active else None
        except (InvalidToken, TokenError, User.DoesNotExist):
            return None

    async def safe_send(self, data):
        """Safely send data over WebSocket with error handling."""
        try:
            await self.send(text_data=json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            # Mark connection as broken if send fails
            raise StopConsumer()
    
    async def heartbeat_loop(self):
        """Send periodic heartbeat to detect broken connections."""
        heartbeat_failures = 0
        max_failures = 3
        
        try:
            while True:
                await asyncio.sleep(25)  # Send heartbeat every 25 seconds (before server timeout)
                try:
                    await self.safe_send({
                        'type': 'heartbeat',
                        'timestamp': asyncio.get_event_loop().time(),
                        'server_id': getattr(self, 'server_id', 'unknown')
                    })
                    heartbeat_failures = 0  # Reset failure count on success
                except Exception as e:
                    heartbeat_failures += 1
                    logger.warning(f"Heartbeat failure #{heartbeat_failures}: {e}")
                    
                    if heartbeat_failures >= max_failures:
                        logger.error(f"Max heartbeat failures reached ({max_failures}). Closing connection.")
                        break
                    
                    # Exponential backoff for failed heartbeats
                    await asyncio.sleep(min(5 * (2 ** heartbeat_failures), 30))
                    
        except asyncio.CancelledError:
            logger.info("Heartbeat loop cancelled gracefully")
        except Exception as e:
            logger.error(f"Critical heartbeat error: {e}")
        finally:
            # Ensure connection is closed if heartbeat loop exits
            try:
                await self.close(code=1000)  # Normal closure
            except Exception:
                pass  # Connection might already be closed

    @database_sync_to_async
    def get_orders(self):
        """Get all orders for the authenticated user."""
        try:
            orders = Order.objects.all().order_by('-created_at')
            serializer = OrderSerializer(orders, many=True)
            return serializer.data
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []


# Utility functions to broadcast order changes
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def broadcast_order_created(order):
    """Broadcast order creation to all connected clients."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            serializer = OrderSerializer(order)
            async_to_sync(channel_layer.group_send)(
                'orders',
                {
                    'type': 'order.created',
                    'order': serializer.data
                }
            )
    except Exception as e:
        logger.error(f"Error broadcasting order creation: {e}")

def broadcast_order_updated(order):
    """Broadcast order update to all connected clients."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            serializer = OrderSerializer(order)
            async_to_sync(channel_layer.group_send)(
                'orders',
                {
                    'type': 'order.updated',
                    'order': serializer.data
                }
            )
    except Exception as e:
        logger.error(f"Error broadcasting order update: {e}")

def broadcast_order_deleted(order_id):
    """Broadcast order deletion to all connected clients."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                'orders',
                {
                    'type': 'order.deleted',
                    'order_id': order_id
                }
            )
    except Exception as e:
        logger.error(f"Error broadcasting order deletion: {e}")
