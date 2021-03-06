import abc
import logging

from django.conf import settings

from loom.master.analysis.task_manager.local import LocalTaskManager
from loom.master.analysis.task_manager.cluster import ClusterTaskManager
from loom.master.analysis.task_manager.cloud import CloudTaskManager
from loom.master.analysis.task_manager.dummy import DummyTaskManager

logger = logging.getLogger('LoomDaemon')

class TaskManagerFactory:
    LOCAL = 'LOCAL'
    CLUSTER = 'ELASTICLUSTER'
    GOOGLE_CLOUD = 'GOOGLE_CLOUD'
    DUMMY = 'DUMMY'

    @classmethod
    def get_task_manager(cls, test=False):
        if test == True:
            return DummyTaskManager()
        
        logger.debug('Getting task manager of type "%s"' % settings.WORKER_TYPE)
        if settings.WORKER_TYPE == cls.LOCAL:
            return LocalTaskManager()
        elif settings.WORKER_TYPE == cls.CLUSTER:
            return ClusterTaskManager()
        elif settings.WORKER_TYPE == cls.GOOGLE_CLOUD:
            return CloudTaskManager()
        elif settings.WORKER_TYPE == cls.DUMMY:
            return DummyTaskManager()
        else:
            raise Exception('Invalid selection WORKER_TYPE=%s' % settings.WORKER_TYPE)


class TaskManager:
    __metaclass__ = abc.ABCMeta
    """ Abstract base class for TaskManagers."""
    
    @abc.abstractmethod
    def run(cls, task_run, task_run_location_id, requested_resources):
        """ Subclasses are required to implement this function prototype."""
        pass

TaskManager.register(LocalTaskManager)
TaskManager.register(ClusterTaskManager)
TaskManager.register(CloudTaskManager)
TaskManager.register(DummyTaskManager)
