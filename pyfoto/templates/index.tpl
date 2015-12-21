<!DOCTYPE html>
<html lang="en" ng-app="pyfotoApp">
<head>
    <meta charset="UTF-8">
    <link rel="stylesheet" href="/static/css/bootstrap.css">
    <link rel="stylesheet" href="/static/css/bootstrap-theme.css">
    <link rel="stylesheet" href="/static/css/pyfoto.css">
</head>
<body>

    <div class="main-area" ng-controller="indexController">

        <div class="col-md-10 left-side" style="height: 100%">

            <div class="gallery">
                <div class="gallery-image" ng-repeat="image in galleryImages"
                     ng-style="{'background-image': 'url(/item/' + image.thumbnail + ')'}"
                        ng-click="openImage(image.id)"></div>
                <div class="more-footer col-md-12" ng-click="nextPage()">Load
                    More</div>
            </div>

            <div class="main-image"
                 ng-style="{'background-image': 'url(/item/' + currentImage + ')'}">

                <div class="col-md-1 left-image" ng-click="prevItem()">
                    <span class="glyphicon glyphicon-menu-left" aria-hidden="true"></span>
                </div>

                <div class="col-md-1 pull-right right-image" ng-click="nextItem()">
                    <span class="glyphicon glyphicon-menu-right" aria-hidden="true"></span>
                </div>
            </div>

        </div>

        <div class="col-lg-2 col-sm-2 col-md-2 right-side">


            <div class="search-area">
                <div class="back-to-search"
                      ng-click="toggleImage('off')">
                    <span class="glyphicon glyphicon-triangle-left" aria-hidden="true"></span> Back to Search
                </div>

                    <form ng-submit="searchImages()" class="form-inline">
                         <div class="form-group">
                            <label class="sr-only" for="searchInput">search</label>
                            <input id="searchInput" ng-model="searchInput" type="text"
                                   placeholder="Search" />
                         </div>
                        <input type="submit" style="position: absolute; left: -9999px; width: 1px; height: 1px;"/>
                    </form>

                <div class="star-rating" star-rating rating-value="searchRating"
                     data-max="5"on-rating-selected="searchRate(rating)"></div>

                <div class="current-search" ng-hide="currentFilters == undefined || currentFilters == '' ">
                    <span class="glyphicon glyphicon-remove-circle" style="cursor: pointer; color:red"
                          ng-click="searchTag('')"></span> Current Search:
                    {{currentFilters}}
                </div>

            </div>

            <div class="search-data" >
                <div class="tag-cloud">
                    <h4 class="header">Search Tags</h4>
                    <span ng-repeat="tag in tags" class="tag" ng-click="searchTag(tag)">{{tag}}</span>
                </div>
            </div>


            <div class="image-data" >


                <div class="image-details">

                    <div class="star-rating" star-rating rating-value="currentRating"
                     data-max="5"on-rating-selected="rateFunction(rating)"></div>

                    <div class="filename">
                        <div class="show-filename" ng-click="showFilename = ! showFilename"
                               ng-show="showFilename" >{{currentName}}</div>
                        <form style="color:black;" ng-show="! showFilename"
                              class="form-inline">
                            <div class="form-group">
                                <label class="sr-only" for="changeFilename">Filename</label>
                                <input   id="changeFilename" type="text" ng-model="newName" name="filename" placeholder="{{currentName}}"  />
                            </div>
                            <button ng-click="updateFilename()" class="btn btn-primary">Save</button>
                            <button ng-click="showFilename = ! showFilename" class="btn btn-danger">Cancel</button>
                        </form>
                    </div>


                    <a href="/item/{{currentImage}}" download="{{currentFilename}}" >Download</a> |
                    <a href="#" style="color: red;" ng-click="deleteImage()">Delete</a>&nbsp;&nbsp;&nbsp;
                </div>

                <div class="tag-cloud">
                    <h4 class="header">Tags</h4>
                    <span ng-repeat="tag in currentTags" class="tag" ng-bind="tag"
                          ng-click="modifyTag(tag, 'remove')"></span>
                </div>
                <div class="tag-cloud">
                    <h5 class="header">Available</h5>
                    <span ng-repeat="tag in availTags" class="tag" ng-bind="tag"
                          ng-click="modifyTag(tag, 'add')"></span>
                </div>

                <div class="add-tag">
                    <form ng-submit="addTagToFile()" class="form-inline">
                         <div class="form-group">
                            <label class="sr-only" for="tagInput">Name</label>
                            <input id="tagInput" ng-model="tagInput" type="text" placeholder="New Tag" />
                         </div>
                        <input type="submit" style="position: absolute; left: -9999px; width: 1px; height: 1px;"/>
                    </form>
                </div>
            </div>

        </div>

    </div>

        <script src="/static/js/jquery-2.1.4.js"></script>
        <script src="/static/js/angular.js"></script>
        <script src="/static/js/bootstrap.js"></script>
        <script src="/static/js/pyfoto.js"></script>


</body>
</html>