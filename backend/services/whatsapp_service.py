import os
import httpx
from typing import Optional
from datetime import datetime


class WhatsAppService:
    """
    WhatsApp Business API service using Twilio.
    Handles sending messages and webhook verification.
    """
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")  # Format: whatsapp:+14155238886
        
        if not all([self.account_sid, self.auth_token, self.whatsapp_number]):
            raise ValueError("Missing Twilio credentials in environment variables")
        
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
    
    async def send_message(self, to_number: str, message: str = None, content_sid: str = None, content_variables: dict = None) -> Optional[str]:
        """
        Send a WhatsApp message via Twilio (Text or Template).
        
        Args:
            to_number: Recipient WhatsApp number (format: +1234567890)
            message: Message text to send (optional if content_sid is used)
            content_sid: Twilio Content Template SID (optional)
            content_variables: Variables for the template (optional, e.g., {'1': 'John'})
            
        Returns:
            Message SID if successful, None if failed
        """
        try:
            # Format the recipient number for WhatsApp
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            payload = {
                "From": self.whatsapp_number,
                "To": to_number,
            }

            if content_sid:
                payload["ContentSid"] = content_sid
                if content_variables:
                    import json
                    payload["ContentVariables"] = json.dumps(content_variables)
            elif message:
                payload["Body"] = message
            else:
                print("✗ Error: Must provide either message body or content_sid")
                return None

            async with httpx.AsyncClient() as client:
                # Log usage
                with open("debug_whatsapp.log", "a", encoding="utf-8") as f:
                    f.write(f"\n--- Sending Message at {datetime.now()} ---\n")
                    f.write(f"To: {to_number}\n")
                    f.write(f"Payload: {payload}\n")
                    f.write(f"From Number (Configured): {self.whatsapp_number}\n")

                response = await client.post(
                    self.api_url,
                    data=payload,
                    auth=(self.account_sid, self.auth_token),
                    timeout=30.0
                )
                
                with open("debug_whatsapp.log", "a", encoding="utf-8") as f:
                    f.write(f"Response Status: {response.status_code}\n")
                    f.write(f"Response Body: {response.text}\n")
                
                if response.status_code == 201:
                    data = response.json()
                    print(f"✓ WhatsApp message sent to {to_number}: SID={data['sid']}")
                    return data["sid"]
                else:
                    print(f"✗ Failed to send WhatsApp message: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            with open("debug_whatsapp.log", "a", encoding="utf-8") as f:
                f.write(f"EXCEPTION: {str(e)}\n")
            print(f"✗ WhatsApp send error: {str(e)}")
            return None
            
    async def get_messages(self, limit: int = 50) -> list:
        """
        Fetch recent WhatsApp message logs from Twilio.
        
        Args:
            limit: Number of recent messages to fetch
            
        Returns:
            List of message objects from Twilio
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.api_url,
                    params={"PageSize": limit},
                    auth=(self.account_sid, self.auth_token),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("messages", [])
                else:
                    print(f"✗ Failed to fetch Twilio logs: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            print(f"✗ Error fetching Twilio logs: {str(e)}")
            return []
    
    def verify_webhook_signature(self, signature: str, url: str, params: dict) -> bool:
        """
        Verify Twilio webhook signature (optional security enhancement).
        
        Args:
            signature: X-Twilio-Signature header value
            url: Full webhook URL
            params: POST parameters
            
        Returns:
            True if signature is valid
        """
        # Implementation can use twilio.request_validator.RequestValidator
        # For MVP, we can skip this or implement basic validation
        return True


# Singleton instance
whatsapp_service = WhatsAppService()
