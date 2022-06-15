from django.urls import path, re_path
from rest_framework.authtoken import views as auth
from django.views.static import serve
from django.conf import settings
from . import views

app_name = 'polls'
urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^api/user/auth', auth.obtain_auth_token),
    re_path(r'^api/index/status', views.index_status, name='index_status'),
    re_path(r'^api/client$', views.client_index, name='client_index'),
    re_path(r'^api/client/create', views.client_create, name='client_create'),
    re_path(r'^api/client/(\d+)$', views.client_info, name='client_info'),
    re_path(r'^api/client/(\d+)/status', views.client_status, name='client_status'),
    re_path(r'^api/client/(\d+)/update', views.client_update, name='client_update'),
    re_path(r'^api/client/(\d+)/remove', views.client_remove, name='client_remove'),
    re_path(r'^api/client/(\d+)/projects', views.project_list, name='project_list'),
    re_path(r'^api/client/(\d+)/project/(\S+)/spiders', views.spider_list, name='spider_list'),
    re_path(r'^api/client/(\d+)/project/(\S+)/spider/(\S+)/job/(\S+)/log', views.job_log, name='job_log'),
    re_path(r'^api/client/(\d+)/project/(\S+)/spider/(\S+)$', views.spider_start, name='spider_start'),
    re_path(r'^api/client/(\d+)/project/(\S+)/jobs', views.job_list, name='job_list'),
    re_path(r'^api/client/(\d+)/project/(\S+)/version', views.project_version, name='project_version'),
    re_path(r'^api/client/(\d+)/project/(\S+)/deploy', views.project_deploy, name='project_deploy'),
    re_path(r'^api/client/(\d+)/project/(\S+)/job/(\S+)/cancel', views.job_cancel, name='job_cancel'),
    re_path(r'^api/project/index', views.project_index, name='project_index'),
    re_path(r'^api/project/create', views.project_create, name='project_create'),
    re_path(r'^api/project/upload', views.project_upload, name='project_upload'),
    re_path(r'^api/project/clone', views.project_clone, name='project_clone'),
    re_path(r'^api/project/(\S+)/configure', views.project_configure, name='project_configure'),
    re_path(r'^api/project/(\S+)/build', views.project_build, name='project_build'),
    re_path(r'^api/project/(\S+)/tree', views.project_tree, name='project_tree'),
    re_path(r'^api/project/(\S+)/remove', views.project_remove, name='project_remove'),
    re_path(r'^api/project/(\S+)/parse', views.project_parse, name='project_parse'),
    re_path(r'^api/project/file/rename', views.project_file_rename, name='project_file_rename'),
    re_path(r'^api/project/file/delete', views.project_file_delete, name='project_file_delete'),
    re_path(r'^api/project/file/create', views.project_file_create, name='project_file_create'),
    re_path(r'^api/project/file/update', views.project_file_update, name='project_file_update'),
    re_path(r'^api/project/file/read', views.project_file_read, name='project_file_read'),
    re_path(r'^api/task$', views.task_index, name='task_index'),
    re_path(r'^api/task/create', views.task_create, name='task_create'),
    re_path(r'^api/task/(\d+)/update', views.task_update, name='task_update'),
    re_path(r'^api/task/(\d+)/info', views.task_info, name='task_info'),
    re_path(r'^api/task/(\d+)/remove', views.task_remove, name='task_remove'),
    re_path(r'^api/task/(\d+)/status', views.task_status, name='task_status'),
    re_path(r'^api/logs_tree', views.logs_tree, name='logs_tree'),
    re_path(r'^api/result_tree', views.results_tree, name='result_tree'),
    re_path(r'^api/result_read', views.results_file_read, name='results_file_read'),
    re_path(r'^api/nlp_tree', views.nlp_tree, name='nlp_tree'),
    re_path(r'^api/nlp/run', views.nlp_run, name='nlp_run'),
    re_path(r'^api/neo4j/create', views.neo4j_create, name='neo4j_create'),
    re_path(r'^api/neo4j/modify', views.neo4j_modify, name='neo4j_modify'),
    re_path(r'^api/neo4j/delete', views.neo4j_delete, name='neo4j_delete'),
    re_path(r'^api/neo4j/available_node', views.neo4j_available_node, name='neo4j_available_node'),
    re_path(r'^api/neo4j/find', views.neo4j_find, name='neo4j_find'),
    re_path(r'^api/neo4j/single_find', views.neo4j_single_find, name='neo4j_single_find'),
    re_path(r'^api/neo4j/get_labels', views.neo4j_get_labels, name='neo4j_get_labels'),
    re_path(r'^api/neo4j/chart_data', views.neo4j_chart_data, name='neo4j_chart_data'),
    re_path('neo4j_graph.html', views.neo4j_graph, name='neo4j_graph'),
    re_path(r'^api/render', views.render_html, name='render_html'),
]

urlpatterns += [
    re_path(r'^static/(?P<path>.*)$',
            serve,
            {'document_root': settings.STATIC_ROOT})
]
