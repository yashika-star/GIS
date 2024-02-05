from django.contrib import admin

from x3d.models import Buildings,EventsData

# Register your models here.

class EventsDataAdmin(admin.ModelAdmin):
    list_display = ['dateTime']
    fields = ('dateTime','eventDescription','eventType','buildingId')



admin.site.register(Buildings)
admin.site.register(EventsData,EventsDataAdmin)