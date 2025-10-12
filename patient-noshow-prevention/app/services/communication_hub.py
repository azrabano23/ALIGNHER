import os
from typing import Dict, Optional
from twilio.rest import Client as TwilioClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import logging

logger = logging.getLogger(__name__)

class CommunicationHub:
    def __init__(self):
        # Twilio setup
        self.twilio_client = None
        if os.getenv('TWILIO_ACCOUNT_SID') and os.getenv('TWILIO_AUTH_TOKEN'):
            self.twilio_client = TwilioClient(
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            )
            self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        # SendGrid setup
        self.sendgrid_client = None
        if os.getenv('SENDGRID_API_KEY'):
            self.sendgrid_client = SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
            self.from_email = os.getenv('FROM_EMAIL', 'noreply@healthsystem.com')
    
    def send_sms(self, to: str, message: str) -> Dict:
        """
        Send SMS message via Twilio
        """
        if not self.twilio_client:
            logger.error("Twilio not configured")
            return {'delivered': False, 'error': 'Twilio not configured'}
        
        if not to:
            logger.error("No phone number provided")
            return {'delivered': False, 'error': 'No phone number provided'}
        
        try:
            # Clean phone number
            phone = self._clean_phone_number(to)
            
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=phone
            )
            
            logger.info(f"SMS sent successfully to {phone}, SID: {message_obj.sid}")
            
            return {
                'delivered': True,
                'message_sid': message_obj.sid,
                'status': message_obj.status,
                'to': phone
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to}: {e}")
            return {'delivered': False, 'error': str(e)}
    
    def send_email(self, to: str, subject: str, body: str, html_body: Optional[str] = None) -> Dict:
        """
        Send email via SendGrid
        """
        if not self.sendgrid_client:
            logger.error("SendGrid not configured")
            return {'delivered': False, 'error': 'SendGrid not configured'}
        
        if not to:
            logger.error("No email address provided")
            return {'delivered': False, 'error': 'No email address provided'}
        
        try:
            # Create email
            message = Mail(
                from_email=self.from_email,
                to_emails=to,
                subject=subject,
                plain_text_content=body
            )
            
            if html_body:
                message.html_content = html_body
            
            # Send email
            response = self.sendgrid_client.send(message)
            
            logger.info(f"Email sent successfully to {to}, status: {response.status_code}")
            
            return {
                'delivered': True,
                'status_code': response.status_code,
                'message_id': response.headers.get('X-Message-Id'),
                'to': to
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return {'delivered': False, 'error': str(e)}
    
    def send_notification(self, channel: str, to: str, content: Dict) -> Dict:
        """
        Send notification via specified channel
        """
        if channel == 'sms':
            return self.send_sms(to, content.get('message', ''))
        elif channel == 'email':
            return self.send_email(
                to=to,
                subject=content.get('subject', 'Appointment Notification'),
                body=content.get('body', ''),
                html_body=content.get('html_body')
            )
        else:
            return {'delivered': False, 'error': f'Unsupported channel: {channel}'}
    
    def _clean_phone_number(self, phone: str) -> str:
        """
        Clean and format phone number for SMS
        """
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Add country code if not present
        if len(digits) == 10:
            digits = '1' + digits
        
        # Format as +1XXXXXXXXXX
        return f'+{digits}'
    
    def get_sms_status(self, message_sid: str) -> Dict:
        """
        Get SMS delivery status from Twilio
        """
        if not self.twilio_client:
            return {'error': 'Twilio not configured'}
        
        try:
            message = self.twilio_client.messages(message_sid).fetch()
            
            return {
                'sid': message.sid,
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'date_sent': message.date_sent,
                'date_updated': message.date_updated
            }
            
        except Exception as e:
            logger.error(f"Failed to get SMS status for {message_sid}: {e}")
            return {'error': str(e)}
    
    def handle_sms_webhook(self, webhook_data: Dict) -> Dict:
        """
        Handle SMS status webhooks from Twilio
        """
        message_sid = webhook_data.get('MessageSid')
        status = webhook_data.get('MessageStatus')
        
        logger.info(f"SMS webhook received - SID: {message_sid}, Status: {status}")
        
        # Update intervention status in database based on webhook
        # This would be implemented to update the Intervention model
        
        return {'processed': True, 'message_sid': message_sid, 'status': status}
    
    def handle_email_webhook(self, webhook_data: Dict) -> Dict:
        """
        Handle email event webhooks from SendGrid
        """
        event_type = webhook_data.get('event')
        message_id = webhook_data.get('sg_message_id')
        email = webhook_data.get('email')
        
        logger.info(f"Email webhook received - Event: {event_type}, Email: {email}")
        
        # Update intervention status based on email events
        # Events: delivered, opened, clicked, bounced, etc.
        
        return {'processed': True, 'event': event_type, 'message_id': message_id}

# Singleton instance
communication_hub = CommunicationHub()
