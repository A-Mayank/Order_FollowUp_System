from fastapi import APIRouter, Request, Response, HTTPException
from services.message_policy import message_policy
from beanie import PydanticObjectId


router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/whatsapp")
async def handle_whatsapp_webhook(request: Request):
    """
    Webhook endpoint for incoming WhatsApp messages from Twilio.
    
    Twilio sends POST requests with form data when customers reply.
    """
    try:
        # Parse Twilio webhook data
        form_data = await request.form()
        print(f"DEBUG: Webhook Payload: {dict(form_data)}")
        
        # Extract relevant fields
        from_number = form_data.get("From", "")
        message_body = form_data.get("Body", "")
        
        # Check for interactive message payloads
        button_payload = form_data.get("ButtonPayload")
        list_id = form_data.get("ListId")
        
        if button_payload:
            print(f"🔹 Received Button Payload: {button_payload}")
            message_body = button_payload 
        elif list_id:
            print(f"🔹 Received List ID: {list_id}")
            message_body = list_id
        
        # Clean the phone number (handle whatsapp: prefix and ensure +)
        phone_number = from_number.replace("whatsapp:", "")
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"
        
        print(f"📥 Incoming WhatsApp message from {phone_number}: {message_body}")
        
        # Find user
        from models.user import User
        from models.order import Order
        
        user = await User.find_one(User.whatsapp_number == phone_number)
        
        if user:
            print(f"DEBUG: Found user {user.name} for number {phone_number}")
            
            # Diagnostic: Count all orders
            all_orders_count = await Order.find_all().count()
            print(f"DEBUG: Total orders in system: {all_orders_count}")
            
            # Get the most recent order 
            # Using .id for the link comparison
            order = await Order.find(
                Order.user_id.id == user.id
            ).sort(-Order.created_at).first_or_none()
            
            if order:
                print(f"DEBUG: Found order {order.id} (status: {order.status}) for user {user.name}")
                # Process reply
                await message_policy.process_customer_reply(order.id, message_body)
            else:
                print(f"⚠️ No orders found for user {phone_number} (User ID: {user.id})")
        else:
            print(f"⚠️ Unknown user {phone_number}. Webhook cannot proceed.")
        
        return Response(content="", status_code=200)
        
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        # Still return 200 to prevent Twilio from retrying
        return Response(content="", status_code=200)


@router.get("/whatsapp")
async def verify_whatsapp_webhook(request: Request):
    """
    Webhook verification endpoint (for initial Twilio setup).
    Twilio may send a GET request to verify the webhook URL.
    """
    return {"status": "Webhook endpoint is active"}
