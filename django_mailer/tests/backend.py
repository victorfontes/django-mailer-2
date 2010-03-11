from django.core.mail import EmailMessage
from django_mailer import models, constants, queue_email_message
from django_mailer.tests.base import MailerTestCase
from django.conf import settings
from django.core import mail
try:
    from django.core.mail import backends
    EMAIL_BACKEND_SUPPORT = True
except ImportError:
    # Django version < 1.2
    EMAIL_BACKEND_SUPPORT = False


class TestBackend(MailerTestCase):
    """
    Backend tests for the django_mailer app.

    For Django versions less than 1.2, these tests are still run but they just
    use the queue_email_message funciton rather than directly sending messages.

    """

    def setUp(self):
        super(TestBackend, self).setUp()
        if EMAIL_BACKEND_SUPPORT:
            if hasattr(settings, 'EMAIL_BACKEND'):
                self.old_email_backend = settings.EMAIL_BACKEND
            else:
                self.old_email_backend = None
            settings.EMAIL_BACKEND = 'django_mailer.smtp_queue.EmailBackend'

    def tearDown(self):
        super(TestBackend, self).tearDown()
        if EMAIL_BACKEND_SUPPORT:
            if self.old_email_backend:
                settings.EMAIL_BACKEND = self.old_email_backend
            else:
                delattr(settings, 'EMAIL_BACKEND')

    def send_message(self, msg):
        if EMAIL_BACKEND_SUPPORT:
            msg.send()
        else:
            queue_email_message(msg)

    def testQueuedMessagePriorities(self):
        # high priority message
        msg = EmailMessage(subject='subject', body='body',
                        from_email='mail_from@abc.com', to=['mail_to@abc.com'],
                        headers={'X-Mail-Queue-Priority': 'high'})
        self.send_message(msg)
        
        # low priority message
        msg = EmailMessage(subject='subject', body='body',
                        from_email='mail_from@abc.com', to=['mail_to@abc.com'],
                        headers={'X-Mail-Queue-Priority': 'low'})
        self.send_message(msg)
        
        # normal priority message
        msg = EmailMessage(subject='subject', body='body',
                        from_email='mail_from@abc.com', to=['mail_to@abc.com'],
                        headers={'X-Mail-Queue-Priority': 'normal'})
        self.send_message(msg)
        
        # normal priority message (no explicit priority header)
        msg = EmailMessage(subject='subject', body='body',
                        from_email='mail_from@abc.com', to=['mail_to@abc.com'])
        self.send_message(msg)
        
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
            self.assertEqual(queued_message.priority,
                             constants.PRIORITY_NORMAL)

    def testSendMessageNowPriority(self):
        # NOW priority message
        msg = EmailMessage(subject='subject', body='body',
                        from_email='mail_from@abc.com', to=['mail_to@abc.com'],
                        headers={'X-Mail-Queue-Priority': 'now'})
        self.send_message(msg)

        queued_messages = models.QueuedMessage.objects.all()
        self.assertEqual(queued_messages.count(), 0)
        self.assertEqual(len(mail.outbox), 1)
