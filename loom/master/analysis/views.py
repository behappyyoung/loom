import logging
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from analysis.models import WorkflowRun, TaskRun, FileDataObject
from loom.common import version
logger = logging.getLogger('loom')

class Helper:

    @classmethod
    def create(cls, request, model_class):
        data_json = request.body
        try:
            model = model_class.create(data_json)
            return JsonResponse({"message": "created %s" % model_class.get_class_name(), "_id": str(model._id), "object": model.to_struct()}, status=201)
        except Exception as e:
            logger.error('Failed to create %s with data "%s". %s' % (model_class, data_json, e.message))
            return JsonResponse({"message": e.message}, status=400)

    @classmethod
    def index(cls, request, model_class):
        query_string = request.GET.get('q')
        if query_string is None:
            model_list = model_class.objects.all()
        else:
            model_list = model_class.get_by_name_or_id(query_string)
        return JsonResponse(
            {
                model_class.get_class_name(plural=True):
                [model.to_struct() for model in model_list]
            },
            status=200)

    @classmethod
    def show(cls, request, id, model_class):
        try:
            model = model_class.get_by_id(id)
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Not Found"}, status=404)
        return JsonResponse(model.to_struct(), status=200)

    @classmethod
    def update(cls, request, id, model_class):
        data_json = request.body
        model = model_class.get_by_id(id)
        try:
            model.update(data_json)
            return JsonResponse({"message": "updated %s" % model_class.get_class_name(), "_id": str(model._id), "object": model.to_struct()}, status=201)
        except Exception as e:
            logger.error('Failed to update %s with data "%s". %s' % (model_class, data_json, e.message))
            return JsonResponse({"message": e.message}, status=400)

@require_http_methods(["GET"])
def status(request):
    return JsonResponse({"message": "server is up"}, status=200)

@require_http_methods(["GET"])
def server_time(request):
    return JsonResponse({"time": timezone.now().isoformat()}, status=200)

@require_http_methods(["GET"])
def worker_info(request):
    worker_info = {
        'FILE_SERVER_FOR_WORKER': settings.FILE_SERVER_FOR_WORKER,
        'FILE_ROOT_FOR_WORKER': settings.FILE_ROOT_FOR_WORKER,
        'LOG_LEVEL': settings.LOG_LEVEL,
        }
    return JsonResponse({'worker_info': worker_info})

@require_http_methods(["GET"])
def file_handler_info(request):
    file_handler_info = {
        'HASH_FUNCTION': settings.HASH_FUNCTION,
        'FILE_SERVER_FOR_WORKER': settings.FILE_SERVER_FOR_WORKER,
        'FILE_SERVER_TYPE': settings.FILE_SERVER_TYPE,
        'FILE_ROOT': settings.FILE_ROOT,
        'IMPORT_DIR': settings.IMPORT_DIR,
        'STEP_RUNS_DIR': settings.STEP_RUNS_DIR,
        'BUCKET_ID': settings.BUCKET_ID,
        'PROJECT_ID': settings.PROJECT_ID,
        }
    return JsonResponse({'file_handler_info': file_handler_info})

@csrf_exempt
@require_http_methods(["GET", "POST"])
def create_or_index(request, model_class):
    if request.method == "POST":
        return Helper.create(request, model_class)
    else:
        return Helper.index(request, model_class)
   
@csrf_exempt
@require_http_methods(["GET", "POST"])
def show_or_update(request, id, model_class):
    if request.method == "POST":
        return Helper.update(request, id, model_class)
    else:
        return Helper.show(request, id, model_class)

@require_http_methods(["GET"])
def storage_locations_by_file(request, id):
    try:
        file = FileDataObject.get_by_id(id)
    except ObjectDoesNotExist:
        return JsonResponse({"message": "Not Found"}, status=404)
    return JsonResponse({"file_storage_locations": [o.to_struct() for o in file.file_contents.file_storage_locations.all()]}, status=200)

@require_http_methods(["GET"])
def file_data_object_source_runs(request, id):
    try:
        file = FileDataObject.get_by_id(id)
    except ObjectDoesNotExist:
        return JsonResponse({"message": "Not Found"}, status=404)
    runs = []
    for task_run_output in file.taskrunoutput_set.all():
        runs.append({'step_run': {'_id': task_run_output.task_run.steprun._id.hex,
                                  'step_name': task_run_output.task_run.steprun.step.step_name},
                     'workflow_run': {'_id': task_run_output.task_run.steprun.workflow_run._id.hex,
                                      'workflow_name': task_run_output.task_run.steprun.workflow_run.workflow.workflow_name}})
    return JsonResponse({"runs": runs}, status=200)

@require_http_methods(["GET"])
def file_imports_by_file(request, id):
    try:
        file = FileDataObject.get_by_id(id)
    except ObjectDoesNotExist:
        return JsonResponse({"message": "Not Found"}, status=404)
    return JsonResponse({"file_imports": [o.to_struct() for o in file.file_imports.all()]}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
def update_tasks(request):
    WorkflowRun.update_status_for_all()
    return JsonResponse({"status": "ok"}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
def run_tasks(request):
    TaskRun.run_all()
    return JsonResponse({"status": "ok"}, status=200)

@require_http_methods(["GET"])
def info(request):
    data = {
        'version': version.version()
    }
    return JsonResponse(data, status=200)
