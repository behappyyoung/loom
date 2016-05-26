#!/usr/bin/env python

import argparse
import os

from loom.client.common import get_settings_manager_from_parsed_args
from loom.client.common import add_settings_options_to_parser
from loom.client.common import read_as_json_or_yaml
from loom.client.importer import WorkflowImporter
from loom.client.exceptions import *
from loom.common.helper import get_console_logger
from loom.common.filehandler import FileHandler
from loom.common.objecthandler import ObjectHandler


class WorkflowRunner(object):
    """Run a workflow, either from a local file or from the server.
    """

    def __init__(self, args=None, logger=None):
        if args is None:
            args = self._get_args()
        self.args = args
        self.settings_manager = get_settings_manager_from_parsed_args(self.args)
        self.master_url = self.settings_manager.get_server_url_for_client()
        if logger is None:
            logger = get_console_logger(name=__file__)
        self.logger = logger
        self.objecthandler = ObjectHandler(self.master_url)
        self.filehandler = FileHandler(self.master_url, logger=self.logger)

    @classmethod
    def _get_args(cls):
        parser = cls.get_parser()
        args = parser.parse_args()
        self._validate_args(args)
        return args

    @classmethod
    def get_parser(cls, parser=None):
        if parser is None:
            parser = argparse.ArgumentParser(__file__)
        parser.add_argument('workflow', metavar='WORKFLOW', help='Workflow ID or file path')
        parser.add_argument('inputs', metavar='INPUT_NAME=DATA_ID', nargs='*', help='Data object ID or file path for inputs')
        parser.add_argument(
            '--note',
            metavar='SOURCE_NOTE',
            help='Description of the data source for any new inputs. '\
            'Give enough detail for traceability.')
        parser = add_settings_options_to_parser(parser)
        return parser

    @classmethod
    def _validate_args(cls, args):
        if not args.inputs:
            return
        for input in arg.inputs:
            vals = input.split('=')
            if not len(vals) == 2 or vals[0] == '':
                raise InvalidInputError('Invalid input key-value pair "%s". Must be of the form key=value or key=value1,value2,...' % input)

    def run(self):
        workflow = self._get_workflow(self.args.workflow)
        inputs = self._get_inputs(self.args.inputs)
        run_request = self.objecthandler.post_run_request(
            {
                'workflow': workflow,
                'inputs': inputs
            }
        )

        self.logger.info('Created run request %s@%s' \
            % (run_request['workflow']['name'],
               run_request['_id']
            ))
        return run_request

    def _get_workflow(self, workflow_id):
        if os.path.isfile(workflow_id):
            return self._get_workflow_from_file(workflow_id)
        else:
            return self._get_workflow_from_server(workflow_id)
        
    def _get_workflow_from_file(self, workflow_filename):
        return WorkflowImporter.import_workflow(workflow_filename, self.master_url, self.logger)

    def _get_workflow_from_server(self, workflow_id):
        workflows = self.objecthandler.get_workflow_index(query_string=workflow_id)

        if len(workflows) < 1:
            raise Exception('Could not find workflow that matches "%s"' % workflow_id)
        elif len(workflows) > 1:
            raise Exception('Multiple workflows on the server matched "%s". Try using the full id. \n%s' %
                            (workflow_id, '\n'.join(
                                [workflow['workflow_name']+'@'+workflow['_id'][:12] for workflow in workflows]
                            )))
        else:
            return workflows[0]

    def _get_inputs(self, input_args):
        """Converts command line args into a list of workflow inputs
        """
        inputs = []
        if input_args:
            for kv_pair in input_args:
                (channel, input_id) = kv_pair.split('=')
                inputs.append(self._get_input(channel, input_id))
        return inputs

    def _get_input(self, channel, input_id):
        """If input_id is a local file, upload it.
        Otherwise let the server try to resolve the input_id.
        """
        if os.path.isfile(input_id):
            input_id = self._get_input_from_file(input_id)
        return {'channel': channel, 'id': input_id}

    def _get_input_from_file(self, input_filename):
        file_import = self.filehandler.import_file(input_filename, self.args.note)
        return "%s@%s" % (file_import['file_data_object']['filename'],
                          file_import['file_data_object']['_id'])

    """
    def _validate_workflow(self):
        if workflow.get('workflow_inputs'):
            if not isinstance(workflow['workflow_inputs'], list):
                raise ValidationError('Workflow is invalid. "workflow_inputs" should contain a list but it contains "%s"'\
                                      % workflow.get('workflow_inputs'))
            for input in workflow['workflow_inputs']:
                if not isinstance(input, dict):
                    raise ValidationError('Workflow is invalid. Workflow input should be a dict but it contains "%s"'\
                                          % input)
                if not input.get('to_channel'):
                    raise ValidationError('Workflow is invalid. "to_channel" is not defined for this input: "%s"' % input)
                if not input.get('type'):
                    raise ValidationError('Workflow is invalid. "type" is not defined for this input: "%s"' % input)
    """


if __name__=='__main__':
    WorkflowRunner().run()
