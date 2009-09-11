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


def send_all():
    """
    Send all non-deferred messages in the queue.
    
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
        for message in models.QueuedMessage.objects.non_deferred():
            result = send_message(message, smtp_connection=connection,
                                  blacklist=blacklist)
            if result == constants.RESULT_SENT:
                sent += 1
            elif result == constants.RESULT_FAILED:
                deferred += 1
            elif result == constants.RESULT_SENT:
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
    if smtp_connection is None:
        smtp_connection = SMTPConnection()
    opened_connection = False

    if blacklist is None:
        blacklisted = models.Blacklist.objects.filter(
                                            email=queued_message.to_address)
    else:
        blacklisted = queued_message.to_address in blacklist

    log_message = None
    if blacklisted:
        logging.info("Not sending to blacklisted email: %s" %
                     queued_message.to_address.encode("utf-8"))
        queued_message.delete()
        result = constants.RESULT_SKIPPED
    else:
        try:
            logging.info("Sending message to %s: %s" %
                         (queued_message.to_address.encode("utf-8"),
                          queued_message.subject.encode("utf-8")))
            opened_connection = smtp_connection.open()
            smtp_connection.connection.sendmail(queued_message.from_address,
                                                [queued_message.to_address],
                                                queued_message.encoded_message)
            queued_message.delete()
            result = constants.RESULT_SENT
        except (SocketError, smtplib.SMTPSenderRefused,
                smtplib.SMTPRecipientsRefused,
                smtplib.SMTPAuthenticationError), err:
            queued_message.defer()
            logging.info("Message to %s deferred due to failure: %s" %
                         (queued_message.to_address.encode("utf-8"), err))
            log_message = unicode(err)
            result = constants.RESULT_FAILED
    if log:
        models.Log.objects.create(queued_message=queued_message.message,
                                  result=result, log_message=log_message)

    if opened_connection:
        smtp_connection.close()
    return result
