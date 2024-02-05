from django.contrib.gis.geos import GEOSGeometry
import json

from django.db import DatabaseError, connections


def create_kg_in_db(table_name, data):
    with connections['default'].cursor() as cursor:
        try:
            cursor.execute("BEGIN;")

            nodes_tablename = table_name + "_kg_nodes"
            links_tablename = table_name + "_kg_links"

            cursor.execute(f"CREATE TABLE {nodes_tablename} (id BIGSERIAL PRIMARY KEY, key int, name VARCHAR(255));")
            for node in data["nodes"]:
                cursor.execute(
                    f"INSERT INTO {nodes_tablename} (key, name) VALUES (%s, %s);", [node["id"], node["name"]])

            cursor.execute(f"CREATE TABLE {links_tablename} (id BIGSERIAL PRIMARY KEY, source int, target int, description TEXT);")
            for link in data["links"]:
                cursor.execute(
                    f"INSERT INTO {links_tablename} (source, target, description) VALUES (%s, %s, %s);", [link["source"], link["target"], link["desc"]])

            cursor.execute("COMMIT;")  # Complete the transaction
            return {
                "success": True,
                "message": f"Tables created for {table_name} successfully."
            }
        except DatabaseError as e:
            cursor.execute("ROLLBACK;")  # Rollback the transaction
            return {
                "success": False,
                "message": str(e)
            }