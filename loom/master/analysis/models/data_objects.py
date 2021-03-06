from analysis.exceptions import DataObjectValidationError
from analysis.models.base import AnalysisAppInstanceModel, \
    AnalysisAppImmutableModel
from universalmodels import fields


class DataObject(AnalysisAppImmutableModel):
    """A unit of data passed into or created by analysis steps.
    This may be a file, an array of files, a JSON data object, 
    or an array of JSON objects.
    """
    pass


class DataSourceRecord(AnalysisAppInstanceModel):
    data_objects = fields.ManyToManyField(DataObject,
                                          related_name = 'data_source_records')
    source_description = fields.TextField(max_length=10000)

    
class DataObjectArray(DataObject):
    """An array of data objects, all of the same type.
    """
    data_objects = fields.ManyToManyField('DataObject',
                                          related_name = 'parent')

    @classmethod
    def create(cls, data):
        o = super(DataObjectArray, cls).create(data)
        cls._verify_children_have_same_type(o)
        return o

    def _verify_children_have_same_type(self):
        child_classes = set()
        for data_object in self.data_objects.all():
            child_classes.add(data_object.downcast().__class__)
            if len(child_classes) > 1:
                raise DataObjectValidationError()
    
    def is_available(self):
        """An array is available if all members are available"""
        return all([member.downcast().is_available() for member in
                    self.data_objects.all()])

    
class FileDataObject(DataObject):
    """Represents a file, including its contents (identified by a hash), its 
    file name, and user-defined metadata.
    """

    NAME_FIELD = 'file_name'

    file_name = fields.CharField(max_length=255)
    file_contents = fields.ForeignKey('FileContents')
    metadata = fields.JSONField()

    def is_available(self):
        """A file is available if we can find any storage location for the file 
        contents
        """
        return self.file_contents.has_storage_location()

class FileContents(AnalysisAppImmutableModel):
    """Represents file contents, identified by a hash. Ignores file name.
    """

    hash_value = fields.CharField(max_length=100)
    hash_function = fields.CharField(max_length=100)

    def has_storage_location(self):
        return self.file_storage_locations.exists()


class FileStorageLocation(AnalysisAppInstanceModel):
    """Base class for any type of location where a specified set 
    of file contents can be found.
    """

    file_contents = fields.ForeignKey('FileContents', null=True, related_name='file_storage_locations')

    @classmethod
    def get_by_file(self, file):
        locations = self.objects.filter(file_contents=file.file_contents).all()
        return locations

    
class ServerStorageLocation(FileStorageLocation):
    """File server where a specified set of file contents can be found and 
    accessed by ssh.
    """

    host_url = fields.CharField(max_length=256)
    file_path = fields.CharField(max_length=256)

    
class GoogleCloudStorageLocation(FileStorageLocation):
    """Project, bucket, and path where a specified set of file contents can be 
    found and accessed using Google Cloud Storage.
    """

    project_id = fields.CharField(max_length=256)
    bucket_id = fields.CharField(max_length=256)
    blob_path = fields.CharField(max_length=256)

class DatabaseDataObject(DataObject):

    def is_available(self):
        """An object stored in the database is always available.
        """
        return True

    class Meta:
        abstract = True

class JSONDataObject(DatabaseDataObject):
    """Contains any valid JSON value. This could be 
    an integer, string, float, boolean, list, or dict
    """

    json_data = fields.JSONField()

class StringDataObject(DatabaseDataObject):

    string_value = fields.TextField()

class BooleanDataObject(DatabaseDataObject):

    boolean_value = fields.BooleanField()

class IntegerDataObject(DatabaseDataObject):

    integer_value = fields.IntegerField()
