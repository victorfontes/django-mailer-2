VERSION = (0, 1, 0, "alpha")


def get_version():
    if VERSION[3] != "final":
        return "%s.%s.%s%s" % (VERSION[0], VERSION[1], VERSION[2], VERSION[3])
    else:
        return "%s.%s.%s" % (VERSION[0], VERSION[1], VERSION[2])


def send_mail(subject, message, from_email, recipient_list,
              fail_silently=False, auth_user=None, auth_password=None,
              priority=None):
    """
    Add a new message to the mail queue.

    This is a replacement for Django's ``send_mail`` core email method.
    
    The `fail_silently``, ``auth_user`` and ``auth_password`` arguments are
    only provided to match the signature of the emulated function. These
    arguments are not used.
    
    """
    from django.core.mail import EmailMessage
    from django.utils.encoding import force_unicode

    subject = force_unicode(subject)
    email_message = EmailMessage(subject, message, from_email,
                                 recipient_list)
    queue_email_message(email_message, priority=priority)


def mail_admins(subject, message, fail_silently=False, priority=None):
    """
    Add one or more new messages to the mail queue addressed to the site
    administrators (defined in ``settings.ADMINS``).

    This is a replacement for Django's ``mail_admins`` core email method.
    
    The ``fail_silently`` argument is only provided to match the signature of
    the emulated function. This argument is not used.
    
    """
    from django.conf import settings
    from django.utils.encoding import force_unicode

    subject = settings.EMAIL_SUBJECT_PREFIX + force_unicode(subject)
    from_email = settings.SERVER_EMAIL
    recipient_list = [recipient[1] for recipient in settings.ADMINS]
    send_mail(subject, message, from_email, recipient_list, priority=priority)


def mail_managers(subject, message, fail_silently=False, priority=None):
    """
    Add one or more new messages to the mail queue addressed to the site
    managers (defined in ``settings.MANAGERS``).

    This is a replacement for Django's ``mail_managers`` core email method.
    
    The ``fail_silently`` argument is only provided to match the signature of
    the emulated function. This argument is not used.
    
    """
    from django.conf import settings
    from django.utils.encoding import force_unicode

    subject = settings.EMAIL_SUBJECT_PREFIX + force_unicode(subject)
    from_email = settings.SERVER_EMAIL
    recipient_list = [recipient[1] for recipient in settings.MANAGERS]
    send_mail(subject, message, from_email, recipient_list, priority=priority)


def queue_email_message(email_message, priority=None):
    """
    Add new messages to the email queue.
    
    The ``email_message`` argument should be an instance of Django's core mail
    ``EmailMessage`` class.
    
    """
    from django_mailer import models

    count = 0
    for to_email in email_message.recipients():
        message = models.Message.objects.create(
            to_address=to_email, from_address=email_message.recipients,
            subject=email_message.subject,
            encoded_message=email_message.message().as_string())
        queued_message = models.QueuedMessage(message=message)
        if priority:
            queued_message.priority = priority
        queued_message.save()
        count += 1
    return count
