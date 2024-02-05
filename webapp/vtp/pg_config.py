# Standard Library
import os


def get_default_config() -> dict:
    default_config = {
        "PG_PORT": 5432,
        "PG_HOST": "db-pg",
        "PG_USER": "calcun",
        "PG_PASSWORD": "test",
        "PG_DBNAME": "calcun_data",
    }
    merged_config = {}
    for k in default_config:
        merged_config[k] = os.environ.get(k, default_config[k])
    return merged_config
