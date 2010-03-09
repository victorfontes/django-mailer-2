from django.core.mail import EmailMessage
from django_mailer import models, constants
from django.test import TestCase
from django.conf import settings


class TestBackend(TestCase):
    """Tests for the django_mailer app"""

    def setUp(self):
        if settings.EMAIL_BACKEND:
            self.old_email_backend = settings.EMAIL_BACKEND
        else:
            self.old_email_backend = None
        settings.EMAIL_BACKEND = 'django_mailer.smtp_queue.EmailBackend'

    def tearDown(self):
        if self.old_email_backend:
            settings.EMAIL_BACKEND = self.old_email_backend
        else:
            settings.pop('EMAIL_BACKEND')
        
    def testMessagePriority(self):
        try:
            # only test with Django version >= 1.2
            from django.core.mail import get_connection
            
            # high priority message
            msg = EmailMessage(subject='subject', body='body',
                                from_email='mail_from@abc.com', to=['mail_to@abc.com'],
                                headers={'X-Mail-Queue-Priority': 'high'})
            msg.send()
            
            # low priority message
            msg = EmailMessage(subject='subject', body='body',
                                from_email='mail_from@abc.com', to=['mail_to@abc.com'],
                                headers={'X-Mail-Queue-Priority': 'low'})
            msg.send()
            
            # normal priority message
            msg = EmailMessage(subject='subject', body='body',
                                from_email='mail_from@abc.com', to=['mail_to@abc.com'],
                                headers={'X-Mail-Queue-Priority': 'normal'})
            msg.send()
            
            # normal priority message (no explicit priority header)
            msg = EmailMessage(subject='subject', body='body',
                                from_email='mail_from@abc.com', to=['mail_to@abc.com'])
            msg.send()
            
            qs = models.QueuedMessage.objects.high_priority()
            self.assertEqual(qs.count(), 1)
            queued_message = qs[0]
            self.assertEqual(queued_message.priority, constants.PRIORITY_HIGH)
            
            qs = models.QueuedMessage.objects.low_priority()
            self.assertEqual(qs.count(), 1)
            queued_message = qs[0]
            self.assertEqual(queued_message.priority, constants.PRIORITY_LOW)
            
            qs = models.QueuedMessage.objects.normal_priority()
            self.assertEqual(qs.count(), 2)
            for queued_message in qs:
                self.assertEqual(queued_message.priority, constants.PRIORITY_NORMAL)
        except ImportError:
            pass
