from django.conf import settings
from django.core.management.base import NoArgsCommand
from django_mailer.engine import send_all
from optparse import make_option
from django_mailer import models
import logging
import sys


# Provide a way of temporarily pausing the sending of mail.
PAUSE_SEND = getattr(settings, "MAILER_PAUSE_SEND", False)
LOGGING_LEVEL = {'0': logging.ERROR, '1': logging.WARNING, '2': logging.INFO}

class Command(NoArgsCommand):
    help = 'Iterate the mail queue, attempting to send all mail.'
    option_list = NoArgsCommand.option_list + (
        make_option('-b', '--block-size', default=500, type='int',
            help='The number of messages to iterate before checking the queue '
                'again (in case new messages have been added while the queue '
                'is being cleared).'),
        make_option('-c', '--count', action='store_true', default=False,
            help='Return the number of messages in the queue (without '
                'actually sending any)'),
    )

    def handle_noargs(self, verbosity, block_size, count, **options):
        logging.basicConfig(level=LOGGING_LEVEL[verbosity],
                            format="%(message)s")
        if count:
            queued = models.QueuedMessage.objects.non_deferred().count()
            deferred = models.QueuedMessage.objects.non_deferred().count()
            sys.stdout.write('%s queued message%s (and %s deferred message%s).'
                             '\n' % (queued, queued != 1 and 's' or '',
                                     deferred, deferred != 1 and 's' or ''))
            sys.exit()
        # if PAUSE_SEND is turned on don't do anything.
        if not PAUSE_SEND:
            send_all(block_size)
        else:
            logging.warning("Sending is paused, exiting without sending "
                            "queued mail.")
