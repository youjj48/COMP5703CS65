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
    from gerapy.server.core.models import Client
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