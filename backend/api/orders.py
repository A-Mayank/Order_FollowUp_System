from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from models.user import User
from models.order import Order, OrderStatus, PaymentStatus
from services.message_policy import message_policy


router = APIRouter(prefix="/api/orders", tags=["orders"])


# Request/Response Models
class CreateOrderRequest(BaseModel):
    name: str = Field(..., description="Customer name")
    whatsapp_number: str = Field(..., description="WhatsApp number with country code, e.g., +1234567890")
    product_name: Optional[str] = None
    amount: Optional[float] = None


class OrderResponse(BaseModel):
    id: str
    user_name: str
    whatsapp_number: str
    status: str
    payment_status: str
    automation_enabled: bool
    sentiment: str
    product_name: Optional[str] = None
    amount: Optional[float] = None
    created_at: datetime
    feedback_rating: Optional[int] = None
    feedback_text: Optional[str] = None


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(request: CreateOrderRequest):
    """
    Create a new order and send confirmation message.
    This is the main customer-facing endpoint.
    """
    print(f"Received order creation request for: {request.name} ({request.whatsapp_number})")
    try:
        # Create or find user
        user = await User.find_one(User.whatsapp_number == request.whatsapp_number)
        
        if not user:
            user = User(
                name=request.name,
                whatsapp_number=request.whatsapp_number
            )
            await user.insert()
        else:
            # Update name if changed
            if user.name != request.name:
                user.name = request.name
                await user.save()
        
        # Create order
        order = Order(
            user_id=user,
            status=OrderStatus.CREATED,
            payment_status=PaymentStatus.PENDING,
            product_name=request.product_name,
            amount=request.amount
        )
        await order.insert()
        
        # Send order confirmation via WhatsApp with AI personalization
        await message_policy.send_order_confirmation(order)
        
        return OrderResponse(
            id=str(order.id),
            user_name=user.name,
            whatsapp_number=user.whatsapp_number,
            status=order.status,
            payment_status=order.payment_status,
            automation_enabled=order.automation_enabled,
            sentiment=order.sentiment,
            product_name=order.product_name,
            amount=order.amount,
            created_at=order.created_at,
            feedback_rating=order.feedback_rating,
            feedback_text=order.feedback_text
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )


@router.patch("/{order_id}/payment-status")
async def update_payment_status(order_id: str, paid: bool):
    """Update payment status (simulates payment gateway callback)"""
    try:
        order = await Order.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if paid:
            order.payment_status = PaymentStatus.PAID
            
            # Auto-advance order status if it's still in initial stages
            if order.status in [OrderStatus.CREATED, OrderStatus.PAYMENT_PENDING]:
                order.status = OrderStatus.PAID
                
            await order.save()
            
            # Send payment confirmation
            await message_policy.send_payment_confirmation(order)
            
            return {"message": "Payment marked as paid", "order_id": order_id}
        else:
            order.payment_status = PaymentStatus.FAILED
            await order.save()
            return {"message": "Payment marked as failed", "order_id": order_id}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{order_id}/process")
async def mark_order_in_process(order_id: str):
    """Mark order as in process (packing) and send notification"""
    try:
        order = await Order.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = OrderStatus.IN_PROCESS
        await order.save()
        
        # Send notification
        await message_policy.send_in_process_notification(order)
        
        return {"message": "Order marked as in process", "order_id": order_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{order_id}/out-for-delivery")
async def mark_order_out_for_delivery(order_id: str):
    """Mark order as out for delivery and send notification"""
    try:
        order = await Order.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = OrderStatus.OUT_FOR_DELIVERY
        await order.save()
        
        # Send notification
        await message_policy.send_out_for_delivery_notification(order)
        
        return {"message": "Order marked as out for delivery", "order_id": order_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{order_id}/ship")
async def mark_order_shipped(
    order_id: str, 
    tracking_id: Optional[str] = None, 
    carrier: Optional[str] = None
):
    """Mark order as shipped and send notification"""
    try:
        order = await Order.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = OrderStatus.SHIPPED
        if tracking_id:
            order.tracking_id = tracking_id
        if carrier:
            order.carrier = carrier
            
        await order.save()
        
        # Send shipping notification
        await message_policy.send_shipping_notification(order)
        
        return {"message": "Order marked as shipped", "order_id": order_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{order_id}/deliver")
async def mark_order_delivered(order_id: str):
    """Mark order as delivered and send feedback request"""
    try:
        order = await Order.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = OrderStatus.DELIVERED
        await order.save()
        
        # Send delivery notification and feedback request
        await message_policy.send_delivery_notification(order)
        
        return {"message": "Order marked as delivered", "order_id": order_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """Get order details"""
    try:
        order = await Order.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        user = await order.user_id.fetch()
        
        return OrderResponse(
            id=str(order.id),
            user_name=user.name,
            whatsapp_number=user.whatsapp_number,
            status=order.status,
            payment_status=order.payment_status,
            automation_enabled=order.automation_enabled,
            sentiment=order.sentiment,
            product_name=order.product_name,
            amount=order.amount,
            created_at=order.created_at,
            feedback_rating=order.feedback_rating,
            feedback_text=order.feedback_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
