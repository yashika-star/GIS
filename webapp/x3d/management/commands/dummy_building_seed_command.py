from csv import DictReader
from django.core.management.base import BaseCommand

from x3d.models import Buildings


class Command(BaseCommand):
    help = "Seed data from CSV files in Buildings table."

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        try:
            with open(file_path, 'r') as csvfile:
                csv_reader = DictReader(csvfile, delimiter=',')
                buildings = []
                for row in csv_reader:
                    building = Buildings()
                    building.BuildingName = row['BuildingName']
                    building.GlobalId = row['GlobalID']
                    building.AddressId = row['AddressID']
                    building.Owner = row['Owner']
                    building.Tennant = row['Tennant']
                    building.BoundingBox = row['BoundingBox']
                    building.Longitude = float(row['Longitude'])
                    building.Latitude = float(row['Latitude'])
                    building.Altitude = float(row['Altitude'])
                    building.lod0 = row['lod0']
                    building.lod1_X3D = row['lod1_X3D']
                    building.lod1_OBJ = row['lod1_OBJ']
                    building.lod1_GLTF = row['lod1_GLTF']
                    building.lod1_GLB = row['lod1_GLB']
                    building.geom = row['geom']

                    buildings.append(building)
                Buildings.objects.bulk_create(buildings)
                self.stdout.write(self.style.SUCCESS(
                    'Buildings Data imported successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR('Error importing data:'))
            self.stdout.write(self.style.ERROR(e))
