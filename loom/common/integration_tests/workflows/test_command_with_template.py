import os
from loom.common.fixtures import *
from loom.common.integration_tests.workflows.abstract_workflow_tester import AbstractWorkflowTester

command_with_template_json_path = os.path.join(
    os.path.dirname(__file__), 
    '../../../common/fixtures/workflows/command_with_template/command_with_template.json')

hello_file = os.path.join(
    os.path.dirname(__file__), 
    '../../../common/fixtures/workflows/command_with_template/hello.txt')

class TestArrayInWorkflow(AbstractWorkflowTester):
    pass
    """
    def setUp(self):

        self.start_server()
        self.upload(hello_file)
        self.start_job(command_with_template_json_path)
        self.wait_for_job()

    def tearDown(self):
        self.stop_server()

    def testWorkflow(self):
        self.assertTrue(True)
    """
