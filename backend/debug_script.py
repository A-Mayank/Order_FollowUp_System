
import asyncio
import os
from dotenv import load_dotenv
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from models.user import User
from models.order import Order
from models.message_log import MessageLog
from models.alert import Alert

load_dotenv()

async def debug_webhook():
    print('Starting DB connection...')
    client = AsyncIOMotorClient(os.getenv('MONGODB_URL'))
    await init_beanie(database=client.order_followup_db, document_models=[User, Order, MessageLog, Alert])
    print('DB Connected.')

    phone = '+917909067451'
    print(f'Searching for user: {phone}')
    
    user = await User.find_one(User.whatsapp_number == phone)
    if not user:
        print(' USER NOT FOUND')
        return

    print(f' Found user: {user.name} ({user.id})')
    
    # Debugging the exact query used in webhook
    order = await Order.find(Order.user_id.ref.id == user.id).sort(-Order.created_at).first_or_none()
    
    if not order:
        print(' NO ORDER FOUND for this user')
    else:
        print(f' Found most recent order: {order.id}')
        print(f'   Status: {order.status}')
        print(f'   Created: {order.created_at}')
        
        # Simulate processing logic check
        cancellable = ['CREATED', 'PAYMENT_PENDING', 'PAID', 'IN_PROCESS']
        print(f'   Is Cancellable? {order.status in cancellable}')

if __name__ == '__main__':
    asyncio.run(debug_webhook())

