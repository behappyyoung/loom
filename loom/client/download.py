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
from loom.common import filehandler, objecthandler
from loom.common.helper import get_console_logger


class AbstractDownloader(object):
    """Common functions for the various subcommands under 'download'
    """
    
    def __init__(self, args):
        """Common init tasks for all Download classes
        """
        self.args = args
        self.settings_manager = get_settings_manager_from_parsed_args(self.args)
        self.master_url = self.settings_manager.get_server_url_for_client()

    @classmethod
    def get_parser(cls, parser):
        parser = add_settings_options_to_parser(parser)
        return parser


class FileDownloader(AbstractDownloader):

    @classmethod
    def get_parser(cls, parser):
        parser = super(FileDownloader, cls).get_parser(parser)
        parser.add_argument(
            'file_ids',
            nargs='+',
            metavar='FILE_ID',
            help='File or list of files to be downloaded')
        parser.add_argument(
            '--directory',
            metavar='DIRECTORY',
            help='Destination directory for downloads')
        parser.add_argument(
            '--rename',
            nargs='+',
            metavar='NEW_FILE_NAME',
            help='Rename the downloaded file(s). The number of names '\
            'must be equal to the number of files downloaded.')
        return parser

    def run(self):
        self._get_filehandler()
        self._download_files()

    def _get_filehandler(self):
        self.filehandler = filehandler.FileHandler(self.master_url, logger=get_console_logger())

    def _download_files(self):
        self.filehandler.download_files(
            self.args.file_ids,
            local_names=self.args.rename,
            target_directory=self.args.directory
        )

class WorkflowDownloader(AbstractDownloader):

    @classmethod
    def get_parser(cls, parser):
        parser = super(WorkflowDownloader, cls).get_parser(parser)
        parser.add_argument(
            'workflow_id',
            metavar='WORKFLOW_ID', help='Workflow to be downloaded.')
        parser.add_argument(
            '--file_name',
            metavar='FILE_NAME',
            help='Destination file name and path for downloaded workflow')
        parser.add_argument(
            '--format',
            choices=['json', 'yaml'],
            default='json',
            help='Data format for downloaded workflow')
        return parser

    def run(self):
        self._get_objecthandler()
        self._get_workflow()
        self._get_file_name()
        self._save_workflow()

    def _get_objecthandler(self):
        self.objecthandler = objecthandler.ObjectHandler(self.master_url)

    def _get_workflow(self):
        self.workflow = self.objecthandler.get_workflow_index(query_string=self.args.workflow_id, min=1, max=1)[0]

    def _get_file_name(self):
        if self.args.file_name is not None:
            self.file_name = self.args.file_name
        else:
            self.file_name = self.workflow['workflow_name']

    def _save_workflow(self):
        with open(self.file_name, 'w') as f:
            if self.args.format == 'json':
                json.dump(self.workflow, f)
            elif self.args.format == 'yaml':
                yaml.safe_dump(self.workflow, f)
            else:
                raise Exception('Invalid format type %s' % self.args.format)
                

class Downloader:
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
        FileDownloader.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=FileDownloader)

        hidden_file_subparser = subparsers.add_parser('files')
        FileDownloader.get_parser(hidden_file_subparser)
        hidden_file_subparser.set_defaults(SubSubcommandClass=FileDownloader)

        workflow_subparser = subparsers.add_parser('workflow', help='download a workflow')
        WorkflowDownloader.get_parser(workflow_subparser)
        workflow_subparser.set_defaults(SubSubcommandClass=WorkflowDownloader)

        hidden_workflow_subparser = subparsers.add_parser('workflows')
        WorkflowDownloader.get_parser(hidden_workflow_subparser)
        hidden_workflow_subparser.set_defaults(SubSubcommandClass=WorkflowDownloader)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Downloader().run()
