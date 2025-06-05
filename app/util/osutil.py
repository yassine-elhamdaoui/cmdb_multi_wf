import json

from app.data import data_directory
import os
import yaml


def get_config(filename :str):
    file_path = get_file_path(data_directory, filename)
    with open(file_path) as file:
        data = json.load(file)
    return data

def get_wf_json(filename :str):
    json_file_path = get_file_path(os.path.join(data_directory, 'wf'), filename)
    with open(json_file_path) as file:
        data = json.load(file)
    return data


def getsql_operations(sql_file_name):
    sql_file_path = get_file_path(os.path.join(data_directory, 'sql'), sql_file_name)
    with open(sql_file_path, "r") as file:
        sql_queries = yaml.safe_load(file)
    return sql_queries


def get_current_directory():
    return os.path.dirname(os.path.abspath(__file__))


def get_parent_directory(current_directory):
    return os.path.abspath(os.path.join(current_directory, '..'))


def get_file_path(file_directory, file_name):
    sql_file_path = os.path.join(file_directory, file_name)
    return sql_file_path


def does_file_exist(file_path):
    if os.path.isfile(file_path):
        return True
    else:
        return False

def get_all_env(): 
    env_vars = os.environ
    for key, value in env_vars.items():
        print(f"{key}: {value}")

