from django.core.management.base import NoArgsCommand
from django_mailer import models
import logging


class Command(NoArgsCommand):
    help = 'Attempt to resend any deferred mail.'
    
    def handle_noargs(self, **options):
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")
        count = models.QueuedMessage.objects.retry_deferred()
        logging.info("%s message(s) removed from deferred" % count)
