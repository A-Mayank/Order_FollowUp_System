from datetime import datetime, timedelta
from typing import Optional
from beanie import PydanticObjectId

from models.order import Order, OrderStatus, PaymentStatus, Sentiment
from models.message_log import MessageLog, MessageType
from models.alert import Alert, AlertReason
from services.ai_service import ai_service
from services.whatsapp_service import whatsapp_service
from services.tracking_service import tracking_service
import os


class MessagePolicyService:
    
    

    
    async def send_order_confirmation(self, order: Order) -> bool:
        try:
            # Fetch user details - handle both Link and direct User object
            if hasattr(order.user_id, 'fetch'):
                user = await order.user_id.fetch()
            else:
                user = order.user_id
            
            # Generate personalized message using AI
            message = ai_service.personalize_message(
                customer_name=user.name,
                order_status="CREATED",
                product_name=order.product_name
            )
            

            
            # Check if template is configured
            template_sid = os.getenv("TWILIO_ORDER_CONFIRMATION_SID")
            
            if template_sid:
                # Use Template
                msg_sid = await whatsapp_service.send_message(
                    to_number=user.whatsapp_number,
                    content_sid=template_sid,
                    content_variables={
                        "1": user.name,
                        "2": order.product_name
                    }
                )
            else:
                # Fallback to Text
                msg_sid = await whatsapp_service.send_message(user.whatsapp_number, message)
            
            if msg_sid:
                # Log the message
                await MessageLog(
                    order_id=order,
                    message_type=MessageType.ORDER_CONFIRMATION,
                    message_content=f"[Template: {template_sid}]" if template_sid else message,
                    whatsapp_message_id=msg_sid,
                    is_incoming=False
                ).insert()
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error sending order confirmation: {str(e)}")
            return False

    async def send_payment_confirmation(self, order: Order) -> bool:
        try:
            if hasattr(order.user_id, 'fetch'):
                user = await order.user_id.fetch()
            else:
                user = order.user_id
            
            message = ai_service.personalize_message(
                customer_name=user.name,
                order_status="PAID",
                product_name=order.product_name
            )
            

            
            msg_sid = await whatsapp_service.send_message(user.whatsapp_number, message)
            
            if msg_sid:
                await MessageLog(
                    order_id=order,
                    message_type=MessageType.PAYMENT_CONFIRMATION,
                    message_content=message,
                    whatsapp_message_id=msg_sid,
                    is_incoming=False
                ).insert()
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error sending payment confirmation: {str(e)}")
            return False
    
    async def send_payment_reminder(self, order: Order, reminder_number: int) -> bool:
        
        # Only send if payment is still pending and automation is enabled
        if order.payment_status != PaymentStatus.PENDING or not order.automation_enabled:
            return False
        
        try:
            if hasattr(order.user_id, 'fetch'):
                user = await order.user_id.fetch()
            else:
                user = order.user_id
            
            # Generate reminder message
            if reminder_number == 1:
                message = ai_service.personalize_message(
                    customer_name=user.name,
                    order_status="PAYMENT_PENDING",
                    product_name=order.product_name
                )
                msg_type = MessageType.PAYMENT_REMINDER_1
                order.payment_reminder_1_sent_at = datetime.utcnow()
            else:
                message = f"Hi {user.name}, this is a final reminder that payment for your order is still pending. Please complete it soon to avoid cancellation."
                msg_type = MessageType.PAYMENT_REMINDER_2
                order.payment_reminder_2_sent_at = datetime.utcnow()
            

            
            # Send message
            # Add explicit cancellation instruction since we don't have a template button for this yet
            message += "\n\nTo cancel your order, reply with 'CANCEL'."
            msg_sid = await whatsapp_service.send_message(user.whatsapp_number, message)
            
            if msg_sid:
                await MessageLog(
                    order_id=order,
                    message_type=msg_type,
                    message_content=message,
                    whatsapp_message_id=msg_sid,
                    is_incoming=False
                ).insert()
                
                await order.save()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error sending payment reminder: {str(e)}")
            return False
    
    async def send_shipping_notification(self, order: Order) -> bool:
        try:
            if hasattr(order.user_id, 'fetch'):
                user = await order.user_id.fetch()
            else:
                user = order.user_id
            
            message = ai_service.personalize_message(
                customer_name=user.name,
                order_status="SHIPPED",
                product_name=order.product_name
            )

            # Add tracking info if available
            if order.tracking_id:
                message += f"\n\n🚚 *Tracking Info*:\nID: {order.tracking_id}\nCarrier: {order.carrier or 'Standard'}"
            

            
            msg_sid = await whatsapp_service.send_message(user.whatsapp_number, message)
            
            if msg_sid:
                await MessageLog(
                    order_id=order,
                    message_type=MessageType.SHIPPING_NOTIFICATION,
                    message_content=message,
                    whatsapp_message_id=msg_sid,
                    is_incoming=False
                ).insert()
                
                order.shipped_at = datetime.utcnow()
                await order.save()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error sending shipping notification: {str(e)}")
            return False
    
    async def send_delivery_notification(self, order: Order) -> bool:
        try:
            if hasattr(order.user_id, 'fetch'):
                user = await order.user_id.fetch()
            else:
                user = order.user_id
            
            message = ai_service.personalize_message(
                customer_name=user.name,
                order_status="DELIVERED",
                product_name=order.product_name
            )
            

            
            # Check if template is configured
            template_sid = os.getenv("TWILIO_DELIVERY_FEEDBACK_SID")
            
            if template_sid:
                # Use Template
                msg_sid = await whatsapp_service.send_message(
                    to_number=user.whatsapp_number,
                    content_sid=template_sid,
                    content_variables={
                        "1": user.name,
                        "2": order.product_name,
                        "3": str(order.id) # For tracking in URL
                    }
                )
            else:
                 # Add explicit feedback instruction to the AI/Fallback message
                 message += "\n\nGive your feedback! *"
                 msg_sid = await whatsapp_service.send_message(user.whatsapp_number, message)
            
            if msg_sid:
                await MessageLog(
                    order_id=order,
                    message_type=MessageType.DELIVERY_NOTIFICATION,
                    message_content=f"[Template: {template_sid}]" if template_sid else message,
                    whatsapp_message_id=msg_sid,
                    is_incoming=False
                ).insert()
                
                order.delivered_at = datetime.utcnow()
                await order.save()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error sending delivery notification: {str(e)}")
            return False
    
    async def send_in_process_notification(self, order: Order) -> bool:
        """Send 'in process' (packing) notification"""
        try:
            if hasattr(order.user_id, 'fetch'):
                user = await order.user_id.fetch()
            else:
                user = order.user_id
            
            message = ai_service.personalize_message(
                customer_name=user.name,
                order_status="IN_PROCESS",
                product_name=order.product_name
            )
            

            
            msg_sid = await whatsapp_service.send_message(user.whatsapp_number, message)
            
            if msg_sid:
                await MessageLog(
                    order_id=order,
                    message_type=MessageType.IN_PROCESS_NOTIFICATION,
                    message_content=message,
                    whatsapp_message_id=msg_sid,
                    is_incoming=False
                ).insert()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error sending in-process notification: {str(e)}")
            return False

    async def send_out_for_delivery_notification(self, order: Order) -> bool:
        """Send 'out for delivery' notification"""
        try:
            if hasattr(order.user_id, 'fetch'):
                user = await order.user_id.fetch()
            else:
                user = order.user_id
            
            message = ai_service.personalize_message(
                customer_name=user.name,
                order_status="OUT_FOR_DELIVERY",
                product_name=order.product_name
            )
            

            
            msg_sid = await whatsapp_service.send_message(user.whatsapp_number, message)
            
            if msg_sid:
                await MessageLog(
                    order_id=order,
                    message_type=MessageType.OUT_FOR_DELIVERY_NOTIFICATION,
                    message_content=message,
                    whatsapp_message_id=msg_sid,
                    is_incoming=False
                ).insert()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error sending out-for-delivery notification: {str(e)}")
            return False

    async def process_customer_reply(self, order_id: PydanticObjectId, reply_text: str) -> None:
        try:
            order = await Order.get(order_id)
            if not order:
                print(f"⚠️ process_customer_reply: Order {order_id} not found")
                return
                
            print(f"DEBUG: Processing reply for order {order.id}: '{reply_text}'")
            clean_reply = reply_text.strip().lower()
            
            # 1. Check for Commands
            if clean_reply in ["1", "status", "check status", "track"]:
                await self._handle_status_check(order)
                return
                
            if clean_reply in ["2", "cancel", "cancel order", "cancel_order"]:
                await self._handle_cancel_request(order)
                return
                
            if clean_reply == "3":
                # Prompt for detailed feedback (just acknowledgement for now)
                await self._send_reply(order, "Please type your feedback or experience with us!")
                return

            # 2. Handle Feedback for DELIVERED orders
            if order.status == OrderStatus.DELIVERED:
                # Extract rating (1-5) using AI
                rating = ai_service.extract_feedback_rating(reply_text)
                order.feedback_rating = rating
                order.feedback_text = reply_text
                
                # Classify sentiment as usual
                sentiment = ai_service.classify_sentiment(reply_text)
                order.sentiment = sentiment
                
                await order.save()
                
                # Log the feedback message
                await MessageLog(
                    order_id=order,
                    message_type=MessageType.CUSTOMER_REPLY,
                    message_content=reply_text,
                    is_incoming=True,
                    sentiment=sentiment
                ).insert()
                
                # Send thank you
                await self._send_reply(order, "Thank you so much for your feedback! It helps us improve.")
                return

            # 3. Normal AI Processing & Feedback Logging
            # Classify sentiment using AI
            sentiment = ai_service.classify_sentiment(reply_text)
            
            # Log the incoming message
            await MessageLog(
                order_id=order,
                message_type=MessageType.CUSTOMER_REPLY,
                message_content=reply_text,
                is_incoming=True,
                sentiment=sentiment
            ).insert()
            
            # Update order
            order.last_customer_reply_at = datetime.utcnow()
            order.sentiment = sentiment
            
            # If negative sentiment, create alert and stop automation
            if sentiment == "negative":
                order.automation_enabled = False
                
                await Alert(
                    order_id=order,
                    reason=AlertReason.NEGATIVE_SENTIMENT,
                    description=f"Customer expressed negative sentiment: '{reply_text[:100]}...'"
                ).insert()
                
                print(f"Negative sentiment detected for order {order.id}. Automation stopped.")
            
            await order.save()
            
        except Exception as e:
            print(f"Error processing customer reply: {str(e)}")

    async def _handle_status_check(self, order: Order):
        """Handle '1' - Status Check"""
        status_msg = f"📦 *Order Status*: {order.status}\n"
        if order.product_name:
            status_msg += f"Product: {order.product_name}\n"
        
        # Add Tracking Info if available
        if order.tracking_id:
            tracking_info = tracking_service.get_tracking_info(order.tracking_id, order.carrier)
            if tracking_info:
                status_msg += f"\n🚚 *Tracking Update*:\nStatus: {tracking_info.get('status')}\nLocation: {tracking_info.get('location')}\nETA: {tracking_info.get('eta')}\n"
        
        status_msg += f"\nPayment: {order.payment_status}\n"
        
        await self._send_reply(order, status_msg)

    async def _handle_cancel_request(self, order: Order):
        """Handle '2' - Cancel Request (Manual approval flow)"""
        # Allow cancellation request if order is not yet shipped
        # Removed IN_PROCESS as requested to streamline flow
        cancellable_statuses = [OrderStatus.CREATED, OrderStatus.PAYMENT_PENDING, OrderStatus.PAID]
        
        if order.status in cancellable_statuses:
            # Step 1: Immediately reply to customer
            await self._send_reply(order, "Processing your cancellation request. We'll notify you once it's confirmed.")
            
            # Step 2: Create alert for admin dashboard (do NOT cancel the order yet)
            await Alert(
                order_id=order,
                reason=AlertReason.CANCELLATION_REQUEST,
                description=f"Customer requested cancellation via WhatsApp (Current status: {order.status})"
            ).insert()
            
            print(f"Cancellation request alert created for order {order.id}")
        else:
            await self._send_reply(order, f"Sorry, your order cannot be cancelled as it is already {order.status}. Please contact support.")

    async def _send_reply(self, order: Order, text: str):
        """Helper to send a reply back to customer"""
        try:
            if hasattr(order.user_id, 'fetch'):
                user = await order.user_id.fetch()
            else:
                user = order.user_id
                
            msg_sid = await whatsapp_service.send_message(user.whatsapp_number, text)
            if msg_sid:
                # Log as outgoing message
                await MessageLog(
                    order_id=order,
                    message_type=MessageType.CUSTOMER_REPLY, # Using this type for now as 'system reply'
                    message_content=text,
                    whatsapp_message_id=msg_sid,
                    is_incoming=False
                ).insert()
        except Exception as e:
            print(f"Error sending reply: {str(e)}")
    
    async def check_no_response_alerts(self) -> None:
        """Check for orders with no customer response in 48 hours (scheduled job)"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=48)
            
            # Find orders with messages sent but no recent customer reply
            orders = await Order.find(
                Order.automation_enabled == True,
                Order.created_at < cutoff_time,
                Order.last_customer_reply_at == None
            ).to_list()
            
            for order in orders:
                # Check if we've sent at least one message
                msg_count = await MessageLog.find(
                    MessageLog.order_id.ref.id == order.id,
                    MessageLog.is_incoming == False
                ).count()
                
                if msg_count > 0:
                    # Create alert and stop automation
                    order.automation_enabled = False
                    await order.save()
                    
                    await Alert(
                        order_id=order,
                        reason=AlertReason.NO_CUSTOMER_RESPONSE,
                        description=f"No customer response for 48 hours"
                    ).insert()
                    
                    print(f"No response alert created for order {order.id}")
            
        except Exception as e:
            print(f"Error checking no-response alerts: {str(e)}")


# Singleton instance
message_policy = MessagePolicyService()
