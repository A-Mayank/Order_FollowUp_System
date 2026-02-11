from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta

from models.order import Order, PaymentStatus
from services.message_policy import message_policy


class ReminderScheduler:
    """
    Background scheduler for automated payment reminders and alert checks.
    Uses APScheduler for time-based automation.
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Start the scheduler with all jobs"""
        
        # Job 1: Check for 5-minute payment reminders (runs every 1 minute)
        self.scheduler.add_job(
            self.send_5min_reminders,
            trigger=IntervalTrigger(minutes=1),
            id="payment_reminder_5min",
            name="Send 5-minute payment reminders",
            replace_existing=True
        )
        
        # Job 2: Check for 24-hour payment reminders (runs every hour)
        self.scheduler.add_job(
            self.send_24hour_reminders,
            trigger=IntervalTrigger(hours=1),
            id="payment_reminder_24hour",
            name="Send 24-hour payment reminders",
            replace_existing=True
        )
        
        # Job 3: Check for no-response alerts (runs every 4 hours)
        self.scheduler.add_job(
            message_policy.check_no_response_alerts,
            trigger=IntervalTrigger(hours=4),
            id="no_response_check",
            name="Check for no-response alerts",
            replace_existing=True
        )
        
        self.scheduler.start()
        print("✓ Scheduler started with automated jobs")
    
    def shutdown(self):
        """Gracefully shutdown the scheduler"""
        self.scheduler.shutdown()
        print("✓ Scheduler shutdown")
    
    async def send_5min_reminders(self):
        """Send first payment reminder 5 minutes after order creation"""
        try:
            # Find orders created ~5 minutes ago with pending payment
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            grace_period = datetime.utcnow() - timedelta(minutes=10)  # 5-min window
            
            orders = await Order.find(
                Order.payment_status == PaymentStatus.PENDING,
                Order.automation_enabled == True,
                Order.payment_reminder_1_sent_at == None,
                Order.created_at <= cutoff_time,
                Order.created_at >= grace_period
            ).to_list()
            
            for order in orders:
                print(f"⏰ Sending 5-min payment reminder for order {order.id}")
                await message_policy.send_payment_reminder(order, reminder_number=1)
            
            if orders:
                print(f"✓ Sent {len(orders)} 5-minute payment reminders")
                
        except Exception as e:
            print(f"Error in 15min reminder job: {str(e)}")
    
    async def send_24hour_reminders(self):
        """Send final payment reminder 24 hours after order creation"""
        try:
            # Find orders created ~24 hours ago with pending payment
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            grace_period = datetime.utcnow() - timedelta(hours=25)  # 1-hour window
            
            orders = await Order.find(
                Order.payment_status == PaymentStatus.PENDING,
                Order.automation_enabled == True,
                Order.payment_reminder_2_sent_at == None,
                Order.created_at <= cutoff_time,
                Order.created_at >= grace_period
            ).to_list()
            
            for order in orders:
                print(f"⏰ Sending 24-hour payment reminder for order {order.id}")
                await message_policy.send_payment_reminder(order, reminder_number=2)
            
            if orders:
                print(f"✓ Sent {len(orders)} 24-hour payment reminders")
                
        except Exception as e:
            print(f"Error in 24hour reminder job: {str(e)}")


# Singleton instance
reminder_scheduler = ReminderScheduler()
