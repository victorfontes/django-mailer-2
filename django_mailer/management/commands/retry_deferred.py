from django.core.management.base import NoArgsCommand
from django_mailer import models
from optparse import make_option
import logging


class Command(NoArgsCommand):
    help = 'Place deferred messages back in the queue.'
    option_list = NoArgsCommand.option_list + (
        make_option('-m', '--max-retries', type='int',
            help="Don't reset deferred messages with more than this many "
                "retries."),
    )

    def handle_noargs(self, max_retries, **options):
        count = models.QueuedMessage.objects.retry_deferred(
                                                    max_retries=max_retries)
        logging.info("%s deferred message%s placed back in the queue" %
                     (count, count != 1 and 's' or ''))
