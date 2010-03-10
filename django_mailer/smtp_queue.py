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

        The messages can be assigned a priority in the queue by including
        an 'X-Mail-Queue-Priority' header set to one of the option strings
        in models.PRIORITIES.

        """
        if not email_messages:
            return

        from django_mailer import constants, queue_email_message

        num_sent = 0
        for email_message in email_messages:
            priority = email_message.extra_headers.pop('X-Mail-Queue-Priority', None)
            priority = constants.PRIORITIES.get(priority and priority.lower())
            queue_email_message(email_message, priority=priority)
            num_sent += 1
        return num_sent
