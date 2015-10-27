/**
 * Created by chris on 8/22/2015.
 */

var pyfotoApp = angular.module('pyfotoApp', []);


pyfotoApp.controller('indexController', ['$scope', '$http', function($scope, $http) {
    $scope.currentImage = "";
    $scope.currentID = 1;
    $scope.currentName = "";

    $scope.starts = function(){
        $http.get("/search?count=1")
            .success(function (response) {
                $scope.currentID = response.data[0].id;
                $scope.currentImage = "/item/" + response.data[0].path;
                $scope.currentName = response.data[0].filename;
                $scope.$apply();
            });
    };

    $scope.nextItem = function(){
        $http.get("/next/" + $scope.currentID + "?count=1")
            .success(function (response) {
                if (response.data.length == 0){
                    return false;
                }
                else {
                    $scope.currentID = response.data[0].id;
                    $scope.currentImage = "/item/" + response.data[0].path;
                    $scope.currentName = response.data[0].filename;
                    $scope.$apply();
                }
            })

    };

        $scope.prevItem = function(){
        $http.get("/prev/" + $scope.currentID + "?count=1")
            .success(function (response) {
                console.log(response);
                if (response.data.length == 0){
                    return false;
                } else {
                    $scope.currentID = response.data[0].id;
                    $scope.currentImage = "/item/" + response.data[0].path;
                    $scope.currentName = response.data[0].filename;
                    $scope.$apply();
                }
            })

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


    $scope.starts();
    //$scope.getFolders();

}]);