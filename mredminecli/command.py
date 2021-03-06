import argparse
from . import RedmineCliException
from arguments import Arguments as A
from formatter import BaseFormatter, ListFormatter
from redmine.resultsets import ResourceSet


BASE_LIST_COMMAND_ARGS = [
    A('--limit', type=int, help='Limit', default=100),
    A('--offset', type=int, help='Offset'),
    A('--order', type=str, help='Order field. field or field:desc', default='id')
]


def int_or_string(value):
    return int(value) if value.isdigit() else value


class BaseCommand(object):
    formatter_class = BaseFormatter
    params_map = {}

    def __init__(self, resource):
        self.resource = resource
        self.redmine = resource.redminecli.redmine
        self.config = resource.redminecli.config

    def get_formatter(self, *args, **kwargs):
        return self.formatter_class(self, *args, **kwargs)

    def get_command_params(self):
        result = {}
        for args_param, command_param in self.params_map.iteritems():
            value = self.config.get_arg(args_param)
            if value is None:
                continue
            result[command_param] = value
        return result

    def get_command_args(self):
        return []

    def run(self):
        formatter = self.get_formatter(orderby=self.config.get_arg('order'))
        redmine_resource_name = getattr(self.resource, 'redmine_name', self.resource.name)
        redmine_resource = getattr(self.redmine, redmine_resource_name, None)
        if not redmine_resource:
            raise RedmineCliException('Redmine has no resource %s' % redmine_resource_name)
        command_name = getattr(self, 'redmine_name', self.name)
        func = getattr(redmine_resource, command_name, None)
        if not func or not callable(func):
            raise RedmineCliException('Redmine resource %s has no callable %s' % (redmine_resource_name, command_name))
        result = func(*self.get_command_args(), **self.get_command_params())
        if isinstance(result, ResourceSet):
            result = list(result.values(*formatter.values))
        formatter.prepare_result(result)
        formatter.print_result(result)


class ProjectListCommand(BaseCommand):
    formatter_class = ListFormatter
    name = 'list'
    redmine_name = 'all'
    description = 'Projects list'
    arguments = BASE_LIST_COMMAND_ARGS

    params_map = {
        'limit': 'limit',
        'offset': 'offset'
    }


def assigned_type(value):
    if value.isdigit():
        return int(value)
    if value == 'me':
        return value
    raise argparse.ArgumentTypeError('%s is not valid value for assigned' % value)


def status_type(value):
    if value.isdigit():
        return int(value)
    if value in ['open', 'closed', '*']:
        return value
    raise argparse.ArgumentTypeError('%s is not valid value for status' % value)


class IssueListCommand(BaseCommand):
    formatter_class = ListFormatter
    name = 'list'
    redmine_name = 'filter'
    description = 'Issue list'

    arguments = [
        A('--project', type=int_or_string, help='Project id or project identifier'),
        A('--query', type=int, help='Query id'),
        A('--status', type=status_type, help='Status: open, closed, * or status id'),
        A('--assigned', type=assigned_type, help='Assigned to: me or user id'),
        A('--tracker', type=assigned_type, help='Tracker id')
    ] + BASE_LIST_COMMAND_ARGS

    params_map = {
        'limit': 'limit',
        'offset': 'offset',
        'order': 'sort',
        'project': 'project_id',
        'tracker': 'tracker_id',
        'query': 'query_id'
    }


class IssueShowCommand(BaseCommand):
    name = 'show'
    redmine_name = 'get'
    description = 'Show issue details'

    arguments = [
        A('issue_id', type=int, help='Issue id')
    ]

    def get_command_args(self):
        return [self.config.get_arg('issue_id')]


class UserListCommand(BaseCommand):
    formatter_class = ListFormatter
    name = 'list'
    redmine_name = 'filter'
    description = 'User list'

    arguments = [
        A('--status', type=int, help='User status. 0 - anonymous, 1 - active (default), 2 - registered, 3 - locked'),
        A('--name', help='Filter users on their login, firstname, lastname and mail. If the pattern contains a space, it will also return users whose firstname match the first word or lastname match the second word.'),
        A('--group', type=int, help='Group id')
    ] + BASE_LIST_COMMAND_ARGS

    params_map = {
        'limit': 'limit',
        'offset': 'offset',
        'status': 'status',
        'name': 'name',
        'group': 'group_id'
    }
