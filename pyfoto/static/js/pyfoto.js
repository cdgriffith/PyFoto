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

pyfotoApp.run(function($rootScope, $location, $http) {
    /* polluting the root scope to a minimum. */
    $rootScope.globals = {
        tags: [],
        currentFilters: null,
        searchRating: 0
        };

    $rootScope.pushUniqueTag = function(tag, my_array){
        if (my_array == undefined){
            my_array = $rootScope.globals.tags;
        }
        if (objIndexOf(my_array, "tag", tag.tag) == -1) {
            if (! "highlight" in tag){
                tag.highlight = false;
            }
            my_array.push(tag);
        }
    };

    // This is here because we should only have to get all tags once, hopefully, kinda
    $http.get("/tag")
        .success(function (response) {
            angular.forEach(response.data, function(value){
                $rootScope.pushUniqueTag(value);
            });
        });

    $rootScope.pushUniqueTag({tag: "untagged", private: 0});

});

pyfotoApp.controller('searchController', ['$scope', '$http', '$routeParams', '$rootScope', '$location', function($scope, $http, $routeParams, $rootScope, $location) {
        $scope.globals = $rootScope.globals;

        $scope.performSearch = function(term) {
            $location.url('/search').search('search', term);
        };

}]);

pyfotoApp.controller('galleryController', ['$scope', '$http', '$routeParams', '$rootScope', '$location',  function($scope, $http, $routeParams, $rootScope, $location) {
    $scope.search_tags = $routeParams.tags;
    $scope.search_rating = $routeParams.rating;
    $scope.search_string = $routeParams.search;
    $scope.globals = $rootScope.globals;

    $scope.searchRating = $scope.search_rating || 0;
    $scope.galleryImages = [];


    if($scope.search_tags == undefined && $scope.search_rating == undefined && $scope.search_string == undefined){
            $http.get("/file")
              .success(function (response) {
                    $scope.galleryImages = response.data;
                    $scope.globals.currentFilters = null;
                });

    } else if ($scope.search_string != undefined) {

        $http.get("/search?search=" + $scope.search_string)
            .success(function (response) {
                $scope.galleryImages = response.data;
                $scope.currentFilters = {string: $scope.search_string};
            });
    } else if ($scope.search_rating != undefined) {
        $http.get("/search?search=" + $scope.search_rating + "&search_type=rating")
            .success(function (response) {
                $scope.galleryImages = response.data;
                $scope.currentFilters = {rating: $scope.search_rating};
            });
    } else if ($scope.search_tags != undefined) {
        $http.get("/search?search=" + $scope.search_tags)
            .success(function (response) {
                $scope.galleryImages = response.data;
                $scope.currentFilters = {tags: $scope.search_tags};
            });
    } else {
        alert("Should not be here, how'd you do that?");
    }

    $scope.performRatingSearch = function(rating) {
        $location.url('/search').search('rating', rating);
    };

}]);


pyfotoApp.controller('indexController', ['$scope', '$http', '$routeParams', '$rootScope', '$location',  function($scope, $http, $routeParams, $rootScope, $location) {
    $scope.image_id = $routeParams.imageId;

    $scope.globals = $rootScope.globals;

    /*$scope.availTags = [];
    $scope.untagged = {tag: "untagged", private: 0};
    $scope.currentImage = "";
    $scope.currentID = 1;
    $scope.currentName = "";
    $scope.currentFilename = "";
    $scope.currentTags = [];
    $scope.privateTags = [];
    $scope.currentFilters = "";
    $scope.currentRating = 0;
    $scope.searchRating = 0;*/

    $scope.showFilename = true;
    $scope.scroller = null;
    $scope.scrolling = false;

    $scope.highlightTag = function(tag){
        //var item = $.grep($scope.globals.tags, function(e){ return e.tag === tag});
        angular.forEach($scope.globals.tags, function(item) {
            if (item.tag == tag) {
                item.highlight = true;
            }
        });
    };

    $scope.unhighlightTag = function(tag){
        angular.forEach($scope.globals.tags, function(item) {
            if (item.tag == tag) {
                item.highlight = false;
            }
        });
    };

    $scope.unhighlightAll = function(){
        angular.forEach($scope.globals.tags, function(item) {
            item.highlight = false;
        });
    };

    $scope.update = function(response){
        $scope.image_info = response.data[0];
        //$scope.currentID = response.data[0].id;
        //$scope.currentImage = response.data[0].path;
        //$scope.currentName = response.data[0].name;
        //$scope.currentFilename = response.data[0].filename;
        //$scope.currentRating = response.data[0].rating;
        //$scope.availTags.length = 0;
        //$scope.currentTags.length = 0;
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



    $scope.openImage = function(file_id){
        $http.get("/file/" + file_id)
            .success(function (response) {
                if (response.data == undefined || response.data.length == 0){
                    alert("Cannot open file");

                } else {
                    $scope.update(response);
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
            templateUrl: '/template/gallery.html',
            controller: 'galleryController'
        })
        .when('/image/:imageId', {
            templateUrl: '/template/image.html',
            controller: 'indexController'
        })
}]);