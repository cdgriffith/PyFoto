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
        if (objIndexOf(my_array, tag.tag, "tag") == -1) {
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

    $rootScope.pushUniqueTag({tag: "untagged", private: 0, highlight: false});

    // Ok, so, this is all kinda silly right now, but this is so it can be exampled for advnced searches later

    $rootScope.getFilters = function(){
       var url = "&";
        if (angular.equals({}, $rootScope.globals.currentFilters)) {
            return url;
        }
        else if ("rating" in $rootScope.globals.currentFilters){
            url += "search="+ $rootScope.globals.currentFilters["rating"] + "&search_type=rating";
        } else if ("tags" in $rootScope.globals.currentFilters){
            url += "search="+ $rootScope.globals.currentFilters.tags.join() + "&search_type=tag";
        } else if ("string" in $rootScope.globals.currentFilters){
            url += "search="+ $rootScope.globals.currentFilters["string"]  + "&search_type=string";
        }
        return url;
    };

    $rootScope.paramFilters = function(){
        if (angular.equals({}, $rootScope.globals.currentFilters)){
            return {};
        } else if ("rating" in $rootScope.globals.currentFilters){
            return {search: $rootScope.globals.currentFilters["rating"], search_type: "rating" };
        } else if ("tags" in $rootScope.globals.currentFilters){
            return {search: $rootScope.globals.currentFilters["tags"], search_type: "tag"};
        } else if ("string" in $rootScope.globals.currentFilters){
            return {search: $rootScope.globals.currentFilters["string"], search_type: "string"};
        }
        return {};
    };

    $rootScope.setFilters = function(parameters){
        if ("search" in parameters){
            if (! ("search_type" in parameters)){
                $rootScope.globals.currentFilters.tags = parameters.search.split(",");
            } else {
                if (parameters.search_type == "tags"){
                    $rootScope.globals.currentFilters.tags = parameters.search.split(",");
                    if ($rootScope.globals.currentFilters.tags.indexOf("") >= 0){
                        $rootScope.globals.currentFilters.tags.splice($rootScope.globals.currentFilters.tags.indexOf(""), 1);
                        if ($rootScope.globals.currentFilters.tags.length == 0){
                            $rootScope.globals.currentFilters = {};
                        }
                    }
                } else {
                    $rootScope.globals.currentFilters[parameters.search_type] = parameters.search;
                }
            }
        } else {
            $rootScope.globals.currentFilters = {};
        }
    };

    $rootScope.performSearch = function(term) {
            $rootScope.searchInput = "";
            $location.url('/search').search('search', term);
        };


});

pyfotoApp.controller('loginController', ['$scope', '$http', '$routeParams', '$rootScope', '$location',  function($scope, $http, $routeParams, $rootScope, $location) {
    $rootScope.hideHeader = true;

    $scope.login = function(username, password){
        $http.post("/auth/login", {username: username, password: password})
        .success(function (response){
            console.log(response);
            $rootScope.token = response.token;
            $location.url('/search');
        }).error(function (response){
        });
    };
}]);

pyfotoApp.controller('galleryController', ['$scope', '$http', '$routeParams', '$rootScope', '$location',  function($scope, $http, $routeParams, $rootScope, $location) {
    $rootScope.setFilters($routeParams);
    $rootScope.hideHeader = false;
    $scope.get_filters = $rootScope.getFilters();
    $scope.param_filters = $rootScope.paramFilters();
    $scope.globals = $rootScope.globals;
    $scope.current_page = "search";
    $scope.image_id = 0;
    $scope.loadMoreHidden = false;
    $scope.loadPrevHidden = true;
    $scope.totalItems = 0;
    $scope.searchRating = 0;
    $http.defaults.headers.common.auth = $rootScope.token;
    console.log($rootScope.token);

    $http.get("/tag")
        .success(function (response) {
            if (response.error == true){
                if(response.message == 'Access Denied'){
                    window.location = '/template/forbidden.html';
                }
            }
            angular.forEach(response.data, function (value) {
                $rootScope.pushUniqueTag(value);
            });
        });

    if ("rating" in $scope.globals.currentFilters){
        $scope.searchRating = $scope.globals.currentFilters.rating;
    }

    $scope.galleryImages = [];

    $rootScope.unhighlightAll();

    $scope.start_at = 0;
    if ($routeParams.start_at >= 0 && $routeParams.start_at != 'undefined'){
        $scope.start_at = $routeParams.start_at;
    }

    $scope.start_at_string =  "start_at=" + $scope.start_at;

    $scope.checkLoad = function(response){
        if (! response.expected){
            $scope.loadMoreHidden = true;
        } else {
            $scope.loadMoreHidden = false;
        }
    };

    if(! ("string" in $scope.globals.currentFilters) &&
        ! ("rating" in $scope.globals.currentFilters) &&
        ! ("tags" in $scope.globals.currentFilters)){
            $http.get("/file?" + $scope.start_at_string)
              .success(function (response) {
                    $scope.galleryImages = response.data;
                    $scope.globals.currentFilters = {};
                    $scope.checkLoad(response);
                    $scope.totalItems = response.total;
                });

    } else if ("string" in $scope.globals.currentFilters) {

        $http.get("/search?search=" + $scope.globals.currentFilters.string + "&" + $scope.start_at_string)
            .success(function (response) {
                $scope.galleryImages = response.data;
                $scope.checkLoad(response);
                $scope.totalItems = response.total;
            });
    } else if ("rating" in $scope.globals.currentFilters) {
        $http.get("/search?search=" + $scope.globals.currentFilters.rating + "&" + $scope.start_at_string + "&search_type=rating")
            .success(function (response) {
                $scope.galleryImages = response.data;
                $scope.checkLoad(response);
                $scope.totalItems = response.total;
            });
    } else if ("tags" in $scope.globals.currentFilters) {
        $http.get("/search?search=" + $scope.globals.currentFilters.tags.join() + "&" + $scope.start_at_string)
            .success(function (response) {
                $scope.galleryImages = response.data;
                $scope.totalItems = response.total;
                $scope.checkLoad(response);
                angular.forEach($scope.globals.currentFilters.tags, function(tag_name){
                    $rootScope.highlightTag(tag_name);
                });
            });
    } else {
        alert("Should not be here, how'd you do that?");
    }

    $scope.toggleSearchTag = function(tag){

        if ("tags" in $scope.globals.currentFilters){
            if (tag.tag == "untagged") {
                $scope.globals.currentFilters.tags.length = 0;
                $scope.globals.currentFilters.tags.push(tag.tag);
            }
            else {
                var pos = $scope.globals.currentFilters.tags.indexOf(tag.tag);
                if (pos >= 0){
                    $scope.globals.currentFilters.tags.splice(pos, 1);
                    if ($scope.globals.currentFilters.tags.length == 0){
                        $location.url($location.path());
                        return true;
                    }
                } else {
                    var untagged_pos = $scope.globals.currentFilters.tags.indexOf("untagged");
                    if (untagged_pos >=0){
                        $scope.globals.currentFilters.tags.splice(untagged_pos, 1);
                    }
                    $scope.globals.currentFilters.tags.push(tag.tag);
                }
            }

            $location.url('/search').search({search: $scope.globals.currentFilters.tags.join(), search_type: "tags"});
        } else {
            $location.url('/search').search({search: tag.tag, search_type: "tags"});
        }

    };

    $scope.performRatingSearch = function(rating) {
        $rootScope.globals.currentFilters = {};
        $location.url('/search').search({search: rating, search_type: "rating"});
    };

    $scope.nextPage = function(){
        var highest = Math.max.apply(Math,$scope.galleryImages.map(function(o){return o.id;}));
        var url = "/next/" + highest + "?count=100";
        url += $scope.get_filters;

        $http.get(url)
            .success(function (response) {
                if (response.data.length == 0){
                    $scope.loadMoreHidden = true;
                    return false;
                }
                else {
                    angular.forEach(response.data, function(value){
                        $scope.galleryImages.push(value);
                        if ($scope.galleryImages.length >= 1000){
                            $scope.galleryImages.splice(0,1);
                            $scope.loadPrevHidden = false;
                        }
                    });
                    $scope.totalItems = response.total;
                    $scope.checkLoad(response);
                }
            })
    };

    $scope.prevPage = function(){
        var lowest = Math.min.apply(Math,$scope.galleryImages.map(function(o){return o.id;}));
        var url = "/prev/" + lowest + "?count=100";
        url += $scope.get_filters;

        $http.get(url)
            .success(function (response) {
                if (response.data.length == 0){
                    $scope.loadPrevHidden = true;
                    return false;
                }
                else {
                    angular.forEach(response.data, function(value){
                        $scope.galleryImages.splice(0,0,value);
                        if ($scope.galleryImages.length >= 1000){
                            $scope.galleryImages.splice(999,1);
                            $scope.loadMoreHidden = false;
                        }
                    });
                    $scope.totalItems = response.total;
                   if (! response.expected){
                        $scope.loadPrevHidden = true;
                   } else {
                        $scope.loadPrevHidden = false;
                   }
                }
            })
    };

}]);


pyfotoApp.controller('indexController', ['$scope', '$http', '$routeParams', '$rootScope', '$location',  '$interval', function($scope, $http, $routeParams, $rootScope, $location, $interval) {
    $rootScope.setFilters($routeParams);
    $scope.get_filters = $rootScope.getFilters();
    $scope.param_filters = $rootScope.paramFilters();
    $scope.globals = $rootScope.globals;
    $scope.current_page = "image";
    $rootScope.hideHeader = false;
    console.log($rootScope.token);
    $http.defaults.headers.common.auth = $rootScope.token;

    $scope.image_id = $routeParams.imageId;

    $scope.my_tags = [];
    $scope.showFilename = true;
    $scope.scroller = null;
    $scope.scrolling = ($routeParams.scrolling == 'true');
    $scope.rating = 0;

    $scope.update = function(response){
        $scope.image_info = response.data[0];
        $scope.rating = $scope.image_info.rating;

        angular.forEach(response.data[0].tags, function(item){
           $scope.my_tags.push(item.tag);
            if(item.private == false){
               $rootScope.highlightTag(item.tag);
           }
        });

        if ($scope.my_tags.length == 0){
            $rootScope.highlightTag("untagged");
        }

        $(".main-image").css('background-image', 'url(/item/' + $scope.image_info.path + ')');

        $scope.showFilename = true;

        if ($scope.scrolling == true){
            $scope.scroller = $interval(function(){
                $scope.nextItem();
            }, 2500, 1);
        }
    };

    $scope.deleteImage = function(){
        $http.delete("/file/" + $scope.image_id)
              .success(function (response) {
                    $scope.nextItem(true);
                });

    };

    $scope.nextItem = function(fallBack){
        var url = "/next/" + $scope.image_id + "?count=1";
        url += $scope.get_filters;
        if (fallBack === undefined){
            fallBack = false;
        }

        $http.get(url)
            .success(function (response) {
                if (response.data.length == 0){
                    $scope.scrollOff();
                    if (fallBack){
                        $scope.prevItem();
                    }
                }
                else {
                    var filters = $scope.get_filters;
                    if ($scope.scrolling){
                        filters += "&scrolling=true";
                    } else {
                        filters += "&scrolling=false";
                    }
                    $location.url("/image/"+ response.data[0].id).search(filters);
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
                    $location.url("/image/"+ response.data[0].id).search($scope.get_filters);
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
                // TODO this should work and doesn't, workaround below
                //var newtag = {tag: $scope.tagInput, private: 0, highlight: true};
                //$scope.global.tags.push(newtag);

                location.reload();

            });
    };

    $scope.modifyTag = function(tag, action){
        if (tag.tag == "untagged") {
            console.log("Someone tried to modify 'untagged', hehe");
            return false;
        }

        if($scope.my_tags.indexOf(tag.tag) >= 0){
            $http.delete("/file/" + $scope.image_id + "/tag/" + tag.tag)
                .success(function (response) {
                   $rootScope.highlightTag(tag.tag, true);
                   $scope.my_tags.splice($scope.my_tags.indexOf(tag.tag),1);
                   if ($scope.my_tags.length == 0){
                       $rootScope.highlightTag("untagged");
                   }

                });
        } else {
            $http.post("/file/" + $scope.image_id + "/tag/" + tag.tag, {})
                .success(function (response) {
                    $rootScope.highlightTag(tag.tag);
                    $rootScope.highlightTag("untagged", true); // could check to see if it's already unchecked, but
                    // I'm lazy and this works fine
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
    });

    $scope.zoomIn = function(){
        $('.alt-view').removeClass('hidden');
        $('.main-view').addClass('hidden');

    };

    $scope.zoomOut = function(){
        $('.alt-view').addClass('hidden');
        $('.main-view').removeClass('hidden');
    };

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
        .when('/login', {
            templateUrl: '/template/login.html',
            controller: 'loginController'
        })
}]);