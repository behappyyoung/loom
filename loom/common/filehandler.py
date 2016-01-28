#!/usr/bin/env python

import abc
import datetime
import errno
import json
import os
import shutil
import socket
import subprocess

import gcloud.storage
import requests

from loom.common import md5calc

# Google Storage JSON API imports
from apiclient.http import MediaIoBaseDownload
from oauth2client.client import GoogleCredentials
import apiclient.discovery


class FileHandlerError(Exception):
    pass


def FileHandler(master_url):
    """Factory method that communicates with master server to retrieve settings and
    determine which concrete subclass to instantiate."""
    settings = _get_settings(master_url)
    if settings['FILE_SERVER_TYPE'] == 'LOCAL':
        return LocalFileHandler(master_url, settings)
    elif settings['FILE_SERVER_TYPE'] == 'REMOTE':
        return RemoteFileHandler(master_url, settings)
    elif settings['FILE_SERVER_TYPE'] == 'GOOGLE_CLOUD':
        return GoogleCloudFileHandler(master_url, settings)
    else:
        raise FileHandlerError('Unrecognized file server type: %s' % settings['FILE_SERVER_TYPE'])

def _get_settings(master_url):
    url = master_url + '/api/filehandlerinfo/'
    response = requests.get(url)
    response.raise_for_status()
    settings = response.json()['filehandlerinfo']
    return settings


class AbstractFileHandler:
    """Abstract base class for filehandlers.

    Public interface and required overrides. Perform file transfer or create locations
    differently depending on fileserver type.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, master_url, settings):
        self.master_url = master_url
        self.settings = settings

    @abc.abstractmethod
    def upload(self, local_path, destination_location):
        pass

    @abc.abstractmethod
    def download(self, source_location, local_path):
        pass

    @abc.abstractmethod
    def get_step_output_location(self, local_path, file_object=None):
        pass

    @abc.abstractmethod
    def get_import_location(self, local_path, file_object=None, file_id=None):
        pass

    def _get_import_path(self, file_id, local_path):
        """Imported files are placed in IMPORT_DIR and named with timestamp, file ID, and filename.""" 
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss")
        return os.path.join(
            self.settings['FILE_ROOT'],
            self.settings['IMPORT_DIR'],
            "%s_%s_%s" % (timestamp, file_id[0:10], os.path.basename(local_path)),
        )

    def _get_step_output_path(self, local_path):
        """Step outputs are placed in directories of the same name as the
        local directories, and named with the same filename. 
        """
        filename = os.path.basename(local_path)
        step_run_dir = os.path.basename(os.path.dirname(local_path))
        workflow_dir = os.path.basename(os.path.dirname(os.path.dirname(local_path)))
        workflows_dir = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(local_path))))
        return os.path.join(
            self.settings['FILE_ROOT'],
            workflows_dir,
            workflow_dir,
            step_run_dir,
            filename
        )


class AbstractPosixPathFileHandler(AbstractFileHandler):
    """Base class for filehandlers that deal with POSIX-style file paths."""
    __metaclass__ = abc.ABCMeta

    def get_step_output_location(self, local_path, file_object=None):
        if file_object is None:
            file_object = create_file_object(local_path)
        location = {
            'file_contents': file_object['file_contents'],
            'file_path': self._get_step_output_path(local_path),
            'host_url': self.settings['FILE_SERVER_FOR_WORKER']
            }
        return location

    def get_import_location(self, local_path, file_object=None, file_id=None):
        if file_object is None:
            file_object = create_file_object(local_path)
        if file_id is None:
            file_id = post_file_object(self.master_url, file_object) #hidden side effect; get file id without posting?
        location = {
            'file_contents': file_object['file_contents'],
            'file_path': self._get_import_path(file_id, local_path), 
            'host_url': self.settings['FILE_SERVER_FOR_WORKER']
            }
        return location


class LocalFileHandler(AbstractPosixPathFileHandler):
    """Subclass of FileHandler that uses cp or ln to 'copy' files."""

    def upload(self, local_path, destination_location):
        """For imports, create imports directory and copy file.
        For step outputs, don't need to do anything, because the working directory is the destination."""
        destination_path = destination_location['file_path']
        if local_path != destination_path:
            try:
                os.makedirs(os.path.dirname(destination_path))
            except OSError as e:
                if e.errno == errno.EEXIST:
                    pass
                else:
                    raise e
            shutil.copyfile(local_path, destination_path)
        return

    def download(self, source_location, local_path):
        """Save space by hardlinking file into the working dir instead of copying. However, won't
        work if the two locations are on different filesystems.
        """
        cmd = ['ln', source_location['file_path'], local_path]
        subprocess.call(cmd)


class RemoteFileHandler(AbstractPosixPathFileHandler):
    """Subclass of FileHandler that uses ssh and scp to copy files."""

    def upload(self, local_path, destination_location):
        destination_path = destination_location['file_path']
        subprocess.call(
            ['ssh',
             self.fileserver,
             'mkdir',
             '-p',
             os.path.dirname(destination_path)]
             )
        subprocess.call(
            ['scp',
             local_path,
             ':'.join([self.fileserver, destination_path])]
            )

    def download(self, source_location, local_path):
        subprocess.call(
            ['scp',
             ':'.join([source_location['host_url'], source_location['file_path']]),
             local_path]
            )

    def get_cluster_remote_path(self, username):
        if not hasattr(self,'_remote_path'):
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss")
            self._remote_path = os.path.join(
                '/home',
                username,
                'working_dir',
                self.IMPORTED_FILES_DIR,
                "%s_%s_%s" % (timestamp, self.file_id[0:10], os.path.split(self.local_path)[1]),
            )
        return self._remote_path

class ElasticlusterFileHandler(AbstractPosixPathFileHandler):
    """ TODO: Use elasticluster and GCE-specific parameters for file transfer. 
    Consider using elasticluster's ssh and sftp commands instead.
    - Would decouple loom from cloud specifics (key management, username, fileserver IP).
    - However, nesting virtualenvs seems problematic, and would have to locate
      elasticluster installation or let user specify.
    """

    def _upload_file_to_elasticluster(self):
        username = self.settings_manager.get_remote_username()
        gce_key = os.path.join(os.getenv('HOME'),'.ssh','google_compute_engine')
        if not os.path.exists(gce_key):
            raise FileHandlerError("GCE key not found at %s" % gce_key)
        print "Creating working directory on elasticluster at %s" % self.file_server
        subprocess.check_call(
            ['ssh',
             username+'@'+self.file_server,
             '-i',
             gce_key,
             'mkdir',
             '-p',
             os.path.dirname(self.get_cluster_remote_path(username))]
             )
        print "Uploading file to elasticluster at %s" % self.file_server
        subprocess.check_call(
            ['scp',
             '-i',
             gce_key,
             self.local_path,
             ':'.join([username+'@'+self.file_server, self.get_cluster_remote_path(username)])]
            )


class GoogleCloudFileHandler(AbstractFileHandler):
    """Subclass of FileHandler that uses the gcloud module to copy files to and from Google Storage."""

    def upload(self, local_path, destination_location):
        blob = self._get_blob(destination_location)
        blob.upload_from_filename(local_path)

    def download(self, source_location, local_path):
        blob = self._get_blob(source_location)
        blob.download_to_filename(local_path)

    def download_with_json_api(self, destination_location, local_path):
        """Download using Google Storage JSON API instead of gcloud-python."""
        blob_path = destination_location['blob_path']
        bucket_id = destination_location['bucket_id']
        credentials = GoogleCredentials.get_application_default()
        service = apiclient.discovery.build('storage', 'v1', credentials=credentials)
        file_request = service.objects().get_media(bucket=bucket_id, object=blob_path)
        with open(local_path, 'w') as local_file:
            downloader = MediaIoBaseDownload(local_file, file_request, chunksize=1024*1024)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print 'Download %d%%.' % int(status.progress() * 100)
                print 'Download Complete!'

    def _get_blob(self, location):
        """Instantiate, configure, and return a gcloud blob."""
        blob_path = location['blob_path']
        project_id = location['project_id']
        bucket_id = location['bucket_id']
        client = gcloud.storage.client.Client(project_id)
        bucket = client.get_bucket(bucket_id)
        blob = bucket.get_blob(blob_path)
        if blob is None:
            blob = gcloud.storage.blob.Blob(blob_path, bucket)
        return blob

    def get_step_output_location(self, local_path, file_object=None):
        if file_object is None:
            file_object = create_file_object(local_path)
        location = {
            'file_contents': file_object['file_contents'],
            'project_id': self.settings['PROJECT_ID'],
            'bucket_id': self.settings['BUCKET_ID'],
            'blob_path': self._get_step_output_path(local_path),
            }
        return location

    def get_import_location(self, local_path, file_object=None, file_id=None):
        if file_object is None:
            file_object = create_file_object(local_path)
        if file_id is None:
            file_id = post_file_object(self.master_url, file_object) #hidden side effect; get file id without posting?
        location = {
            'file_contents': file_object['file_contents'],
            'project_id': self.settings['PROJECT_ID'],
            'bucket_id': self.settings['BUCKET_ID'],
            'blob_path': self._get_import_path(file_id, local_path), 
            }
        return location


# Utility functions used by FileHandlers as well as external modules.
def create_file_object(file_path):
    file = {
        'file_contents': {
            'hash_value': md5calc.calculate_md5sum(file_path),
            'hash_function': 'md5',
        },
        'metadata': {
            'filename': os.path.basename(file_path)
        }
    }
    return file

def post_file_object(url, file_obj):
    """Register a file object with the server."""
    try:
        response = requests.post(url+'/api/files', data=json.dumps(file_obj))
    except requests.exceptions.ConnectionError as e:
        raise FileHandlerError("No response from server %s\n%s" % (url, e))
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise FileHandlerError("%s\n%s" % (e.message, response.text))
    return response.json().get('_id')

def post_location(url, file_storage_location_obj):
    """Register a file storage location with the server."""
    try:
        response = requests.post(url+'/api/file_storage_locations', data=json.dumps(file_storage_location_obj))
    except requests.exceptions.ConnectionError as e:
        raise FileHandlerError("No response from server %s\n%s)" % (url, e))
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise FileHandlerError("%s\n%s" % (e.message, response.text))
    return response.json().get('_id')