from django.test import TestCase
import uuid

from analysis.exceptions import *
from analysis.models import *
from loom.common import fixtures

from .common import UniversalModelTestMixin


class TestFile(TestCase, UniversalModelTestMixin):

    def testFile(self):
        file = FileDataObject.create(fixtures.file_struct)
        self.assertEqual(file.file_contents.hash_value, fixtures.file_struct['file_contents']['hash_value'])
        self.roundTripJson(file)
        self.roundTripStruct(file)

    def testIsAvailable(self):
        file = FileDataObject.create(fixtures.file_struct)
        self.assertFalse(file.is_available())
        file_storage_location = FileStorageLocation.create(fixtures.server_storage_location_struct)
        self.assertTrue(file.is_available())


class TestDataObjectArray(TestCase, UniversalModelTestMixin):

    def testFileArray(self):
        file_array = DataObjectArray.create(fixtures.file_array_struct)
        self.assertEqual(file_array.data_objects.count(), len(fixtures.file_array_struct['data_objects']))
        self.roundTripJson(file_array)
        self.roundTripStruct(file_array)

    def testJsonArray(self):
        json_array = DataObjectArray.create(fixtures.json_array_struct)
        self.assertEqual(json_array.data_objects.count(), len(fixtures.json_array_struct['data_objects']))
        self.roundTripJson(json_array)
        self.roundTripStruct(json_array)

    def testEmptyArray(self):
        empty_array = DataObjectArray.create({'data_objects': []})
        self.roundTripJson(empty_array)
        self.roundTripStruct(empty_array)

    def testFileArrayIsAvailable(self):
        file_array = DataObjectArray.create({'data_objects': [fixtures.file_struct, fixtures.file_struct_2]})
        self.assertFalse(file_array.is_available())
        file_storage_location = FileStorageLocation.create(fixtures.server_storage_location_struct)
        self.assertFalse(file_array.is_available())
        file_storage_location_2 = FileStorageLocation.create(fixtures.server_storage_location_struct_2)
        self.assertTrue(file_array.is_available())

    def testJSONArrayIsAvailable(self):
        json_array = DataObjectArray.create(fixtures.json_array_struct)
        self.assertTrue(json_array.is_available())

    def testNegHeterogeneousArray(self):
        with self.assertRaises(DataObjectValidationError):
            heterogeneous_array = DataObjectArray.create(fixtures.heterogeneous_array_struct)


class TestFileStorageLocation(TestCase, UniversalModelTestMixin):

    def testFileStorageLocation(self):
        file_storage_location = FileStorageLocation.create(fixtures.server_storage_location_struct)
        self.assertEqual(file_storage_location.file_path, fixtures.server_storage_location_struct['file_path'])
        self.roundTripJson(file_storage_location)
        self.roundTripStruct(file_storage_location)

    def testGetByFile(self):
        storage_location = FileStorageLocation.create(fixtures.server_storage_location_struct)
        file = FileDataObject.create(fixtures.file_struct)
        retrieved_storage_location = FileStorageLocation.get_by_file(file).first()
        self.assertEqual(uuid.UUID(str(storage_location._id)), uuid.UUID(str(retrieved_storage_location._id)))


class TestServerStorageLocation(TestCase, UniversalModelTestMixin):

    def testServerStorageLocation(self):
        server_storage_location = ServerStorageLocation.create(fixtures.server_storage_location_struct)
        self.assertEqual(server_storage_location.file_path, fixtures.server_storage_location_struct['file_path'])
        self.roundTripJson(server_storage_location)
        self.roundTripStruct(server_storage_location)
