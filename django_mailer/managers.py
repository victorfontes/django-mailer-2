from django.db import models
from django_mailer import constants


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
        return self.filter(deferred=False)

    def deferred(self):
        """
        Return a QuerySet of all deferred messages in the queue.
        
        """
        return self.filter(deferred=True)

    def retry_deferred(self, new_priority=None):
        """
        Reset the deferred flag for all deferred messages so they will be
        retried.
        
        """
        count = self.deferred().count()
        update_kwargs = dict(deferred=False, retries=models.F('retries')+1)
        if new_priority is not None:
            update_kwargs['priority'] = new_priority
        self.deferred().update(**update_kwargs)
        return count
