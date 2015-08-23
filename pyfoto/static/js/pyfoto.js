/**
 * Created by chris on 8/22/2015.
 */

var pyfotoApp = angular.module('pyfotoApp', []);


pyfotoApp.controller('indexController', ['$scope', '$http', function($scope, $http) {
    $scope.imageList = [];
    $scope.currentDir = "";
    $scope.currentDirPath = [];
    $scope.folderList = [];
    $scope.currentImage = "";
    $scope.listIndex = 0;

    $scope.getFolders = function(){
            $http.get("/folder")
                .success(function (response) {
                    $scope.folderList = response.folders;
                    console.log(response.folders);
                });
    };

    $scope.getItems = function(folder){
        $scope.currentDir = folder;
            $http.get("/folder/"+ folder)
                .success(function (response) {
                    $scope.imageList = response.files;
                    $scope.currentDirPath = response.path;
                    $scope.currentImage = "/item/" + $scope.currentDir + "/" + $scope.imageList[0];
                    $scope.listIndex = 0;
        });
    };

    $scope.prevItem = function(){
        $scope.listIndex--;
        if ($scope.listIndex < 0){
            $scope.listIndex = $scope.imageList.length - 1;
        }
        $scope.currentImage = "/item/" + $scope.currentDir + "/" + $scope.imageList[$scope.listIndex];
        $scope.$apply();
    };

    $scope.nextItem = function(){
        $scope.listIndex++;
        if ($scope.listIndex > $scope.imageList.length){
            $scope.listIndex = 0;
        }

        $scope.currentImage = "/item/" + $scope.currentDir + "/" + $scope.imageList[$scope.listIndex];
        $scope.$apply();
    };

    $scope.keyHandler = function(e){
        if(e.keyCode === 39) {
            //right arrow
            $scope.nextItem();
        } else if(e.keyCode === 37) {
            //left arrow
            $scope.prevItem();
        }
    };

    var $doc = angular.element(document);

    $doc.on('keydown', $scope.keyHandler);
    $scope.$on('$destroy',function(){
        $doc.off('keydown', $scope.keyHandler);
    });


    $scope.getFolders();
    //$scope.getFolders();




}]);