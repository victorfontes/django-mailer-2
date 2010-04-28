from django.conf import settings
from django_mailer import constants

# Provide a way of temporarily pausing the sending of mail.
PAUSE_SEND = getattr(settings, "MAILER_PAUSE_SEND", False)

USE_BACKEND = getattr(settings, 'MAILER_USE_BACKEND',
                      'django.core.mail.backends.smtp.EmailBackend')

# Default priorities for the mail_admins and mail_managers methods.
MAIL_ADMINS_PRIORITY = getattr(settings, 'MAILER_MAIL_ADMINS_PRIORITY',
                               constants.PRIORITY_HIGH)
MAIL_MANAGERS_PRIORITY = getattr(settings, 'MAILER_MAIL_MANAGERS_PRIORITY',
                                 None)

# When queue is empty, how long to wait (in seconds) before checking again.
EMPTY_QUEUE_SLEEP = getattr(settings, "MAILER_EMPTY_QUEUE_SLEEP", 30)

# Lock timeout value. how long to wait for the lock to become available.
# default behavior is to never wait for the lock to be available.
LOCK_WAIT_TIMEOUT = getattr(settings, "MAILER_LOCK_WAIT_TIMEOUT", -1)
