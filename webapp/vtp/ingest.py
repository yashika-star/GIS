# Standard Library
import argparse
import json
import logging
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from pyproj import CRS
import rasterio
import age
import fiona
from shapely.geometry import MultiPoint, MultiLineString, MultiPolygon
import geopandas as gpd
from sqlalchemy import create_engine, inspect
import csv
import pandas as pd
import psycopg2

from pg_config import get_default_config


logging.getLogger().setLevel(logging.INFO)

SUPPORTED_VECTOR_SUFFIXES = ["shp", "json", "geojson", "kml", "zip", "csv"]
SUPPORTED_RASTER_SUFFIXES = ["tif", "tiff", "geotiff"]

def csv_to_kg_json(nodes_file, links_file):
    data = {
        "nodes": [],
        "links": []
    }

    with open(nodes_file, newline='', encoding='utf-8') as csvf:
        reader = csv.DictReader(csvf)
        for row in reader:
            data['nodes'].append(row)
    with open(links_file, newline='', encoding='utf-8') as csvf:
        reader = csv.DictReader(csvf)
        for row in reader:
            data['links'].append(row)

    return data

def get_epsg_from_compound_crs(crs_wkt):
    crs = CRS.from_wkt(crs_wkt)
    epsg = None
    height_epsg = None
    if crs.is_compound:
        epsg = crs.sub_crs_list[0].to_epsg()
        if crs.sub_crs_list[0].is_vertical:
            height_epsg = epsg
            epsg = crs.sub_crs_list[1].to_epsg()
        elif crs.sub_crs_list[1].is_vertical:
            height_epsg = crs.sub_crs_list[1].to_epsg()
    else:
        epsg = crs.to_epsg()

    return (epsg, height_epsg)

def force_multi_geometry(geometry):
    if geometry.geom_type == 'Point':
        return MultiPoint([geometry])
    elif geometry.geom_type == 'LineString':
        return MultiLineString([geometry])
    elif geometry.geom_type == 'Polygon':
        return MultiPolygon([geometry])
    else:
        return geometry

def properties_extractor(d: dict, key_filter: list = []) -> list:
    cypher_properties = []
    for key, value in d.items():
        if key not in key_filter:
            cypher_properties.append(f"{key}:'{value}'")
    return cypher_properties


def drop_table_from_db(table_name):
    config = get_default_config()
    conn_string = "dbname='"+config['PG_DBNAME']+"' user='"+config['PG_USER']+"' password='"+config['PG_PASSWORD']+"'host="+config['PG_HOST']
    postgresConnection = psycopg2.connect(conn_string)
    try:
    # Connect to the PostgreSQL database server
        cursor= postgresConnection.cursor()
        cursor.execute("DROP TABLE IF EXISTS "+table_name+";")
        postgresConnection.commit()

    except Exception as ex:
            
            print(type(ex), ex)
            # if exception occurs, you must rollback even though just retrieving.
            postgresConnection.rollback()
    finally:
        postgresConnection.close()
        


def add_data_to_table(table_name,options):
    config = get_default_config()
    conn_string = "dbname='"+config['PG_DBNAME']+"' user='"+config['PG_USER']+"' password='"+config['PG_PASSWORD']+"'host="+config['PG_HOST']
    postgresConnection = psycopg2.connect(conn_string)

    try:
        cursor= postgresConnection.cursor()
        with open(options.input_file, 'r') as f:
            next(f) # Skip the header row.
            cursor.copy_from(f, table_name, sep=',')
        postgresConnection.commit()
        
    except Exception as ex:
            print(type(ex), ex)
            # if exception occurs, you must rollback even though just retrieving.
            postgresConnection.rollback()
        
    finally:
        logging.info("Data import successfully")
        postgresConnection.close()



def create_table_in_db(table_name,columns,config,options,srs,geom_type,data_df):
    conn_string = "dbname='"+config['PG_DBNAME']+"' user='"+config['PG_USER']+"' password='"+config['PG_PASSWORD']+"'host="+config['PG_HOST']
    postgresConnection = psycopg2.connect(conn_string)
    try:
        # Connect to the PostgreSQL database server
        cursor= postgresConnection.cursor()
        if options.overwrite:
            columns_str = " "
            for k in columns:
                if columns[k] == "geometry":
                    columns_str+=k +" "+columns[k]+"("+geom_type+","+srs+"),"
                else:
                    columns_str+=k +" "+columns[k]+","
            sqlCreateTable = "create table "+table_name+"("+columns_str[:-1]+")"
            drop_table_from_db(table_name)
            cursor.execute(sqlCreateTable)
            postgresConnection.commit()
            add_data_to_table(table_name,options)

        else:
            columns_str = " "
            for k in columns:
                if columns[k] == "geometry":
                    columns_str+=k +" "+columns[k]+"("+geom_type+","+srs+"),"
                else:
                    columns_str+=k +" "+columns[k]+","
            sqlCreateTable = "create table IF NOT EXISTS  "+table_name+"("+columns_str[:-1]+")"
            cursor.execute(sqlCreateTable)
            postgresConnection.commit()
            add_data_to_table(table_name,options)     
    except Exception as ex:
            print(type(ex), ex)
            # if exception occurs, you must rollback even though just retrieving.
            postgresConnection.rollback()
    finally:
        postgresConnection.close()

 
def parse_CSV_file(csv_file_path:str,table_name,config,options):
    df_csv = pd.read_csv(csv_file_path)
    field_types={1:'text',2:'bigint',3:'numeric',4:'boolean',5:'geometry',6:'timestamp',7:'interval'}
    df_postgres={'object':'text','int64':'bigint','float64':'numeric','bool':'boolean','datetime64':'timestamp','timedelta':'interval'}
    print("Automatically assigned field types:")
    for col in df_csv.columns:
        if str(df_csv.dtypes[col]) in df_postgres:
            print("Field Name: "+col + ",  "+'Field Type: '+df_postgres[str(df_csv.dtypes[col])] )
           
        else:
            logging.error('Fieldtype '+str(df_csv.dtypes[col])+' is not configured')
            exit(1)

    
    user_input = input("Enter \'y\' to define own data types \n")
    assigned_data_types = {}
    if(user_input.lower() == "y"): 
        print("\n\nDefine data types for each field.")
        print("Enter data type from below list eg. 1 for Text data type. \n ")
        print(field_types)
        try:
            for col in df_csv.columns:
                dtype_input = int(input("Enter data type for column '"+col+"':"))
                if(field_types[dtype_input]):
                    assigned_data_types[col]=field_types[dtype_input]
                    
                    
        except Exception as ex:
            print(ex)
    else:
        for col in df_csv.columns:
            if str(df_csv.dtypes[col]) in df_postgres:
                assigned_data_types[col]=df_postgres[str(df_csv.dtypes[col])]
                print("Field Name: "+col + ",  "+'Field Type: '+df_postgres[str(df_csv.dtypes[col])])
    


    srs = input("Please enter epsg code for geometry,  default 4326 : ")
    if not srs or srs=='':
        srs="4326" 

    geometry_input =  input ("Please select geometry type: \n 1. Point \n 2. LineString \n 3. Polygon \n")
    geometry_type = ''
    if int(geometry_input) == 1:
        geometry_type  = "multipointz"
    elif int(geometry_input) ==  2:
        geometry_type  = "multilinestringz"
    elif int(geometry_input) ==3:
        geometry_type  = "multipolygonz"
        
    else:
        logging.error("Incorrect input for geometry type\n")
        exit(1)
    
    create_table_in_db(table_name,assigned_data_types,config,options,srs,geometry_type,df_csv)


    

    

def ingest_data(options: argparse.Namespace) -> None:
    logging.info(f"Ingesting input file: {options.input_file}")
    config = get_default_config()
    logging.info(config)

    logging.info(options)

    # Handle zipfile
    if options.input_file and Path(options.input_file).suffix.lower() == ".zip":
        with zipfile.ZipFile(options.input_file) as z:
            files = z.namelist()
            for suffix in SUPPORTED_VECTOR_SUFFIXES + SUPPORTED_RASTER_SUFFIXES:
                if suffix == "zip":
                    continue
                for file_path in [f for f in files if f.endswith(suffix)]:
                    sub_layer_name = re.sub(
                        r"[^a-zA-Z0-9_ \n\.]", "", Path(file_path).stem.lower()
                    )
                    o = argparse.Namespace(input_file=f"/vsizip/{options.input_file.resolve()}/{file_path}",
                                           new_layer_name=f"{options.new_layer_name}{sub_layer_name}",
                                           knowledge_graph_name=options.knowledge_graph_name,
                                           overwrite=options.overwrite)
                    ingest_data(o)
        return

    ext_name = Path(options.input_file).suffix[1:] if options.input_file else "csv"

    if ext_name in SUPPORTED_VECTOR_SUFFIXES:
        postgis_connection = f"""host={config['PG_HOST']} port={config['PG_PORT']} user={config['PG_USER']} dbname={config['PG_DBNAME']} password={config['PG_PASSWORD']}"""

        if options.knowledge_graph_name and ext_name in ['json', 'csv']:
            GRAPH_NAME = options.knowledge_graph_name
            connection = age.connect(postgis_connection)
            try:
                connection.setGraph(GRAPH_NAME)
                if options.overwrite:
                    age.deleteGraph(connection.connection, GRAPH_NAME)
                    connection.setGraph(GRAPH_NAME)

                kg_json = {}
                if ext_name == 'csv':
                    kg_json = csv_to_kg_json(options.nodes_file, options.links_file)
                else:
                    kg_json = open(options.input_file)
                    kg_json = json.load(kg_json)

                print(kg_json)
                nodes = kg_json['nodes']
                vertices_cypher = []
                return_dict = {}
                for node in nodes:
                    vertex_alias = f"v{node['id']}"
                    return_dict[vertex_alias] = f"{vertex_alias}:v{node['name']}"
                    cypher_merge = f"MERGE ({return_dict[vertex_alias]}"
                    cypher_properties = properties_extractor(node, ["id", "name"])
                    if cypher_properties:
                        cypher_merge += " {" + ', '.join(cypher_properties) + "}"

                    vertices_cypher.append(cypher_merge + ")")

                vertex_cypher = '\n'.join(vertices_cypher) + "\nRETURN [" + ','.join(list(return_dict.keys())) + "]"

                # Inserting vertices
                cursor = connection.execCypher(vertex_cypher)
                for row in cursor:
                    vertices = row[0]
                    for vertex in vertices:
                        print(vertex.id, vertex.label, vertex["desc"])
                        print("-->", vertex)

                match_cypher = "MATCH " + ', '.join(["(" + v + ")" for v in return_dict.values()])
                links = kg_json['links']
                links_cypher = []
                return_list = []
                REL_TYPE = "BELONGS_TO"
                for link in links:
                    link_alias = f"e{link['source']}{link['target']}"
                    return_list.append(link_alias)
                    cypher_merge = f"MERGE (v{link['source']})-[{link_alias}:{REL_TYPE}"
                    cypher_properties = properties_extractor(link, ["source", "target"])
                    if cypher_properties:
                        cypher_merge += " {" + ', '.join(cypher_properties) + "}"

                    links_cypher.append(cypher_merge + f"]->(v{link['target']})")

                link_cypher = match_cypher + '\n' + '\n'.join(links_cypher) + "\nRETURN [" + ','.join(return_list) + "]"

                # Inserting edges
                cursor = connection.execCypher(link_cypher)
                for row in cursor:
                    edges = row[0]
                    for edge in edges:
                        print(edge.id, edge.label, edge["desc"])
                        print("-->", edge)

                connection.commit()
            except Exception as ex:
                print(type(ex), ex)
                # if exception occurs, you must rollback even though just retrieving.
                connection.rollback()
            finally:
                connection.close()
        elif ext_name == "csv" and options.data_type and options.data_type.lower() == "spatial_csv":
            try:
                parse_CSV_file(options.input_file,options.new_layer_name,config,options)
               

                # connection.commit()
            except Exception as ex:
                print(type(ex), ex)
                # if exception occurs, you must rollback even though just retrieving.
                # connection.rollback()
            finally:
                # connection.close()
            
                pass                        
        elif ext_name == 'shp':
            c = fiona.open(options.input_file)
            if c.schema["geometry"] == 'Unknown':
                epsg, height_epsg = get_epsg_from_compound_crs(c.crs_wkt)
                features = [feature for feature in c]
                gdf = gpd.GeoDataFrame(features, crs=epsg).explode()
                gdf = gdf.rename(columns={
                    'geometry': 'geom'
                }).set_geometry('geom')
                print("Geom Types in Unknown (GeometryCollection): ", gdf.geom_type.unique())
                engine = create_engine(f"postgresql://{config['PG_USER']}:{config['PG_PASSWORD']}@{config['PG_HOST']}:{config['PG_PORT']}/{config['PG_DBNAME']}")
                for geom_type in gdf.geom_type.unique():
                    cgdf = gdf[gdf.geom_type == geom_type]
                    table_name = f"{options.new_layer_name}_{geom_type}"
                    cgdf['geom'] = cgdf.apply(lambda row: force_multi_geometry(row['geom']), axis=1)
                    if_exists = 'append'
                    if inspect(engine).has_table(table_name) and not options.overwrite:
                        print(f"Table {table_name} already exists. Skipping overwrite and will append records.")
                    else:
                        if_exists = 'replace'

                    cgdf.to_postgis(name=table_name, con=engine, if_exists=if_exists, index=False)
                return

            command_args = [
                "ogr2ogr",
                "-f",
                "PostgreSQL",
                f"PG:{postgis_connection}",
                str(options.input_file),
                "-nln",
                options.new_layer_name,
                "-nlt",
                "PROMOTE_TO_MULTI",
                "-dim",
                "3",
                "-lco",
                "GEOMETRY_NAME=geom",
                "-lco",
                "precision=NO",
                "-progress",
            ]
            if options.overwrite:
                command_args.append("-overwrite")
            logging.info(f"Running command: {' '.join(command_args)}")

            out = subprocess.check_output(command_args)
            logging.info(out.decode())
    elif ext_name in SUPPORTED_RASTER_SUFFIXES:
        # Define the first command
        raster2pgsql_cmd = [
            "raster2pgsql",
            "-C",
            "-I",
            "-F",
            "-t", "128x128",
            str(options.input_file),
            f"public.{options.new_layer_name}"
        ]

        src = rasterio.open(str(options.input_file))
        crs = CRS.from_wkt(src.crs.wkt)
        epsg, height_epsg = get_epsg_from_compound_crs(src.crs.wkt)

        if epsg is not None:
            raster2pgsql_cmd.append("-s")
            raster2pgsql_cmd.append(str(epsg))

        if options.overwrite:
            raster2pgsql_cmd.append("-d")
        logging.info(f"Running command: {' '.join(raster2pgsql_cmd)}")

        # Execute the first command
        process_raster = subprocess.Popen(raster2pgsql_cmd, stdout=subprocess.PIPE)

        # Define the second command
        psql_cmd = [
            "psql",
            "-h", str(config['PG_HOST']),
            "-p", str(config['PG_PORT']),
            "-U", str(config['PG_USER']),
            "-d", str(config['PG_DBNAME'])
        ]

        # Set the PGPASSWORD environment variable
        os.environ['PGPASSWORD'] = config['PG_PASSWORD']
        logging.info(f"Running command: {' '.join(psql_cmd)}")

        # Execute the second command, using the output of the first command as input
        out = subprocess.check_output(psql_cmd, stdin=process_raster.stdout)
        process_raster.stdout.close()

        logging.info(out.decode())
        del os.environ['PGPASSWORD']
    else:
        m = f"""
        File extension '{Path(options.input_file).suffix}' for file {options.input_file} is not supported.
        This program only supports these file extensions: {SUPPORTED_VECTOR_SUFFIXES}, {SUPPORTED_RASTER_SUFFIXES}
        """
        raise ValueError(m)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="Data ingestion",
        description="Different GIS vector and raster data ingestion script for postgresql.",
        epilog="Text at the bottom of help",
    )

    parser.add_argument("--input-file", "-i", type=Path)
    parser.add_argument("--nodes-file", "-nf", type=Path, help="Path to nodes csv file.")
    parser.add_argument("--links-file", "-lf", type=Path, help="Path to links csv file.")
    parser.add_argument("--new-layer-name", "-nln", type=str, required=True)
    parser.add_argument("--knowledge-graph-name", "-kgn", type=str, default="")
    parser.add_argument("--data-type", "-dt", type=str, default="",  help="Path to csv file with spatial data.")
    parser.add_argument("-overwrite", action="store_true")

    options = parser.parse_args()
    if not options.knowledge_graph_name and not options.input_file:
        print("Input file parameter is missing.")
        sys.exit(1)

    ingest_data(options)


if __name__=="__main__":
    main()