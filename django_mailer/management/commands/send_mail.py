from django.conf import settings
from django.core.management.base import NoArgsCommand
from django_mailer.engine import send_all
from optparse import make_option
import logging


# Provide a way of temporarily pausing the sending of mail.
PAUSE_SEND = getattr(settings, "MAILER_PAUSE_SEND", False)
LOGGING_LEVEL = {'0': logging.CRITICAL, '1': logging.INFO, '2': logging.DEBUG}

class Command(NoArgsCommand):
    help = 'Iterate the mail queue, attempting to send all mail.'
    option_list = NoArgsCommand.option_list + (
        make_option('-b', '--block-size', default=500, type='int',
            help='The number of messages to iterate before checking the queue '
                'again (in case new messages have been added while the queue '
                'is being cleared).'),
    )

    def handle_noargs(self, verbosity, block_size, **options):
        logging.basicConfig(level=LOGGING_LEVEL[verbosity],
                            format="%(message)s")
        # if PAUSE_SEND is turned on don't do anything.
        if not PAUSE_SEND:
            send_all(block_size)
        else:
            logging.warning("Sending is paused, exiting without sending "
                            "queued mail.")
