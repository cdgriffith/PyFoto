/**
 * Created by chris on 8/22/2015.
 */

function removeByValue(arr) {
    var what, a = arguments, L = a.length, ax;
    while (L > 1 && arr.length) {
        what = a[--L];
        while ((ax= arr.indexOf(what)) !== -1) {
            arr.splice(ax, 1);
        }
    }
    return arr;
}


var pyfotoApp = angular.module('pyfotoApp', []);


pyfotoApp.controller('indexController', ['$scope', '$http', function($scope, $http) {
    $scope.currentImage = "";
    $scope.currentID = 1;
    $scope.currentName = "";
    $scope.currentTags = [];
    $scope.currentSeries = [];
    $scope.availTags = [];

    $scope.tags = [];

    $scope.update = function(response){
        $scope.currentID = response.data[0].id;
        $scope.currentImage = "/item/" + response.data[0].path;
        $scope.currentName = response.data[0].filename;
        $scope.currentTags = response.data[0].tags;
        $scope.currentSeries = response.data[0].series;
        $scope.availTags = [];
        angular.forEach($scope.tags, function(value){
            if($scope.currentTags.indexOf(value) == -1){
                $scope.availTags.push(value);
            }
        });
        $scope.$apply();
    };

    $scope.starts = function(){
        $http.get("/search?count=1")
            .success(function (response) {
                $scope.update(response);
            });
    };

    $scope.nextItem = function(){
        $http.get("/next/" + $scope.currentID + "?count=1")
            .success(function (response) {
                if (response.data.length == 0){
                    return false;
                }
                else {
                    $scope.update(response);
                }
            })

    };

        $scope.prevItem = function(){
        $http.get("/prev/" + $scope.currentID + "?count=1")
            .success(function (response) {
                if (response.data.length == 0){
                    return false;
                } else {
                    $scope.update(response);
                }
            })
    };

    $scope.addTagToFile = function(){
        if ($scope.tagInput == "" || $scope.tagInput == undefined){
            alert("You're an idiot");
            return false;
        }

        $http.post("/file/" + $scope.currentID + "/tag/" + $scope.tagInput)
        .success(function (response) {
               $scope.currentTags.push($scope.tagInput);
                $scope.tagInput = "";
                //$scope.apply();
            });

    };

    $scope.allTags = function(){
        $http.get("/tag")
            .success(function (response) {
                angular.forEach(response.data, function(value){
                   $scope.tags.push(value);
                });
                console.log($scope.tags);
            });
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
    $scope.allTags();

}]);