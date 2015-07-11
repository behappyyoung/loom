from django.conf import settings
import os

with open(os.path.join(settings.BASE_DIR,'../../doc/examples/helloworld/helloworld.json')) as f:
    helloworld_json = f.read()

{
    'step_definition': 
    {
        'template': {
            'environment': {
                'docker_image': u'ubuntu'
                }, 
            'command': u'echo world > world.txt', 
            'output_ports': [
                {
                    'file_path': u'world.txt'
                    }
                ]
            }
        }, 
    'is_complete': True, 
    }


hello_world_step_definition_obj1 = {
    "template":
        {
        "command":"echo world > world.txt",
        "environment": {
            "docker_image":"ubuntu"
            },
        "output_ports": [
            {
                "file_path": "world.txt"
                }
            ]
        }
    }


hello_world_step_run_obj1 = {
    "output_binding": {
        "file": {
            "hash_function":"md5",
            "hash_value":"8c2753548775b4161e531c323ea24c08"
            },
        "output_port": {
            "file_path": "world.txt"
            }
        },
    "step_definition": hello_world_step_definition_obj1,
    }

hello_world_step_result_obj1 = {
    'step_definition': hello_world_step_definition_obj1,
    'output_binding': {
        'output_port': {
            'file_path': u'world.txt',
            }, 
        'file': {
            'hash_value': u'8c2753548775b4161e531c323ea24c08', 
            'hash_function': u'md5'
            }
        }
    }

hello_world_step_definition_obj2 = {
    'data_bindings': [
        {
            'input_port': {
                'file_path': u'hello.txt'
                }, 
            'file': {
                'hash_value': u'b1946ac92492d2347c6235b4d2611184', 
                'hash_function': u'md5'
                }
            }
        ], 
    'template': {
        'environment': {
            'docker_image': u'ubuntu'
            }, 
        'input_ports': [
            {
                'file_path': u'hello.txt'
                }, 
            {
                'file_path': u'world.txt'
                }
            ], 
        'command': u'cat hello.txt world.txt > hello_world.txt', 
        'output_ports': [
            {
                'file_path': u'hello_world.txt'
                }
            ]
        }
    }

hello_world_step_result_obj2 = {
    'step_definition': hello_world_step_definition_obj2,
    'output_binding': {
        'output_port': {
            'file_path': u'hello_world.txt'
            }, 
        'file': {
            'hash_value': u'ffdc12d8d601ae40f258acf3d6e7e1fb', 
            'hash_function': u'md5'
            }
        }
    }

hello_world_step_run_obj1 = {
    "is_complete": True,
    "step_definition": hello_world_step_definition_obj1,
    "step_results": [
        hello_world_step_result_obj1,
        ]
    }

hello_world_step_run_obj2 = {
    'step_definition': hello_world_step_definition_obj2,
    'is_complete': True, 
    'step_results': [hello_world_step_result_obj2]
    }

file_obj = {
    'hash_value': '1234asfd',
    'hash_function': 'md5',
    }

file_path_location_obj = {
    'file': file_obj,
    'file_path': '/absolute/path/to/my/file.txt',
    }

docker_image_obj = {
    'docker_image': '1234567asdf',
    }

step_definition_input_port_obj = {
    'file_path':'copy/my/file/here.txt',
    }

step_definition_output_port_obj = {
    'file_path':'look/for/my/file/here.txt',
    }

step_definition_data_binding_obj = {
    'file': file_obj,
    'input_port': step_definition_input_port_obj,
    }

template_obj = {
    'input_ports': [step_definition_input_port_obj],
    'output_ports': [step_definition_output_port_obj],
    'command': 'echo test',
    'environment': docker_image_obj,
    }

step_obj = {
    'template': template_obj,
    'data_bindings': [step_definition_data_binding_obj],
    }

docker_image_obj = {
    'docker_image': 'ubuntu',
    }

input_port_obj_1 = {
    'name': 'input_port1',
    'file_path': 'rel/path/to/input_file',
    }

output_port_obj_1 = {
    'name': 'output_port1',
    'file_path': 'rel/path/to/output_file',
    }

input_port_obj_2 = {
    'name': 'input_port2',
    'file_path': 'rel/path/to/input_file',
    }

output_port_obj_2 = {
    'name': 'output_port2',
    'file_path': 'rel/path/to/output_file',
    }

port_identifier_obj = {
    'step': 'stepname',
    'port': 'portname',
    }

data_binding_obj = {
    'file': file_obj,
    'destination': {
        'step': 'step1',
        'port': 'input_port1',
        },
    }

data_pipe_obj = {
    'source': {
        'step': 'step1',
        'port': 'output_port1',
        },
    'destination': {
        'step': 'step2',
        'port': 'input_port2',
        },
    }

resource_set_obj = {
    'memory': '5G',
    'cores': 4,
    }

step_obj_1 = {
    'name': 'step1',
    'input_ports': [input_port_obj_1],
    'output_ports': [output_port_obj_1],
    'command': 'echo hello',
    'environment': docker_image_obj,
    'resources': resource_set_obj,
    }

step_obj_2 = {
    'name': 'step2',
    'input_ports': [input_port_obj_2],
    'output_ports': [output_port_obj_2],
    'command': 'echo world',
    'environment': docker_image_obj,
    'resources': resource_set_obj,
    }

analysis_obj = {
    'steps': [step_obj_1, step_obj_2],
    'data_bindings': [data_binding_obj],
    'data_pipes': [data_pipe_obj],
    }

request_obj = {
    'analyses': [analysis_obj],
    'requester': 'someone@example.com',
    }
