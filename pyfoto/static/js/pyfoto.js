/**
 * Created by chris on 8/22/2015.
 */


var pyfotoApp = angular.module('pyfotoApp', []);


pyfotoApp.controller('indexController', ['$scope', '$http',  function($scope, $http) {
    $scope.galleryImages = [];

    $scope.currentImage = "";
    $scope.currentID = 1;
    $scope.currentName = "";
    $scope.currentTags = [];
    $scope.currentSeries = [];
    $scope.availTags = [];
    $scope.currentFilters = "";

    $scope.tags = [];

    $scope.update = function(response){
        $scope.currentID = response.data[0].id;
        $scope.currentImage = response.data[0].path;
        $scope.currentName = response.data[0].filename;
        $scope.currentTags = response.data[0].tags;
        $scope.currentSeries = response.data[0].series;
        $scope.availTags.length = 0;

        angular.forEach($scope.tags, function(value){
            if($scope.currentTags.indexOf(value) == -1){
                $scope.availTags.push(value);
            }
        });
    };

    $scope.removeCurrentTag = function(tag) {
        var index = $scope.currentTags.indexOf(tag);
        $scope.currentTags.splice(index, 1);
    };

    $scope.updateAvailTags = function(){
        $scope.availTags = [];
        angular.forEach($scope.tags, function(value){
            if($scope.currentTags.indexOf(value) == -1){
                $scope.availTags.push(value);
            }
        });
        $scope.availTags.sort();
    };

    $scope.deleteImage = function(){
          $http.delete("/file/" + $scope.currentID)
              .success(function (response) {
                    $scope.nextItem();
                });

    };

    $scope.starts = function(){
            $http.get("/file?count=100")
              .success(function (response) {
                    $scope.toggleImage("off");
                   $scope.galleryImages = response.data;
                    $scope.currentFilters = $scope.searchInput;
                    $scope.searchInput = "";
                });
    };

    $scope.nextItem = function(){
        var url = "/next/" + $scope.currentID + "?count=1";
        if ($scope.currentFilters != "" && $scope.currentFilters != undefined){
            url += "&search="+$scope.currentFilters;
        }
        $http.get(url)
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
        var url = "/prev/" + $scope.currentID + "?count=1";
            if ($scope.currentFilters != ""  && $scope.currentFilters != undefined){
                url += "&search="+$scope.currentFilters;
            }

        $http.get(url)
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
                $scope.tags.push($scope.tagInput);
               $scope.currentTags.push($scope.tagInput);
                $scope.tagInput = "";
            });
    };

    $scope.modifyTag = function(tag, action){
        if(action=='add'){
            $http.post("/file/" + $scope.currentID + "/tag/" + tag)
            .success(function (response) {
                   $scope.currentTags.push(tag);
                    $scope.updateAvailTags();
                });
        } else if (action == 'remove') {
            $http.delete("/file/" + $scope.currentID + "/tag/" + tag)
            .success(function (response) {
                   $scope.removeCurrentTag(tag);
                    $scope.updateAvailTags();
                });
        }

    };


    $scope.allTags = function(){
        $http.get("/tag")
            .success(function (response) {
                angular.forEach(response.data, function(value){
                   $scope.tags.push(value);
                });
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

    $scope.toggleImage = function(way) {
        if (way == "off"){
            $(".main-image").hide();
            $(".image-data").hide();
            $(".gallery").show();
            $(".back-to-search").hide();
            $(".search-data").show();
        } else {
            $(".main-image").show();
            $(".image-data").show();
            $(".gallery").hide();
            $(".back-to-search").show();
            $(".search-data").hide();
        }
    };


    $scope.searchImages = function(){
        if ($scope.searchInput == "" || $scope.searchInput == undefined){
            $http.get("/file")
              .success(function (response) {
                    $scope.toggleImage("off");
                   $scope.galleryImages = response.data;
                    $scope.currentFilters = $scope.searchInput;
                    $scope.searchInput = "";
                });

        } else {

            $http.get("/search?search=" + $scope.searchInput)
                .success(function (response) {
                    $scope.toggleImage("off");
                    $scope.galleryImages = response.data;
                    $scope.currentFilters = $scope.searchInput;
                    $scope.searchInput = "";
                });
        }

    };

    $scope.openImage = function(file_id){
        $http.get("/file/" + file_id)
            .success(function (response) {
                if (response.data == undefined || response.data.length == 0){
                    alert("Cannot open file");

                } else {
                    $scope.update(response);
                    $scope.toggleImage("on");
                }
            })
    };

    $scope.nextPage = function(){
        var highest = Math.max.apply(Math,$scope.galleryImages.map(function(o){return o.id;}));
        var url = "/next/" + highest + "?count=100";
        if ($scope.currentFilters != "" && $scope.currentFilters != undefined){
            url += "&search="+$scope.currentFilters;
        }
        $http.get(url)
            .success(function (response) {
                if (response.data.length == 0){
                    return false;
                }
                else {
                    angular.forEach(response.data, function(value){
                        $scope.galleryImages.push(value);
                        if ($scope.galleryImages.length >= 1000){
                            $scope.galleryImages.splice(0,1);
                        }
                    });
                }
            })
    };


    $scope.searchTag = function(tag){
        $scope.searchInput = tag;
        $scope.searchImages();
    }

    var $doc = angular.element(document);

    $doc.on('keydown', $scope.keyHandler);
    $scope.$on('$destroy',function(){
        $doc.off('keydown', $scope.keyHandler);
    });

    $scope.toggleImage("off");
    $scope.starts();
    $scope.allTags();

}]);