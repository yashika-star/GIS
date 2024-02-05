from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
import uuid 

class Buildings(models.Model):
    BuildingName = models.CharField(max_length=50, null=True)
    GlobalId = models.CharField(max_length=50, null=True)
    AddressId = models.CharField(max_length=50, null=True)
    Owner = models.CharField(max_length=50, null=True)
    Tennant = models.CharField(max_length=50, null=True)
    lod0 = models.TextField(null=True)
    lod1_X3D = models.TextField(null=True)
    lod1_OBJ = models.TextField(null=True)
    lod1_GLTF = models.TextField(null=True)
    lod1_GLB = models.TextField(null=True)
    BoundingBox = models.TextField(null=True)
    Longitude = models.FloatField(null=True)
    Latitude = models.FloatField(null=True)
    Altitude = models.FloatField(null=True)
    geom = models.PolygonField(null=True)


class AssetLookup(models.Model):
    dataId = models.UUIDField(primary_key = True, 
         default = uuid.uuid4, 
         editable = False)
    buildingIds = ArrayField(ArrayField(
            models.BigIntegerField(blank=True),
            size=1000,
        ),
        size=1000,)

class EventsData(models.Model):
    dateTime = models.DateTimeField()
    eventDescription=models.TextField(max_length=500)
    EventChoices = (
        ('0', 'Normal'),
        ('1', 'Medium'),
        ('2', 'Critical'),
    )
    eventType=models.CharField(max_length=1, choices=EventChoices)
    buildingId = models.ForeignKey(Buildings,on_delete=models.CASCADE,null=False)
    def __str__(self):
        return self.get_eventType_display()


class NetworkData(models.Model):
    node_id = models.CharField(max_length=100)
    group=models.IntegerField()
    source= models.CharField(max_length=100)
    target=models.CharField(max_length=100)
    value=models.BigIntegerField()
    label=models.CharField(max_length=100)

