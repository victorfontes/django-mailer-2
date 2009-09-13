"""
The "engine room" of django mailer.

Methods here actually handle the sending of queued messages.

"""
from django.conf import settings
from django.core.mail import SMTPConnection
from lockfile import FileLock, AlreadyLocked, LockTimeout
from django_mailer import constants, models
from socket import error as SocketError
import logging
import smtplib
import time


# When queue is empty, how long to wait (in seconds) before checking again.
EMPTY_QUEUE_SLEEP = getattr(settings, "MAILER_EMPTY_QUEUE_SLEEP", 30)

# Lock timeout value. how long to wait for the lock to become available.
# default behavior is to never wait for the lock to be available.
LOCK_WAIT_TIMEOUT = getattr(settings, "MAILER_LOCK_WAIT_TIMEOUT", -1)


def _message_queue(block_size):
    """
    A generator which iterates queued messages in blocks so that new
    prioritised messages can be inserted during iteration of a large number of
    queued messages.
    
    To avoid an infinite loop, yielded messages *must* be deleted or deferred.
    
    """
    def get_block():
        queue = models.QueuedMessage.objects.non_deferred().select_related()
        if block_size:
            queue = queue[:block_size]
        return queue
    queue = get_block()
    while queue:
        for message in queue:
            yield message
        queue = get_block()


def send_all(block_size=500):
    """
    Send all non-deferred messages in the queue.
    
    A lock file is used to ensure that this process can not be started again
    while it is already running.
    
    The ``block_size`` argument allows for queued messages to be iterated in
    blocks, allowing new prioritised messages to be inserted during iteration
    of a large number of queued messages.
    
    """
    lock = FileLock("send_mail")

    logging.debug("Acquiring lock...")
    try:
        lock.acquire(LOCK_WAIT_TIMEOUT)
    except AlreadyLocked:
        logging.debug("Lock already in place. Exiting.")
        return
    except LockTimeout:
        logging.debug("Waiting for the lock timed out. Exiting.")
        return
    logging.debug("Lock acquired.")

    start_time = time.time()

    sent = deferred = skipped = 0

    try:
        connection = SMTPConnection()
        blacklist = models.Blacklist.objects.values_list('email', flat=True)
        connection.open()
        for message in _message_queue(block_size):
            result = send_message(message, smtp_connection=connection,
                                  blacklist=blacklist)
            if result == constants.RESULT_SENT:
                sent += 1
            elif result == constants.RESULT_FAILED:
                deferred += 1
            elif result == constants.RESULT_SKIPPED:
                skipped += 1
        connection.close()
    finally:
        logging.debug("Releasing lock...")
        lock.release()
        logging.debug("Lock released.")

    logging.info("")
    logging.info("%s sent, %s deferred, %s skipped." % (sent, deferred,
                                                        skipped))
    logging.info("Completed in %.2f seconds." % (time.time() - start_time))


def send_loop(empty_queue_sleep=None):
    """
    Loop indefinitely, checking queue at intervals and sending and queued
    messages.
    
    The interval (in seconds) can be provided as the ``empty_queue_sleep``
    argument. The default is attempted to be retrieved from the
    ``MAILER_EMPTY_QUEUE_SLEEP`` setting (or if not set, 30s is used).
    
    """
    empty_queue_sleep = empty_queue_sleep or EMPTY_QUEUE_SLEEP
    while True:
        while not models.QueuedMessage.objects.all():
            logging.debug("Sleeping for %s seconds before checking queue "
                          "again." % empty_queue_sleep)
            time.sleep(empty_queue_sleep)
        send_all()


def send_message(queued_message, smtp_connection=None, blacklist=None,
                 log=True):
    """
    Send a queued message, returning a response code as to the action taken.
    
    The response codes can be found in ``django_mailer.constants``. The
    response will be either ``RESULT_SKIPPED`` for a blacklisted email,
    ``RESULT_FAILED`` for a deferred message or ``RESULT_SENT`` for a
    successful sent message.
    
    To allow optimizations if multiple messages are to be sent, an SMTP
    connection can be provided and a list of blacklisted email addresses.
    Otherwise an SMTP connection will be opened to send this message and the
    email recipient address checked against the ``Blacklist`` table.
    
    If the message recipient is blacklisted, the message will be removed from
    the queue without being sent. Otherwise, the message is attempted to be
    sent with an SMTP failure resulting in the message being flagged as
    deferred so it can be tried again later.
    
    By default, a log is created as to the action. Either way, the original
    message is not deleted.
    
    """
    message = queued_message.message
    if smtp_connection is None:
        smtp_connection = SMTPConnection()
    opened_connection = False

    if blacklist is None:
        blacklisted = models.Blacklist.objects.filter(email=message.to_address)
    else:
        blacklisted = message.to_address in blacklist

    log_message = ''
    if blacklisted:
        logging.info("Not sending to blacklisted email: %s" %
                     message.to_address.encode("utf-8"))
        queued_message.delete()
        result = constants.RESULT_SKIPPED
    else:
        try:
            logging.info("Sending message to %s: %s" %
                         (message.to_address.encode("utf-8"),
                          message.subject.encode("utf-8")))
            opened_connection = smtp_connection.open()
            smtp_connection.connection.sendmail(message.from_address,
                                                [message.to_address],
                                                message.encoded_message)
            queued_message.delete()
            result = constants.RESULT_SENT
        except (SocketError, smtplib.SMTPSenderRefused,
                smtplib.SMTPRecipientsRefused,
                smtplib.SMTPAuthenticationError), err:
            queued_message.defer()
            logging.info("Message to %s deferred due to failure: %s" %
                         (message.to_address.encode("utf-8"), err))
            log_message = unicode(err)
            result = constants.RESULT_FAILED
    if log:
        models.Log.objects.create(message=message, result=result,
                                  log_message=log_message)

    if opened_connection:
        smtp_connection.close()
    return result
