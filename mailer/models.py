from datetime import datetime
from django.db import models
from mailer import constants

PRIORITIES = (
    (constants.PRIORITY_HIGH, 'high'),
    (constants.PRIORITY_NORMAL, 'normal'),
    (constants.PRIORITY_LOW, 'low'),
)



class MessageManager(models.Manager):
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
        return self.exclude(priority=constants.PRIORITY_DEFERRED)
    
    def deferred(self):
        """
        Return a QuerySet of all deferred messages in the queue.
        
        """
        return self.filter(priority=constants.PRIORITY_DEFERRED)
    
    def retry_deferred(self, new_priority=constants.PRIORITY_NORMAL):
        """
        Set all 
        """
        count = 0
        for message in self.deferred():
            if message.retry(new_priority):
                count += 1
        return count


class Message(models.Model):
    
    objects = MessageManager()
    
    to_address = models.CharField(max_length=50)
    from_address = models.CharField(max_length=50)
    subject = models.CharField(max_length=100)
    message_body = models.TextField()
    when_added = models.DateTimeField(default=datetime.now)
    priority = models.PositiveSmallIntegerField(choices=PRIORITIES,
                                            default=constants.PRIORITY_NORMAL)
    deferred = models.BooleanField()
    # @@@ campaign?
    # @@@ content_type?
    
    def defer(self, save=True):
        self.deferred = True
        if save:
            self.save()
    
    def retry(self, new_priority=None, save=True):
        if not self.deferred:
            return False
        self.deferred = False
        if new_priority is not None:
            self.priority = new_priority
        if save: 
            self.save()
        return True


class DontSendEntryManager(models.Manager):
    
    def has_address(self, address):
        """
        is the given address on the don't send list?
        """
        
        if self.filter(to_address=address).count() > 0: # @@@ is there a better way?
            return True
        else:
            return False


class DontSendEntry(models.Model):
    
    objects = DontSendEntryManager()
    
    to_address = models.CharField(max_length=50)
    when_added = models.DateTimeField()
    # @@@ who added?
    # @@@ comment field?
    
    class Meta:
        verbose_name = 'don\'t send entry'
        verbose_name_plural = 'don\'t send entries'
    

RESULT_CODES = (
    (constants.RESULT_SENT, 'success'),
    (constants.RESULT_SKIPPED, 'not sent (opt out)'),
    (constants.RESULT_FAILED, 'failure'),
)



class MessageLogManager(models.Manager):
    
    def log(self, message, result_code, log_message = ''):
        """
        create a log entry for an attempt to send the given message and
        record the given result and (optionally) a log message
        """
        
        message_log = self.create(
            to_address = message.to_address,
            from_address = message.from_address,
            subject = message.subject,
            message_body = message.message_body,
            when_added = message.when_added,
            priority = message.priority,
            # @@@ other fields from Message
            result = result_code,
            log_message = log_message,
        )
        message_log.save()


class MessageLog(models.Model):
    
    objects = MessageLogManager()
    
    # fields from Message
    to_address = models.CharField(max_length=50)
    from_address = models.CharField(max_length=50)
    subject = models.CharField(max_length=100)
    message_body = models.TextField()
    when_added = models.DateTimeField()
    priority = models.PositiveSmallIntegerField(choices=PRIORITIES)
    # @@@ campaign?
    
    # additional logging fields
    when_attempted = models.DateTimeField(default=datetime.now)
    result = models.PositiveSmallIntegerField(choices=RESULT_CODES)
    log_message = models.TextField()
