from csv import DictReader
from django.core.management.base import BaseCommand

from x3d.models import EventsData,Buildings


class Command(BaseCommand):
    help = "Seed data from CSV files in events table."

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        try:
            with open(file_path, 'r') as csvfile:
                csv_reader = DictReader(csvfile, delimiter=',')
                eventsData = []
                for row in csv_reader:
                    event= EventsData()
                    event.dateTime=row["dateTime"]
                    event.buildingId=Buildings.objects.get(id = int(row["buildingId_id"]))
                    event.eventDescription=row["eventDescription"]
                    event.eventType=row["eventType"]
                    eventsData.append(event)
                EventsData.objects.bulk_create(eventsData)
                self.stdout.write(self.style.SUCCESS(
                    'Events Data imported successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR('Error importing data:'))
            self.stdout.write(self.style.ERROR(e))
