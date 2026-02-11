import os
from typing import Optional
import google.generativeai as genai
from openai import OpenAI


class AIService:
    def __init__(self):
        self.ai_provider = os.getenv("AI_PROVIDER", "gemini").lower()  # Default to Gemini
        
        if self.ai_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required when AI_PROVIDER=openai")
            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        elif self.ai_provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required when AI_PROVIDER=gemini")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        else:
            raise ValueError(f"Unsupported AI provider: {self.ai_provider}")
    
    def personalize_message(self, customer_name: str, order_status: str, product_name: Optional[str] = None) -> str:
        try:
            prompt = self._build_personalization_prompt(customer_name, order_status, product_name)
            
            if self.ai_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a friendly customer service assistant. Generate short, warm WhatsApp messages (max 2-3 sentences)."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=100
                )
                return response.choices[0].message.content.strip()
            
            elif self.ai_provider == "gemini":
                response = self.model.generate_content(prompt)
                return response.text.strip()
                
        except Exception as e:
            print(f"AI personalization failed: {str(e)}")
            # Fallback to static message
            return self._get_fallback_message(customer_name, order_status, product_name)
    
    def classify_sentiment(self, customer_reply: str) -> str:
        try:
            prompt = f"""Classify the sentiment of this customer message as exactly one word: positive, neutral, or negative.

Customer message: "{customer_reply}"

Respond with only one word: positive, neutral, or negative."""

            if self.ai_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a sentiment classifier. Respond with exactly one word: positive, neutral, or negative."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=10
                )
                sentiment = response.choices[0].message.content.strip().lower()
            
            elif self.ai_provider == "gemini":
                response = self.model.generate_content(prompt)
                sentiment = response.text.strip().lower()
            
            # Validate response
            if sentiment in ["positive", "neutral", "negative"]:
                return sentiment
            else:
                return "neutral"  # Default
                
        except Exception as e:
            print(f"AI sentiment classification failed: {str(e)}")
            return "neutral"  # Safe default
            
    def extract_feedback_rating(self, feedback_text: str) -> Optional[int]:
        """
        Extract a numerical rating (1-5) from feedback text using AI.
        """
        try:
            prompt = f"""Extract a numerical rating from 1 to 5 from this customer feedback.
If no clear rating is found, return 0.
Return ONLY a single number.

Customer feedback: "{feedback_text}"

Rating (1-5):"""

            if self.ai_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a data extractor. Respond with only a single digit from 0 to 5."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=5
                )
                rating_str = response.choices[0].message.content.strip()
            
            elif self.ai_provider == "gemini":
                response = self.model.generate_content(prompt)
                rating_str = response.text.strip()
            
            # Extract first digit found
            import re
            match = re.search(r'[0-5]', rating_str)
            if match:
                rating = int(match.group())
                return rating if rating > 0 else None
            return None
                
        except Exception as e:
            print(f"AI rating extraction failed: {str(e)}")
            return None
    
    def _build_personalization_prompt(self, customer_name: str, order_status: str, product_name: Optional[str]) -> str:
        """Build prompt for message personalization"""
        product_info = f" for {product_name}" if product_name else ""
        fish_theme = "Please use fish-themed puns, nautical language, and a friendly 'fresh catch' personality. Avoid being generic."
        
        prompts = {
            "CREATED": f"Write a friendly WhatsApp order confirmation message for {customer_name}{product_info}. {fish_theme}",
            "PAYMENT_PENDING": f"Write a gentle payment reminder for {customer_name}{product_info}. {fish_theme}",
            "PAID": f"Write a celebratory message for {customer_name} confirming that we received their payment for {product_name}. Be enthusiastic and use nautical themes! {fish_theme}",
            "IN_PROCESS": f"Write a short update for {customer_name} that their order{product_info} is being prepared. {fish_theme}",
            "SHIPPED": f"Write an exciting shipping notification for {customer_name}{product_info}. Use nautical terms like 'sailing your way' or 'anchors aweigh'. {fish_theme}",
            "OUT_FOR_DELIVERY": f"Write a quick alert for {customer_name} that their order{product_info} is out for delivery today. Use terms like 'splashing down soon'. {fish_theme}",
            "DELIVERED": f"Write a warm thank you message for {customer_name} for their order{product_info} that has just been delivered. Mention it's the catch of the day! {fish_theme}",
        }
        
        return prompts.get(order_status, f"Write a friendly fish-themed message to {customer_name} about their order{product_info}.")
    
    def _get_fallback_message(self, customer_name: str, order_status: str, product_name: Optional[str]) -> str:
        """Static fallback messages when AI fails"""
        product_info = f" ({product_name})" if product_name else ""
        
        fallbacks = {
            "CREATED": f"Hi {customer_name}, your catch{product_info} has been confirmed. We'll have it swimming your way soon.",
            "PAYMENT_PENDING": f"Hi {customer_name}, just a friendly nudge that payment for your order{product_info} is pending. Please settle the bill so we can get fishing.",
            "PAID": f"Payment received. Thanks {customer_name}, we're getting your fresh catch{product_info} ready for the journey.",
            "IN_PROCESS": f"Hi {customer_name}, your order{product_info} is currently being packed with ice and care.",
            "SHIPPED": f"Great news {customer_name}, your order{product_info} has been shipped and is sailing your way.",
            "OUT_FOR_DELIVERY": f"Heads up {customer_name}, your fresh order{product_info} is out for delivery today. Get the grill ready.",
            "DELIVERED": f"Hi {customer_name}, your order{product_info} has been delivered. It's the catch of the day. Please give your feedback.",
        }
        
        return fallbacks.get(order_status, f"Hi {customer_name}, update on your order{product_info}.")


# Singleton instance
ai_service = AIService()
