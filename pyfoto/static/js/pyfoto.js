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
        currentFilters: {},
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

    $rootScope.highlightTag = function(tag, remove){
        //var item = $.grep($scope.globals.tags, function(e){ return e.tag === tag});
        var remove_tag = remove || false;
        angular.forEach($rootScope.globals.tags, function(item) {
            if (item.tag == tag) {
                item.highlight = !remove_tag;
            }
        });
    };

    $rootScope.unhighlightAll = function(){
        angular.forEach($rootScope.globals.tags, function(item) {
            item.highlight = false;
        });
    };

    // This is here because we should only have to get all tags once, hopefully, kinda
    $http.get("/tag")
        .success(function (response) {
            angular.forEach(response.data, function(value){
                $rootScope.pushUniqueTag(value);
            });
        });

    $rootScope.pushUniqueTag({tag: "untagged", private: 0});

    // Ok, so, this is all kinda silly right now, but this is so it can be exampled for advnced searches later

    $rootScope.getFilters = function(){
       var url = "&";
        if (angular.equals({}, $rootScope.globals.currentFilters)){
            return url;
        } else if ("tags" in $rootScope.globals.currentFilters){
            url += "search="+ $rootScope.globals.currentFilters["tags"] + "&searchType=tag";
        } else if ("string" in $rootScope.globals.currentFilters){
            url += "search="+ $rootScope.globals.currentFilters["string"]  + "&searchType=string";
        } else if ("rating" in $rootScope.globals.currentFilters){
            url += "search="+ $rootScope.globals.currentFilters["rating"] + "&searchType=rating";
        }
        return url;
    };

    $rootScope.paramFilters = function(){
        if (angular.equals({}, $rootScope.globals.currentFilters)){
            return {};
        } else if ("tags" in $rootScope.globals.currentFilters){
            return {search: $rootScope.globals.currentFilters["tags"], searchType: "tag"};
        } else if ("string" in $rootScope.globals.currentFilters){
            return {search: $rootScope.globals.currentFilters["string"], searchType: "string"};
        } else if ("rating" in $rootScope.globals.currentFilters){
            return {search: $rootScope.globals.currentFilters["rating"], searchType: "rating" };
        }
        return {};
    };

    $rootScope.setFilters = function(params){
        if ("search" in params){
            if (! ("search_type" in params)){
                $rootScope.globals.currentFilters["tags"] = params.search;
            } else {
                $rootScope.globals.currentFilters[params.search_type] = params.search;
            }
        }
        console.log($rootScope.globals.currentFilters);
    };


});

pyfotoApp.controller('searchController', ['$scope', '$http', '$routeParams', '$rootScope', '$location', function($scope, $http, $routeParams, $rootScope, $location) {
        $scope.globals = $rootScope.globals;

        $scope.performSearch = function(term) {
            $location.url('/search').search('search', term);
        };

}]);

pyfotoApp.controller('galleryController', ['$scope', '$http', '$routeParams', '$rootScope', '$location',  function($scope, $http, $routeParams, $rootScope, $location) {
    $rootScope.setFilters($routeParams);
    $scope.get_filters = $rootScope.getFilters();
    $scope.globals = $rootScope.globals;

    $scope.searchRating = 0;

    if ("rating" in $scope.globals.currentFilters){
        $scope.searchRating = $scope.globals.currentFilters.rating;
    }

    $scope.galleryImages = [];

    $rootScope.unhighlightAll();

    if(! ("string" in $scope.globals.currentFilters) &&
        ! ("rating" in $scope.globals.currentFilters) &&
        ! ("tags" in $scope.globals.currentFilters)){
            $http.get("/file")
              .success(function (response) {
                    $scope.galleryImages = response.data;
                    $scope.globals.currentFilters = {};
                });

    } else if ("string" in $scope.globals.currentFilters) {

        $http.get("/search?search=" + $scope.globals.currentFilters.string)
            .success(function (response) {
                $scope.galleryImages = response.data;
            });
    } else if ("rating" in $scope.globals.currentFilters) {
        $http.get("/search?search=" + $scope.globals.currentFilters.rating + "&search_type=rating")
            .success(function (response) {
                $scope.galleryImages = response.data;
            });
    } else if ("tags" in $scope.globals.currentFilters) {
        $http.get("/search?search=" + $scope.globals.currentFilters.tags)
            .success(function (response) {
                $scope.galleryImages = response.data;
                // TODO add code to highlight tags
            });
    } else {
        alert("Should not be here, how'd you do that?");
    }

    $scope.performRatingSearch = function(rating) {
        $rootScope.globals.currentFilters = {};
        $location.url('/search').search({search: rating, search_type: "rating"});
    };

    $scope.nextPage = function(){
        var highest = Math.max.apply(Math,$scope.galleryImages.map(function(o){return o.id;}));
        var url = "/next/" + highest + "?count=100";
        url += $rootScope.get_filters;

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

}]);


pyfotoApp.controller('indexController', ['$scope', '$http', '$routeParams', '$rootScope', '$location',  '$interval', function($scope, $http, $routeParams, $rootScope, $location, $interval) {
    $rootScope.setFilters($routeParams);
    $scope.get_filters = $rootScope.getFilters();
    $scope.globals = $rootScope.globals;

    $scope.image_id = $routeParams.imageId;

    $scope.my_tags = [];
    $scope.showFilename = true;
    $scope.scroller = null;
    $scope.scrolling = $routeParams.scrolling || false;
    $scope.rating = 0;


    $scope.update = function(response){
        $scope.image_info = response.data[0];
        $scope.rating = $scope.image_info.rating;

        angular.forEach(response.data[0].tags, function(item){
           $scope.my_tags.push(item.tag);
            if(item.private == false){
               $scope.highlightTag(item.tag);
           }
        });

        $(".main-image").css('background-image', 'url(/item/' + $scope.image_info.path + ')');

        $scope.showFilename = true;

        if ($scope.scrolling){
        $scope.scroller = $interval(function(){
            $scope.nextItem();
        }, 2500, 1);

        }

    };

    $scope.deleteImage = function(){
          $http.delete("/file/" + $scope.image_id)
              .success(function (response) {
                    //TODO if there is no next item, go to previous.
                    $scope.nextItem();
                });

    };

    $scope.nextItem = function(){
        var url = "/next/" + $scope.image_id + "?count=1";
        url += $rootScope.getFilters();
        console.log(url);

        $http.get(url)
            .success(function (response) {
                if (response.data.length == 0){
                    $scope.scrollOff();
                }
                else {
                    $location.url("/image/"+ response.data[0].id).search($rootScope.paramFilters()).search({"scrolling": $scope.scrolling});
                }
            })
    };

    $scope.prevItem = function(){
        var url = "/prev/" + $scope.image_id + "?count=1";
        url += $rootScope.getFilters();

        $http.get(url)
            .success(function (response) {
                if (response.data.length == 0){
                    $scope.scrollOff();
                } else {
                    $location.url("/image/"+ response.data[0].id).search($rootScope.paramFilters());
                }
            })
    };

    $scope.addTagToFile = function(){
        if ($scope.tagInput == "" || $scope.tagInput == undefined){
            alert("You're an idiot");
            return false;
        }

        $http.post("/file/" + $scope.image_id + "/tag/" + $scope.tagInput, {})
        .success(function (response) {
                var newtag = {tag: $scope.tagInput, private: 0, highlight: true};
                $scope.global.tags.push(newtag);
                $scope.tagInput = "";
            });
    };

    $scope.modifyTag = function(tag, action){
        if (tag.tag == "untagged") {
            console.log("Someone tried to modify 'untagged', hehe");
            return false;
        }

        if($scope.my_tags.indexOf(tag.tag) >= 0){
            console.log("removing");
            $http.delete("/file/" + $scope.image_id + "/tag/" + tag.tag)
                .success(function (response) {
                   $rootScope.highlightTag(tag.tag, true);
                   $scope.my_tags.splice($scope.my_tags.indexOf(tag.tag),1);
                });
        } else {
            console.log("adding");
            $http.post("/file/" + $scope.image_id + "/tag/" + tag.tag, {})
                .success(function (response) {
                    $rootScope.highlightTag(tag.tag);
                    $scope.my_tags.push(tag.tag);
                });
        }

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



    $scope.rateFunction = function(rating) {

        $http.put("/file/" + $scope.image_id, {rating: rating})
            .error(function(data){
           alert("Not able to update file rating");
        });
    };


    $scope.updateFilename = function(){
      if ($scope.newName == undefined || $scope.newName == ""){
          $scope.showFilename = true;
          return false;
      }

        $http.put("/file/" + $scope.image_id, {name: $scope.newName})
            .success(function(data){
                $scope.image_info.name = $scope.newName;
                $scope.showFilename = true;
            })
            .error(function(data){
           alert("Not able to update filename");
        });

    };

    $scope.scrollOn = function(){
        $scope.scrolling = true;
        $scope.scroller = $interval(function(){
            $scope.nextItem();
        }, 2500, 1);

    };

    $scope.scrollOff = function(){
        $scope.scrolling = false;
        $interval.cancel($scope.scroller);
    };

    var $doc = angular.element(document);

    $doc.on('keydown', $scope.keyHandler);
    $scope.$on('$destroy',function(){
        $doc.off('keydown', $scope.keyHandler);
    });

    $rootScope.unhighlightAll();
    $scope.openImage($scope.image_id);

    $scope.$on('$destroy', function iVeBeenDismissed() {
        $scope.scrollOff();
    })

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