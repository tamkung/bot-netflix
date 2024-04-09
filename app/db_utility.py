from app import SQL_DB

import sqlalchemy
from flask import jsonify,request


def createDBConnection():
    try:
        sql_db_connection = SQL_DB.engine.connect()
        if sql_db_connection.closed:
            return False
        return True
    except (Exception) as error:
        return False


def executeDB(func):
    def funcWrapper(*args, **kwargs):
        try:
            return_func = func(*args, **kwargs)
            SQL_DB.session.commit()
            SQL_DB.session.close()
        except (Exception) as error:
            print("error: " + str(error))
            SQL_DB.session.rollback()
            SQL_DB.session.close()
            return jsonify({"status": "fail", "message": str(error)}), 500
        return return_func
    funcWrapper._original = func
    return funcWrapper


def asDictManyTable(object_table):
    dict_buffer = {}
    for item in object_table:
        if hasattr(object_table[item], '__bind_key__'):
            dict_buffer = {**dict_buffer, **object_table[item].asDict()}
        else:
            dict_buffer = {**dict_buffer, **{item: object_table[item]}}
    return dict_buffer


def toList(data):
    if data:
        return [item.asDict() for item in data]
    else:
        return "data format is wrong"

