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


# Handling Code
In parsing functions (i.e. within akf_parsing_functions_one), 
you can log can log segment specific info to file:

`
self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)
`

## Parsing code 
To use your custom parsing code instantiate your 'segment_parser.py'
FunctionMapAKF constructor. Make sure your function tag is the one
used in the segment_classifier. For the keys in 'function_map' use 
the keyss noted in your segment holder (i.e. 'akf_segment_holder')

```python
    self.akf_one = AkfParsingFunctionsOne(endobject_factory, output_analyzer)
    self.akf_two = AkfParsingFunctionsTwo(endobject_factory, output_analyzer)
    
    # for the keys use the keys from 'akf_segment_holder' or similar

    self.function_map = {
        "Sitz": self.akf_one.parse_sitz,
        "Verwaltung": self.akf_one.parse_verwaltung,
        "Telefon/Fernruf": self.akf_one.parse_telefon_fernruf,
        "Vorstand": self.akf_one.parse_vorstand,
        "Aufsichtsrat": self.akf_one.parse_aufsichtsrat,
        "Gründung": self.akf_one.parse_gruendung,
        "Arbeitnehmervertreter": self.akf_one.parse_arbeitnehmervertreter,
        "Tätigkeitsgebiet": self.akf_one.parse_taetigkeitsgebiet,
        "Zahlstellen": self.akf_two.parse_zahlstellen,
    }
```