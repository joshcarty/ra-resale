from django.contrib import admin

from .models import Event, Ticket, Tracker


admin.site.register(Event)
admin.site.register(Ticket)
admin.site.register(Tracker)