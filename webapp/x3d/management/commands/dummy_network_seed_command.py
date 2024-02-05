from csv import DictReader
from django.core.management.base import BaseCommand

from x3d.models import NetworkData


class Command(BaseCommand):
    help = "Seed data from CSV files in network table."

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        try:
            with open(file_path, 'r') as csvfile:
                csv_reader = DictReader(csvfile, delimiter=',')
                network_data_list = []
                for row in csv_reader:
                    network_data= NetworkData()
                    network_data.node_id =row["node_id"]
                    network_data.group=row["group"]
                    network_data.source=row["source"]
                    network_data.target=row["target"]
                    network_data.value=row["value"]
                    network_data.label=row["label"]
                  
                    network_data_list.append(network_data)
                NetworkData.objects.bulk_create(network_data_list)
                self.stdout.write(self.style.SUCCESS(
                    'Network Data imported successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR('Error importing data:'))
            self.stdout.write(self.style.ERROR(e))
