from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from datetime import datetime

from models.order import Order, Sentiment
from models.alert import Alert
from services.whatsapp_service import whatsapp_service
from services.ai_service import ai_service
from models.message_log import MessageType, MessageLog
from models.user import User


router = APIRouter(prefix="/api/admin", tags=["admin"])


# Response Models
class OrderSummary(BaseModel):
    id: str
    user_name: str
    whatsapp_number: str
    status: str
    payment_status: str
    sentiment: str
    automation_enabled: bool
    product_name: str | None
    amount: float | None
    created_at: datetime
    feedback_rating: int | None = None
    feedback_text: str | None = None


class MessageLogResponse(BaseModel):
    id: str
    order_id: str
    message_type: str
    message_content: str
    sent_at: datetime
    is_incoming: bool
    sentiment: str | None


class AlertResponse(BaseModel):
    id: str
    order_id: str
    reason: str
    description: str
    created_at: datetime
    resolved: bool


@router.get("/orders", response_model=List[OrderSummary])
async def get_all_orders(skip: int = 0, limit: int = 50):
    """Get all orders for admin dashboard"""
    try:
        orders = await Order.find_all().sort(-Order.created_at).skip(skip).limit(limit).to_list()
        
        result = []
        for order in orders:
            user = await order.user_id.fetch()
            result.append(OrderSummary(
                id=str(order.id),
                user_name=user.name,
                whatsapp_number=user.whatsapp_number,
                status=order.status,
                payment_status=order.payment_status,
                sentiment=order.sentiment,
                automation_enabled=order.automation_enabled,
                product_name=order.product_name,
                amount=order.amount,
                created_at=order.created_at,
                feedback_rating=order.feedback_rating,
                feedback_text=order.feedback_text
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages", response_model=List[MessageLogResponse])
async def get_message_logs(order_id: str | None = None, skip: int = 0, limit: int = 100):
    """Get message logs, optionally filtered by order_id"""
    try:
        if order_id:
            messages = await MessageLog.find(
                MessageLog.order_id.ref.id == order_id
            ).sort(-MessageLog.sent_at).skip(skip).limit(limit).to_list()
        else:
            messages = await MessageLog.find_all().sort(-MessageLog.sent_at).skip(skip).limit(limit).to_list()
        
        return [
            MessageLogResponse(
                id=str(msg.id),
                order_id=str(msg.order_id.ref.id),
                message_type=msg.message_type,
                message_content=msg.message_content,
                sent_at=msg.sent_at,
                is_incoming=msg.is_incoming,
                sentiment=msg.sentiment if msg.sentiment else None
            )
            for msg in messages
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(resolved: bool | None = None, skip: int = 0, limit: int = 50):
    """Get alerts, optionally filtered by resolved status"""
    try:
        if resolved is not None:
            alerts = await Alert.find(
                Alert.resolved == resolved
            ).sort(-Alert.created_at).skip(skip).limit(limit).to_list()
        else:
            alerts = await Alert.find_all().sort(-Alert.created_at).skip(skip).limit(limit).to_list()
        
        return [
            AlertResponse(
                id=str(alert.id),
                order_id=str(alert.order_id.ref.id),
                reason=alert.reason,
                description=alert.description,
                created_at=alert.created_at,
                resolved=alert.resolved
            )
            for alert in alerts
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Mark an alert as resolved"""
    try:
        alert = await Alert.get(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.resolved = True
        alert.resolved_at = datetime.utcnow()
        await alert.save()
        
        return {"message": "Alert resolved", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/orders/{order_id}/cancel")
async def admin_cancel_order(order_id: str):
    """
    Admin manually cancels an order (after customer requested cancellation).
    - Sets order status to CANCELLED
    - Sends WhatsApp confirmation to the customer
    - Auto-resolves any CANCELLATION_REQUEST alerts for this order
    """
    try:
        from beanie import PydanticObjectId
        from models.alert import AlertReason
        from models.message_log import MessageLog, MessageType
        
        order = await Order.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status == "CANCELLED":
            raise HTTPException(status_code=400, detail="Order is already cancelled")
        
        # 1. Cancel the order
        order.status = "CANCELLED"
        order.automation_enabled = False
        await order.save()
        
        # 2. Send WhatsApp confirmation to customer
        user = await order.user_id.fetch()
        msg_sid = await whatsapp_service.send_message(
            user.whatsapp_number,
            "✅ Your order has been successfully cancelled. If you have any questions, feel free to reach out!"
        )
        
        if msg_sid:
            await MessageLog(
                order_id=order,
                message_type=MessageType.ORDER_CONFIRMATION,
                message_content="✅ Your order has been successfully cancelled.",
                whatsapp_message_id=msg_sid,
                is_incoming=False
            ).insert()
        
        # 3. Auto-resolve related cancellation alerts
        cancel_alerts = await Alert.find(
            Alert.order_id.ref.id == PydanticObjectId(order_id),
            Alert.reason == "CANCELLATION_REQUEST",
            Alert.resolved == False
        ).to_list()
        
        for alert in cancel_alerts:
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            await alert.save()
        
        return {
            "message": "Order cancelled and customer notified",
            "order_id": order_id,
            "alerts_resolved": len(cancel_alerts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-messages")
async def sync_messages_from_twilio():
    """
    Sync recent messages from Twilio to recover logs 
    missed while the app was offline.
    """
    try:
        twilio_messages = await whatsapp_service.get_messages(limit=50)
        synced_count = 0
        
        for msg in twilio_messages:
            sid = msg.get("sid")
            body = msg.get("body")
            status = msg.get("status")
            direction = msg.get("direction") # inbound or outbound-api
            
            # Skip if already logged
            exists = await MessageLog.find_one(MessageLog.whatsapp_message_id == sid)
            if exists:
                continue
            
            # Determine direction
            is_incoming = direction == "inbound"
            
            # Find phone number
            # inbound: From is customer
            # outbound: To is customer
            target_phone = msg.get("from") if is_incoming else msg.get("to")
            if target_phone:
                target_phone = target_phone.replace("whatsapp:", "")
            
            # Find user and order
            user = await User.find_one(User.whatsapp_number == target_phone)
            if not user:
                continue
                
            order = await Order.find(
                Order.user_id.id == user.id
            ).sort(-Order.created_at).first_or_none()
            
            if not order:
                continue
                
            # Log it
            msg_type = MessageType.CUSTOMER_REPLY if is_incoming else MessageType.ORDER_CONFIRMATION # Default guess
            
            # Try to be smarter about outgoing types if possible
            if not is_incoming:
                if "confirmed" in body.lower(): msg_type = MessageType.ORDER_CONFIRMATION
                elif "payment" in body.lower() and "received" in body.lower(): msg_type = MessageType.PAYMENT_CONFIRMATION
                elif "shipped" in body.lower(): msg_type = MessageType.SHIPPING_NOTIFICATION
                elif "out for delivery" in body.lower(): msg_type = MessageType.OUT_FOR_DELIVERY_NOTIFICATION
                elif "delivered" in body.lower(): msg_type = MessageType.DELIVERY_NOTIFICATION
            
            sentiment = None
            if is_incoming:
                sentiment = ai_service.classify_sentiment(body)
            
            # Create log entry
            date_sent_str = msg.get("date_sent")
            sent_at = datetime.utcnow()
            
            if date_sent_str:
                try:
                    # Twilio JSON API usually returns ISO 8601: "2021-12-01T21:05:01Z"
                    # But could be RFC 2822 in some versions: "Wed, 01 Dec 2021 21:05:01 +0000"
                    if "T" in date_sent_str:
                        # Try ISO parsing (Python 3.7+)
                        cleaned_date = date_sent_str.replace("Z", "+00:00")
                        sent_at = datetime.fromisoformat(cleaned_date).replace(tzinfo=None)
                    else:
                        import email.utils
                        parsed = email.utils.parsedate(date_sent_str)
                        if parsed:
                            sent_at = datetime(*parsed[:6])
                except Exception as parse_err:
                    print(f"Date parsing failed for {date_sent_str}: {parse_err}")
                    # sent_at stays as utcnow()

            # Ensure body is not None
            if not body:
                body = "[No content]"

            await MessageLog(
                order_id=order,
                message_type=msg_type,
                message_content=body,
                whatsapp_message_id=sid,
                is_incoming=is_incoming,
                sent_at=sent_at,
                sentiment=sentiment
            ).insert()
            
            synced_count += 1
            
        return {"message": f"Successfully synced {synced_count} messages from Twilio", "count": synced_count}
        
    except Exception as e:
        print(f"Error in sync-messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
