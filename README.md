# akf-hocrparser
Parsing .hocr-output of ocromore to get a content-classified .json output for further database export.


# Installation 

To initialize the git submodules (~git version 2.7.4):

`
git submodule update --init --recursive
`



For development Pycharm IDE 2017.3 Community Edition was used 


If using the Pycharm IDE to look at accumulated segmentation analysis files adapt the IDE settings to have proper view.
This is in idea.properties-file which can i.e. be found over Help->Edit Custom Properties in Pycharm:


`
editor.soft.wrap.force.limit=10000
`