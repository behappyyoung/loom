'use strict';

angular
    .module('loom.controllers')
    .controller('FileListController', FileListController);

FileListController.$inject = ['$scope', '$http', 'Data', '$state'];

function FileListController($scope, $http, Data, $state){
    $http.get('/api/file_data_objects')
	.success(function(response) {
	    Data.files = response['file_data_objects'];
	    $scope.files = Data.files;
	    
	    $scope.files.forEach(function(file) {
		$http.get('/api/file_data_objects/' + file._id + '/data_source_records/')
		    .then(function(response){
			file['data_source_records'] = response['data']['data_source_records'];
		    });
		$http.get('/api/file_data_objects/' + file._id + '/file_storage_locations/')
		    .then(function(response){
			file['file_storage_locations'] = response['data']['file_storage_locations'];
		    });
	    });
	});
    $scope.$state = $state;
};

