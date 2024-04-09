import datetime
import time as time_lib
import email.utils
import os
import pytz
import string
from uuid import UUID
from flask import request
import base64
import hashlib
import random
from datetime import timedelta, datetime, time

from app import ENV_CONFIG
from dateutil.parser import parse


BASEDIR = os.path.abspath(os.path.dirname(__file__))


def convert_timestamp_in_datetime_utc(timestamp_received):
    dt_naive_utc = datetime.utcfromtimestamp(timestamp_received)
    return dt_naive_utc.replace(tzinfo=pytz.utc)

def toList(data):
    if data:
        return [item.asDict() for item in data]
    else:
        return "data format is wrong"


def toListForMultiTable(data):
    if data:
        return [item._asdict() for item in data]
    else:
        return "data format is wrong"


def converterDate(output):
    if isinstance(output, datetime.date):
        return output.__str__()


def convertUUIDToString(value):
    if isinstance(value, UUID):
        return str(value)


def randomString(size):
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(size))


def decode(data):
    cut_str = str(data)[5:][:-4][::-1]
    slicer = "==="
    if len(cut_str) % 4 != 0:
        cut_str += slicer[0:(4 - (len(cut_str) % 4))]
    return base64.b64decode(cut_str).decode("utf-8")


def encode(data):
    return randomString(5) + str(base64.b64encode(data.encode('utf-8'))[::-1])[:-1][2:] + randomString(4)


def hashPassword(password):
    key = ENV_CONFIG.HASH_KEY
    raw_password = password + key
    secret_password = hashlib.sha512(raw_password.encode())
    return secret_password.hexdigest()


def convertStrToDate(time):
    try:
        if isinstance(int(time), int):
            return int(time)
    except:
        pass
    try:
        if isinstance(float(time), float):
            return float(time)
    except:
        pass
    try:
        result = datetime.strptime(str(time), '%Y-%m-%d %H:%M:%S.%f')
    except:
        try:
            result = datetime.strptime(str(time), '%Y-%m-%d %H:%M:%S')
        except:
            try:
                result = datetime.strptime(str(time), '%Y-%m-%dT%H:%M:%SZ')
            except:
                try:
                    result = datetime.strptime(str(time), '%Y-%m-%dT%H:%M:%S')
                except:
                    try:
                        result = datetime.strptime(str(time), '%Y-%m-%dT%H:%M:%S.%f')
                    except:
                        try:
                            result = parse(str(time))
                        except:
                            result =email.utils.parsedate(str(time))
                            result = convert_timestamp_in_datetime_utc(time_lib.mktime(result))
                            result = result - timedelta(hours=7)

    return result

def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time