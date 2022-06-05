import sys
import fnmatch
import re
import traceback
import json
import os
import string
from copy import deepcopy
from furl import furl
from subprocess import Popen, PIPE, STDOUT
from os.path import abspath
from shutil import ignore_patterns, copy2, copystat
from jinja2 import Template
from scrapyd_api import ScrapydAPI
from bs4 import BeautifulSoup

from shutil import move, copy, rmtree
from os.path import join, exists, dirname

sys.path.append('../..')

from . import get_logger

IGNORES = ['.git/', '*.pyc', '.DS_Store', '.idea/',
           '*.egg', '*.egg-info/', '*.egg-info', 'build/']

NO_REFERRER = '<meta name="referrer" content="never">'

BASE = '<base href="{href}">'

VOCAB = (
    'O', '[PAD]', 'B-DISEASE', 'I-DISEASE', 'B-SYMPTOM',
    'I-SYMPTOM', 'B-CAUSE', 'I-CAUSE', 'B-POSITION',
    'I-POSITION','B-TREATMENT', 'I-TREATMENT',
    'B-DRUG', 'I-DRUG', 'B-EXAMINATION', 'I-EXAMINATION')
label2index = {tag: idx for idx, tag in enumerate(VOCAB)}
index2label = {idx: tag for idx, tag in enumerate(VOCAB)}

def get_scrapyd(client):
    if not client.auth:
        return ScrapydAPI(scrapyd_url(client.ip, client.port))
    return ScrapydAPI(scrapyd_url(client.ip, client.port), auth=(client.username, client.password))

def scrapyd_url(ip, port):
    """
    get scrapyd url
    :param ip: host
    :param port: port
    :return: string
    """
    url = 'http://{ip}:{port}'.format(ip=ip, port=port)
    return url

def ignored(ignores, path, file):
    """
    judge if the file is ignored
    :param ignores: ignored list
    :param path: file path
    :param file: file name
    :return: bool
    """
    file_name = join(path, file)
    for ignore in ignores:
        if '/' in ignore and ignore.rstrip('/') in file_name:
            return True
        if fnmatch.fnmatch(file_name, ignore):
            return True
        if file == ignore:
            return True
    return False

def log_exception(exception=Exception, logger=None):
    """
    used for log exceptions
    """
    if not logger:
        logger = get_logger(__name__)

    def deco(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except exception as err:
                logger.exception(err, exc_info=True)
            else:
                return result
        return wrapper
    return deco

def bytes2str(data):
    """
    bytes2str
    :param data: origin data
    :return: str
    """
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    data = data.strip()
    return data

def get_tree(path, ignores=IGNORES):
    """
    get tree structure
    :param path: Folder path
    :param ignores: Ignore files
    :return: Json
    """
    result = []
    for file in os.listdir(path):
        if os.path.isdir(join(path, file)):
            if not ignored(ignores, path, file):
                children = get_tree(join(path, file), ignores)
                if children:
                    result.append({
                        'label': file,
                        'children': children,
                        'path': path
                    })
        else:
            if not ignored(ignores, path, file):
                result.append({'label': file, 'path': path})
    return result

def log_url(ip, port, project, spider, job):
    """
    get log url
    :param ip: host
    :param port: port
    :param project: project
    :param spider: spider
    :param job: job
    :return: string
    """
    url = 'http://{ip}:{port}/logs/{project}/{spider}/{job}.log'.format(ip=ip, port=port, project=project,
                                                                        spider=spider, job=job)
    return url

def get_job_id(client, task):
    """
    construct job id
    :param client: client object
    :param task: task object
    :return: job id
    """
    return '%s-%s-%s' % (client.name, task.project, task.spider)

def process_html(html, base_url):
    """
    process html, add some tricks such as no referrer
    :param html: source html
    :return: processed html
    """
    dom = BeautifulSoup(html, 'lxml')
    dom.find('head').insert(0, BeautifulSoup(NO_REFERRER, 'lxml'))
    dom.find('head').insert(0, BeautifulSoup(
        BASE.format(href=base_url), 'lxml'))
    html = str(dom)
    # html = unescape(html)
    return html

def clients_of_task(task):
    """
    get valid clients of task
    :param task: task object
    :return:
    """
    from .models import Client
    client_ids = json.loads(task.clients)
    for client_id in client_ids:
        client = Client.objects.get(id=client_id)
        if client:
            yield client

def is_in_curdir(filepath):
    """
    return if a filepath in cur directory
    """
    execute_path = os.getcwd()
    print('ecec', execute_path, filepath)
    result = os.path.realpath(filepath).startswith(
        os.path.realpath(execute_path))
    print('result', result)
    return result

def get_entities(text,result):
    entities = []
    curr_entity = ''
    curr_tag = ''
    for o,pred in zip(text,result):
        pp = index2label[pred]
        if pp.startswith('B'):
            curr_entity = o
            curr_tag = pp.split('-')[1]
        elif pp.startswith('I'):
            if curr_entity != '':
                curr_entity += ' '
                curr_entity += o
            else:
                print("ERROR: An I-label doesn't followed with a B-label")
        else:
            if curr_tag != '':
                entities.append((curr_entity,curr_tag))
            curr_entity = ''
            curr_tag = ''
    if curr_tag != '':
        entities.append((curr_entity,curr_tag))
    return entities

def get_relations(original,predicted):
    """
        Label conversion based on predicted values and document types.
        :param original: document types(DISEASE or SYMPTOM)
        :param predicted: predicted values
        :return: New tag names
    """
    if original == "DISEASE":
        if predicted == "DISEASE":
            return "DISEASE_RELATED_DISEASE"
        elif predicted == "SYMPTOM":
            return "DISEASE_HAS_SYMPTOM"
        elif predicted == "EXAMINATION":
            return "DISEASE_CORRESPONDING_EXAMINATION"
        elif predicted == "TREATMENT":
            return "DISEASE_CORRESPONDING_TREATMENT"
        elif predicted == "DRUG":
            return "DISEASE_CORRESPONDING_DRUG"
        elif predicted == "POSITION":
            return "DISEASE_CORRESPONDING_POSITION"
        elif predicted == "CAUSE":
            return "DISEASE_CORRESPONDING_CAUSE"
        else:
            return "UNKNOWN"
    elif original == "SYMPTOM":
        if predicted == "DISEASE":
            return "SYMPTOM_CORRESPONDING_DISEASE"
        elif predicted == "SYMPTOM":
            return "SYMPTOM_RELATED_SYMPTOM"
        elif predicted == "EXAMINATION":
            return "SYMPTOM_CORRESPONDING_EXAMINATION"
        elif predicted == "TREATMENT":
            return "SYMPTOM_CORRESPONDING_TREATMENT"
        elif predicted == "DRUG":
            return "SYMPTOM_CORRESPONDING_DRUG"
        elif predicted == "POSITION":
            return "SYMPTOM_CORRESPONDING_POSITION"
        elif predicted == "CAUSE":
            return "SYMPTOM_CORRESPONDING_CAUSE"
        else:
            return "UNKNOWN"
    else:
        return "UNKNOWN"

def remove_dup(title,result_list):
    new_res = []
    for item in result_list:
        entity,relation = item
        if entity.lower() == title.lower():
            continue
        else:
            if item not in new_res:
                new_res.append(item)

    return new_res

def replace_relations(prediction_list,title_type):
    new_res = []
    for item in prediction_list:
        entity,relation = item
        new_res.append((entity,get_relations(original = title_type, predicted = relation)))
    return new_res


def convert_into_dict(title, prediction_list, title_type="DISEASE"):
    json_dict = dict()
    json_dict['NAME'] = title
    json_dict['TITLE_TYPE'] = title_type
    for item in prediction_list:
        entity, tag = item
        try:
            json_dict[tag].append(entity)
        except:
            json_dict[tag] = [entity]

    return json_dict

def post_process(title,title_type,results):
    prediction_list = replace_relations(remove_dup(title,results),title_type)
    return convert_into_dict(title,prediction_list,title_type)