import json
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
import os
from django.conf import settings
from urllib.parse import urlparse, urlunparse
from django.contrib.gis.geos import GEOSGeometry
from x3d.models import AssetLookup, Buildings,EventsData,NetworkData
import uuid 
from django.db import connection
import datetime

X3D_PREFIX_SUFFIX = 'x3d'


def replace_hostname(original_url, new_hostname):
    # Parse the original URL
    parsed_url = urlparse(original_url)

    # Replace the hostname with the new one
    modified_url = parsed_url._replace(netloc=new_hostname)

    # Reconstruct the modified URL
    final_url = urlunparse(modified_url)

    return final_url


@api_view(['POST'])
@permission_classes((AllowAny, ))
# @renderer_classes([JSONRenderer])
def index(request):
    # if request.method == "POST":
    aoi = request.data.get('aoi', None)

    if not aoi:
        return Response({
            'status_code': status.HTTP_400_BAD_REQUEST,
            'message': '"aoi" param not found.'
        }, status=status.HTTP_400_BAD_REQUEST)
    try:
        aoi = json.loads(aoi.replace("\'", "\""))
        aoi = json.dumps(aoi, separators=(',', ':'))
        aoi_geom = GEOSGeometry(aoi, 4326)
    except Exception as e:
        print(e)
        return Response({
            'status_code': status.HTTP_400_BAD_REQUEST,
            'message': 'Invalid geojson.'
        }, status=status.HTTP_400_BAD_REQUEST)

    included_field_names = ["BuildingName", "lod1_X3D", "geom","id"]
    buildings = Buildings.objects.filter(
        geom__intersects=aoi_geom).only(*included_field_names).distinct("id","BuildingName", "lod1_X3D", "geom").order_by('id')

    assets = []
    buildingIds=[]
    for building in buildings:
        file_url = request.build_absolute_uri(os.path.join(f'/api/{X3D_PREFIX_SUFFIX}/', settings.MEDIA_URL.replace("/", ""), X3D_PREFIX_SUFFIX, getattr(building, included_field_names[1])))
        if settings.DEBUG:
            file_url = replace_hostname(file_url, "localhost:8080")

        geom = getattr(building, included_field_names[2])
        if geom and geom.geojson:
            geom = json.loads(geom.geojson)
        result = {
            included_field_names[0]: getattr(building, included_field_names[0]),
            included_field_names[1]: file_url,
            "file_bbox": geom
        }
        buildingIds.append(getattr(building, included_field_names[3]))
        assets.append(result)




    # x3d_folder_path = os.path.join(settings.MEDIA_ROOT, X3D_PREFIX_SUFFIX)
    # files = [f for f in os.listdir(x3d_folder_path) if os.path.isfile(
    #     os.path.join(x3d_folder_path, f))]

    # file_urls = [request.build_absolute_uri(os.path.join(
    #     f'/api/{X3D_PREFIX_SUFFIX}/', settings.MEDIA_URL.replace("/", ""), X3D_PREFIX_SUFFIX, f)) for f in files]

    # print(request.META.get('HTTP_X_FORWARDED_PROTO'))
    # print(request.META.get('HTTP_X_FORWARDED_HOST'))

    # Only for development! Don't use this in production.
    # if settings.DEBUG:
    #     file_urls = [replace_hostname(url, "localhost:8080")
    #                  for url in file_urls]

    
    data_id = str(uuid.uuid4())
    scene_assets =  AssetLookup()
    scene_assets.dataId = data_id
    scene_assets.buildingIds=buildingIds
    scene_assets.save()

    
    
    return Response({
        'status_code': status.HTTP_200_OK,
        'data': {'assets':assets,'dataId':data_id},
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((AllowAny, ))
def assetDetails(request):
    # data_type = request.data.get('type', None)
    scene_id = request.data.get('sceneId', None)

    if scene_id:
        try:
            data_detail_view = []
            time_series_data = []
            network_data = {
                "nodes":[],
                "links":[]
            }
            info_view = []

            scene_assets = AssetLookup.objects.filter(dataId=scene_id).values()

            for data in scene_assets: 
                for building_id in data["buildingIds"]:
                    building_info=Buildings.objects.filter(id=building_id).values('BuildingName','Altitude')
                    
                    events_info = EventsData.objects.filter(buildingId_id=building_id).values().distinct("dateTime")
                    for bInfo in building_info:
                        data_detail_view.append({"name":bInfo['BuildingName'],"height":bInfo['Altitude']})
                        info_view.append({"name":bInfo['BuildingName'],"height":bInfo['Altitude']})
                    for eInfo in events_info:
                        evTyp = ''
                        if eInfo["eventType"] == '0':
                            evTyp = 'Normal'
                        elif eInfo["eventType"] == '1':
                            evTyp='Medium'
                        else:
                            evTyp='Critical'

                        
                        time_series_data.append({"date_time":eInfo["dateTime"].date(),"event_description":eInfo["eventDescription"],
                                                 "event_type":evTyp})
            

            if len(data_detail_view)  > 0:
                network_data_queryset = NetworkData.objects.values()
                for data in network_data_queryset:
                    network_data['nodes'].append({"id":data['node_id'],'group':data["group"]})
                    network_data['links'].append({"source":data['source'],'target':data["target"],"value":data["value"],"label":data["label"]})

                # cursor=connection.cursor()
                # sql_edges = "SELECT start_id, end_id, properties FROM \"TestCarto\"._ag_label_edge"
                # cursor.execute(sql_edges)
                # for row in cursor.fetchall():
                #     network_data['links'].append({'source':row[0],'target':row[1],'properties':json.loads(row[2])})
                # sql_nodes = "SELECT id, properties FROM \"TestCarto\"._ag_label_vertex"
                # cursor.execute(sql_nodes)
                # for row in cursor.fetchall():
                #     network_data['nodes'].append({'id':row[0],'properties':json.loads(row[1])})

                        


        except Exception as e:
            return Response({
                'status_code': status.HTTP_404_NOT_FOUND,
                'message': 'scene id not found in db.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
        'status_code': status.HTTP_200_OK,
        'data': {"data_detail_view":data_detail_view, "time_series_data":time_series_data,"info_view":info_view,"network_data":network_data},},status=status.HTTP_200_OK)
    else:
        return Response({
            'status_code': status.HTTP_400_BAD_REQUEST,
            'message': 'param not found.'
        }, status=status.HTTP_400_BAD_REQUEST)
    

   
