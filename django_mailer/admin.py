from django.contrib import admin
from django_mailer import models


class Message(admin.ModelAdmin):
    list_display = ('to_address', 'subject', 'date_created')


class QueuedMessage(admin.ModelAdmin):
    list_display = ('id', 'message__to_address', 'message__subject',
                    'message__date_created', 'priority')


class Blacklist(admin.ModelAdmin):
    list_display = ('email', 'date_added')


class Log(admin.ModelAdmin):
    list_display = ('id', 'message__to_address', 'message__subject', 'date',
                    'result')


admin.site.register(models.Message, Message)
admin.site.register(models.QueuedMessage, QueuedMessage)
admin.site.register(models.Blacklist, Blacklist)
admin.site.register(models.Log, Log)
