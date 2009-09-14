from django.db import models
from django_mailer import constants
import datetime


class QueueManager(models.Manager):
    use_for_related_fields = True

    def high_priority(self):
        """
        Return a QuerySet of high priority queued messages.
        
        """
        return self.filter(priority=constants.PRIORITY_HIGH)

    def normal_priority(self):
        """
        Return a QuerySet of normal priority queued messages.
        
        """
        return self.filter(priority=constants.PRIORITY_NORMAL)

    def low_priority(self):
        """
        Return a QuerySet of low priority queued messages.
        
        """
        return self.filter(priority=constants.PRIORITY_LOW)

    def non_deferred(self):
        """
        Return a QuerySet containing all non-deferred queued messages.
        
        """
        return self.filter(deferred=None)

    def deferred(self):
        """
        Return a QuerySet of all deferred messages in the queue.
        
        """
        return self.exclude(deferred=None)

    def retry_deferred(self, max_retries=None, new_priority=None):
        """
        Reset the deferred flag for all deferred messages so they will be
        retried.
        
        If ``max_retries`` is set, deferred messages which have been retried
        more than this many times will *not* have their deferred flag reset.
        
        If ``new_priority`` is ``None`` (default), deferred messages retain
        their original priority level. Otherwise all reset deferred messages
        will be set to this priority level.
        
        """
        queryset = self.deferred()
        if max_retries:
            queryset.filter(retries__lte=max_retries)
        count = queryset.count()
        update_kwargs = dict(deferred=datetime.datetime.now(),
                             retries=models.F('retries')+1)
        if new_priority is not None:
            update_kwargs['priority'] = new_priority
        queryset.update(**update_kwargs)
        return count
