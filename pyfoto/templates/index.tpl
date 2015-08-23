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
        <div class="col-lg-1 col-sm-2 col-md-1" style="height:100%; overflow-y: auto">
            <div class="list-group-item" ng-repeat="folder in folderList" ng-bind="folder.path" ng-click="getItems(folder.path)">

            </div>
        </div>
        <div class="col-lg-11 col-sm-10 col-md-11">
            <div class="main-image"><img ng-src="{{'{{currentImage}}'}}" style="max-width:100%; max-height: 100%" /></div>
        </div>



    </div>



        <script src="/static/js/jquery-2.1.1.min.js"></script>
        <script src="/static/js/angular.min.js"></script>
        <script src="/static/js/bootstrap.js"></script>
        <script src="/static/js/pyfoto.js"></script>
</body>
</html>