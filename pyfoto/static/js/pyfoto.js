/**
 * Created by chris on 8/22/2015.
 */


var pyfotoApp = angular.module('pyfotoApp', []);

pyfotoApp.directive("starRating", function(){

return {
			restrict : 'A',
			template : '<ul class="rating">'
					 + '<li ng-repeat="star in stars" ng-class="star" ng-click="toggle($index)">'
					 + '<span class="glyphicon glyphicon-star"></span>'
					 + '</li>'
					 + '</ul>',
			scope : {
				ratingValue : '=',
				max : '=',
				onRatingSelected : '&'
			},
			link : function(scope, elem, attrs) {
				var updateStars = function() {
					scope.stars = [];
					for ( var i = 0; i < scope.max; i++) {
						scope.stars.push({
							filled : i < scope.ratingValue
						});
					}
				};

				scope.toggle = function(index) {
					scope.ratingValue = index + 1;
					scope.onRatingSelected({
						rating : index + 1
					});
				};

				scope.$watch('ratingValue',
					function(oldVal, newVal) {
						if (newVal >= 0) {
							updateStars();
						}
					}
				);
			}
		};


});



pyfotoApp.controller('indexController', ['$scope', '$http',  function($scope, $http) {
    $scope.galleryImages = [];
    $scope.tags = [];
    $scope.availTags = [];

    $scope.currentImage = "";
    $scope.currentID = 1;
    $scope.currentName = "";
    $scope.currentFilename = "";
    $scope.currentTags = [];
    $scope.currentFilters = "";
    $scope.currentRating = 0;

    $scope.showGallery = true;
    $scope.showFilename = true;


    $scope.update = function(response){
        $scope.currentID = response.data[0].id;
        $scope.currentImage = response.data[0].path;
        $scope.currentName = response.data[0].name;
        $scope.currentFilename = response.data[0].filename;
        $scope.currentTags = response.data[0].tags;
        $scope.currentRating = response.data[0].rating;
        $scope.availTags.length = 0;

        angular.forEach($scope.tags, function(value){
            if($scope.currentTags.indexOf(value) == -1 && value != "untagged"){
                $scope.availTags.push(value);
            }
        });

        $scope.showFilename = true;

    };

    $scope.removeCurrentTag = function(tag) {
        var index = $scope.currentTags.indexOf(tag);
        $scope.currentTags.splice(index, 1);
    };

    $scope.updateAvailTags = function(){
        //Makes sure 'untagged' is applied properly.

        $scope.availTags = [];
        angular.forEach($scope.tags, function(value){
            if($scope.currentTags.indexOf(value) == -1 && value != "untagged"){
                $scope.availTags.push(value);
            }
        });
        if ($scope.currentTags.length == 0) {
            $scope.currentTags.push("untagged");
        } else if ($scope.currentTags.indexOf("untagged") > -1) {
            $scope.removeCurrentTag("untagged");
        }

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

        $http.post("/file/" + $scope.currentID + "/tag/" + $scope.tagInput, {})
        .success(function (response) {
                $scope.tags.push($scope.tagInput);
               $scope.currentTags.push($scope.tagInput);
                $scope.tagInput = "";
                $scope.updateAvailTags();
            });
    };

    $scope.modifyTag = function(tag, action){
        if (tag == "untagged") {
            console.log("Someone tried to modify 'untagged', hehe");
            return false;
        }
        if(action=='add'){
            $http.post("/file/" + $scope.currentID + "/tag/" + tag, {})
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
        // This should be replaced by the angular ng-hide or ng-show with a
        // boolean variable, but doesn't want to work for some reason.
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

    $scope.rateFunction = function(rating) {

        $http.put("/file/" + $scope.currentID, {rating: rating})
            .error(function(data){
           alert("Not able to update file rating");
        });
    };

    $scope.updateFilename = function(){
      if ($scope.newName == undefined || $scope.newName == ""){
          $scope.showFilename = true;
          return false;
      }

        $http.put("/file/" + $scope.currentID, {name: $scope.newName})
            .success(function(data){
                $scope.currentName = $scope.newName;
                $scope.showFilename = true;
            })
            .error(function(data){
           alert("Not able to update filename");
        });

    };


    $scope.searchTag = function(tag){
        $scope.searchInput = tag;
        $scope.searchImages();
    };

    var $doc = angular.element(document);

    $doc.on('keydown', $scope.keyHandler);
    $scope.$on('$destroy',function(){
        $doc.off('keydown', $scope.keyHandler);
    });

    $scope.toggleImage("off");
    $scope.starts();
    $scope.allTags();

}]);
