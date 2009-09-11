from django.db import models
from django_mailer import constants, managers
import datetime


PRIORITIES = (
    (constants.PRIORITY_HIGH, 'high'),
    (constants.PRIORITY_NORMAL, 'normal'),
    (constants.PRIORITY_LOW, 'low'),
)

RESULT_CODES = (
    (constants.RESULT_SENT, 'success'),
    (constants.RESULT_SKIPPED, 'not sent (blacklisted)'),
    (constants.RESULT_FAILED, 'failure'),
)


class Message(models.Model):
    to_address = models.CharField(max_length=200)
    from_address = models.CharField(max_length=200)
    subject = models.CharField(max_length=255)

    encoded_message = models.TextField()
    date_created = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        ordering = ('date_created',)

    def __unicode__(self):
        return '%s: %s' % (self.to_address, self.subject)


class QueuedMessage(models.Model):
    message = models.OneToOneField(Message, editable=False)
    priority = models.PositiveSmallIntegerField(choices=PRIORITIES,
                                            default=constants.PRIORITY_NORMAL)
    deferred = models.DateTimeField(null=True, blank=True)
    retries = models.PositiveIntegerField(default=0)
    date_queued = models.DateTimeField(default=datetime.datetime.now)

    objects = managers.QueueManager()

    class Meta:
        ordering = ('priority', 'date_queued')

    def defer(self):
        self.deferred = datetime.datetime.now()
        self.save()


class Blacklist(models.Model):
    email = models.EmailField(max_length=200)
    date_added = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        ordering = ('-date_added',)
        verbose_name = 'blacklisted e-mail address'
        verbose_name_plural = 'blacklisted e-mail addresses'


class Log(models.Model):
    message = models.ForeignKey(Message)
    result = models.PositiveSmallIntegerField(choices=RESULT_CODES)
    date = models.DateTimeField(default=datetime.datetime.now)
    log_message = models.TextField()

    class Meta:
        ordering = ('-date',)
