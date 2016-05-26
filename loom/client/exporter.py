#!/usr/bin/env python

import argparse
import json
import os
import sys
import yaml
from loom.client import settings_manager
from loom.client.common import get_settings_manager_from_parsed_args
from loom.client.common import add_settings_options_to_parser
from loom.client.exceptions import *
from loom.common.filehandler import FileHandler
from loom.common.objecthandler import ObjectHandler
from loom.common.helper import get_console_logger


class AbstractExporter(object):
    """Common functions for the various subcommands under 'export'
    """
    
    def __init__(self, args):
        """Common init tasks for all Export classes
        """
        self.args = args
        self.settings_manager = get_settings_manager_from_parsed_args(self.args)
        self.master_url = self.settings_manager.get_server_url_for_client()

    @classmethod
    def get_parser(cls, parser):
        parser = add_settings_options_to_parser(parser)
        return parser


class FileExporter(AbstractExporter):

    @classmethod
    def get_parser(cls, parser):
        parser = super(FileExporter, cls).get_parser(parser)
        parser.add_argument(
            'file_ids',
            nargs='+',
            metavar='FILE_ID',
            help='File or list of files to be exported')
        parser.add_argument(
            '--destination',
            metavar='DESTINATION',
            help='Destination filename or directory')
        return parser

    def run(self):
        filehandler = FileHandler(self.master_url, logger=get_console_logger())
        return filehandler.export_files(
            self.args.file_ids,
            destination_url=self.args.destination
        )

class WorkflowExporter(AbstractExporter):

    @classmethod
    def get_parser(cls, parser):
        parser = super(WorkflowExporter, cls).get_parser(parser)
        parser.add_argument(
            'workflow_id',
            metavar='WORKFLOW_ID', help='Workflow to be downloaded.')
        parser.add_argument(
            '--destination',
            metavar='DESTINATION',
            help='Destination filename or directory')
        parser.add_argument(
            '--format',
            choices=['json', 'yaml'],
            default='json',
            help='Data format for downloaded workflow')
        return parser

    def run(self):
        objecthandler = ObjectHandler(self.master_url)
        workflow = objecthandler.get_workflow_index(query_string=self.args.workflow_id, min=1, max=1)[0]
        destination = self._get_destination(workflow)
        self._save_workflow(workflow, destination)

    def _get_destination(self, workflow):
        default_name = '%s.%s' % (workflow['name'], self.args.format)
        if self.args.destination is None:
            destination = os.path.join(os.getcwd(), default_name)
            return FileHandler.rename_to_avoid_overwrite(destination)
        elif os.isdir(self.args.destination):
            destination = os.path.join(self.args.destination, default_name)
            return FileHandler.rename_to_avoid_overwrite(destination)
        else:
            # Don't modify a file destination specified by the user, even if it overwrites something.
            return self.args.destination

    def _save_workflow(self, workflow, destination):
        print 'Downloading workflow %s@%s to %s.' % (workflow.get('name'), workflow.get('_id'), destination)
        with open(destination, 'w') as f:
            if self.args.format == 'json':
                json.dump(workflow, f)
            elif self.args.format == 'yaml':
                yaml.safe_dump(workflow, f)
            else:
                raise Exception('Invalid format type %s' % self.args.format)


class Exporter:
    """Sets up and executes commands under "download" on the main parser.
    """

    def __init__(self, args=None):

        # Args may be given as an input argument for testing purposes.
        # Otherwise get them from the parser.
        if args is None:
            args = self._get_args()
        self.args = args

    def _get_args(self):
        parser = self.get_parser()
        return parser.parse_args()

    @classmethod
    def get_parser(cls, parser=None):

        # If called from main, use the subparser provided.
        # Otherwise create a top-level parser here.
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        subparsers = parser.add_subparsers(help='select a data type to download', metavar='{file,workflow}')

        file_subparser = subparsers.add_parser('file', help='download a file or an array of files')
        FileExporter.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=FileExporter)

        hidden_file_subparser = subparsers.add_parser('files')
        FileExporter.get_parser(hidden_file_subparser)
        hidden_file_subparser.set_defaults(SubSubcommandClass=FileExporter)

        workflow_subparser = subparsers.add_parser('workflow', help='download a workflow')
        WorkflowExporter.get_parser(workflow_subparser)
        workflow_subparser.set_defaults(SubSubcommandClass=WorkflowExporter)

        hidden_workflow_subparser = subparsers.add_parser('workflows')
        WorkflowExporter.get_parser(hidden_workflow_subparser)
        hidden_workflow_subparser.set_defaults(SubSubcommandClass=WorkflowExporter)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Exporter().run()
