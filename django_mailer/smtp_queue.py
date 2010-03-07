"""Queued SMTP email backend class."""

import logging
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger('django_mailer')
logger.setLevel(logging.DEBUG)


class EmailBackend(BaseEmailBackend):
    '''
    A wrapper that manages a queued SMTP system.

    '''

    def send_messages(self, email_messages):
        """
        Add new messages to the email queue.

        The ``email_messages`` argument should be one or more instances
        of Django's core mail ``EmailMessage`` class.

        The messages can be assigned a priority in the queue by using the
        ``priority`` argument.

        """
        if not email_messages:
            return

        from django_mailer import constants, models

        num_sent = 0
        for email_message in email_messages:
            count = 0
            for to_email in email_message.recipients():
                message = models.Message.objects.create(
                    to_address=to_email, from_address=email_message.from_email,
                    subject=email_message.subject,
                    encoded_message=email_message.message().as_string())
                queued_message = models.QueuedMessage(message=message)
                if priority:
                    queued_message.priority = priority
                queued_message.save()
                count += 1
            num_sent += 1
        return num_sent
