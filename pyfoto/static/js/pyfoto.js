/**
 * Created by chris on 8/22/2015.
 */

function objIndexOf(myArray, searchTerm, property) {
    for(var i = 0, len = myArray.length; i < len; i++) {
        if (myArray[i][property] === searchTerm) return i;
    }
    return -1;
}


var pyfotoApp = angular.module('pyfotoApp', ['ngRoute']);

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

pyfotoApp.run(function($rootScope, $location) {
    /* polluting the root scope to a minimum. Could do directives, but that just adds overhead */
        $rootScope.searchRating = 0;

        $rootScope.performTagSearch = function() {
            $location.path('/search').search('tags', $rootScope.searchInput);
        };
        $rootScope.performRatingSearch = function(rating) {
            $location.path('/search').search('rating', rating);
        };
});


pyfotoApp.controller('searchController', ['$scope', '$http', '$routeParams',  function($scope, $http, $routeParams) {
    $scope.search_tags = $routeParams.tags;
    $scope.search_rating = $routeParams.ratings;

    console.log($scope.search_tags);
    console.log($scope.search_rating);

}]);


pyfotoApp.controller('indexController', ['$scope', '$http', '$interval',  function($scope, $http, $interval) {
    $scope.galleryImages = [];
    $scope.tags = [];
    $scope.availTags = [];
    $scope.untagged = {tag: "untagged", private: 0};

    $scope.currentImage = "";
    $scope.currentID = 1;
    $scope.currentName = "";
    $scope.currentFilename = "";
    $scope.currentTags = [];
    $scope.privateTags = [];
    $scope.currentFilters = "";
    $scope.currentRating = 0;
    $scope.searchRating = 0;

    $scope.showGallery = true;
    $scope.showFilename = true;
    $scope.scroller = null;
    $scope.scrolling = false;

    $scope.update = function(response){
        $scope.currentID = response.data[0].id;
        $scope.currentImage = response.data[0].path;
        $scope.currentName = response.data[0].name;
        $scope.currentFilename = response.data[0].filename;
        $scope.currentRating = response.data[0].rating;
        $scope.availTags.length = 0;
        $scope.currentTags.length = 0;
        $scope.privateTags.length = 0;

        angular.forEach(response.data[0].tags, function(item){
           if(item.private == false){
               $scope.currentTags.push(item);
           } else {
               $scope.privateTags.push(item);
           }
        });

        angular.forEach($scope.tags, function(item){
            if(objIndexOf($scope.currentTags, item.tag, "tag") == -1 &&
                objIndexOf($scope.privateTags, item.tag, "tag") == -1 &&
                item.tag != "untagged"){
                $scope.availTags.push(item);
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
            if($scope.currentTags.indexOf(value) == -1 && value.tag != "untagged"){
                $scope.availTags.push(value);
            }
        });
        /*if ($scope.currentTags.length == 0) {
            $scope.currentTags.push($scope.untagged);
        } else if ($scope.currentTags.indexOf($scope.untagged) > -1) {
            $scope.removeCurrentTag($scope.untagged);
        }*/

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
        if ($scope.currentFilters != "" && $scope.currentFilters != undefined && $scope.currentFilters != "star rating"){
            url += "&search=" + $scope.currentFilters;
        } else if ($scope.currentFilters == "star rating"){
            url += "&searchType=rating" + "&search=" +$scope.searchRating;
        }
        $http.get(url)
            .success(function (response) {
                if (response.data.length == 0){
                    $scope.scrollOff();
                }
                else {
                    $scope.update(response);
                }
            })
    };

    $scope.prevItem = function(){
        var url = "/prev/" + $scope.currentID + "?count=1";
            if ($scope.currentFilters != ""  && $scope.currentFilters != undefined && $scope.currentFilters != "star rating"){
                url += "&search="+$scope.currentFilters;
        } else if ($scope.currentFilters == "star rating"){
            url += "&searchType=rating" + "&search=" +$scope.searchRating;
        }

        $http.get(url)
            .success(function (response) {
                if (response.data.length == 0){
                    return false;
                } else {
                    $scope.update(response);
                    return true;
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
                var newtag = {tag: $scope.tagInput, private: 0};
                $scope.tags.push(newtag);
                $scope.currentTags.push(newtag);
                $scope.tagInput = "";
                $scope.updateAvailTags();
            });
    };

    $scope.modifyTag = function(tag, action){
        if (tag.tag == "untagged") {
            console.log("Someone tried to modify 'untagged', hehe");
            return false;
        }
        if(action=='add'){
            $http.post("/file/" + $scope.currentID + "/tag/" + tag.tag, {})
            .success(function (response) {
                   $scope.currentTags.push(tag);
                    $scope.updateAvailTags();
                });
        } else if (action == 'remove') {
            $http.delete("/file/" + $scope.currentID + "/tag/" + tag.tag)
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
        $scope.tags.push($scope.untagged);
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
            $scope.scrollOff();
        } else {
            $(".main-image").show();
            $(".image-data").show();
            $(".gallery").hide();
            $(".back-to-search").show();
            $(".search-data").hide();
        }
    };


    $scope.searchImages = function(){
        $scope.searchRating = 0;
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

    $scope.searchRate = function(rating) {

        $http.get("/search?search=" + rating + "&search_type=rating")
            .success(function (response) {
                $scope.toggleImage("off");
                $scope.galleryImages = response.data;
                $scope.currentFilters = "star rating";
                $scope.searchInput = "";
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
        $scope.searchInput = tag.tag;
        $scope.searchImages();
    };



    $scope.scrollOn = function(){
        $scope.scroller = $interval(function(){
            $scope.nextItem();
        }, 1500);

    };

    $scope.scrollOff = function(){
        $interval.cancel($scope.scroller);
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


pyfotoApp.config(['$routeProvider', function ($routeProvider) {
    $routeProvider
        .when('/', {
            redirectTo: '/search'
        })
        .when('/search', {
            templateUrl: '/template/search.html',
            controller: 'searchController'
        })
        .when('/image/:imageId', {
            templateUrl: '/template/image.html',
            controller: 'indexController'
        })
}]);