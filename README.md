![docxstruct](docs/img/docxstruct_logo.png "docxstruct")
============
![license](https://img.shields.io/badge/license-Apache%20License%202.0-blue.svg)

Docxstruct parses .hocr-output of [ocromore][ocromore-link] to get a content-classified .json output 
for further database export. It is part of the [Aktienführer-Datenarchiv work process][akf-link],
but can also be used independently.

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
`Docxstruct` is made to be adapted for parsing other kinds of content
than 'Aktienführer'. It can be used as generic text-content recognizer and classifier.
Therefore it provides lot's of analysis and structure for that. 

Usually all akf-specific content is stored in files which are called 'akf_....'
this are the parts where you might want to put your custom functionalities. 

Ways how to do that are described in the following documentation parts.


## Creating segments 
For creating a segment from input data. In your segment holder class (i.e. 'akf_segment_holder') create
the code which recognizes start and  optionally the stop condition of the
segment. The segment recognition class should always inherit from 'Segment'
parent class (which gives a set of values and has abstract functions for matching).
When creating a matching function (match_start_condition or match_stop_condition)
make sure that the function has the same parameters as in the example (or as abstract functions in 'Segment').

If the 'match_stop_condition' function is not defined, the segment will continue
from the start line to the start of the next segment by default. This behaviour can
also be specified in the configuration. The given segment tag to the parents constructor
is used for common identification of the segment later. The match work function 
is used to log the segments data to properties of this segment. 

The fuzzy search can be used to recognize messy results with a regex. 

The match conditions themselves are checked automatically against each line 
until the segment has been found automatically.



```python

    class SegmentVerwaltung(Segment):
        # example recognition:
        # Verwaltung: 8045 Ismaning bei Mün- \n chen ...
        # Verwaltungsrat:
        # Verw.: (20b) Hannover ...

        def __init__(self):
            super().__init__("Verwaltung")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^((Verwaltung(:?srat\s?|\s?))|Verw\.\s?):", line_text, err_number=0)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True
```


## Parsing code 
To use your custom parsing code instantiate your 'segment_parser.py'
FunctionMapAKF constructor. Make sure your function tag is the one
used in the segment_classifier. For the keys in 'function_map' use 
the keys noted in your segment holder (i.e. 'akf_segment_holder')

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

### Parsing functions 
Here is an example of a mapped parsing function from above. These functions
can be stored in a common parsing class like in 'akf_parsing_functions_one'. 
The parameters have to be exactly the same like in example.

The add_check_element functionality adds in the output an additional
element for this segment with the original data (for evaluation later).
Also it improves the data to be better parsed. (recommended to use this function always)
Options for this function can be found in the configuration. 


To note results to final output the add_to_my_obj function is used. 
It works by simple key-value storing. If there are multiple objects within
one segment element counter can be incremented to assign values to another segment. 
There is also an option to only store if the value has any content. 

```python

    def parse_gruendung(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        year = dh.strip_if_not_none(origpost_red, ".,\s")
        self.ef.add_to_my_obj("year", year, object_number=element_counter, only_filled=True)
```
Within such parsing functions (i.e. within akf_parsing_functions_one), 
you can log can log segment specific info to file:

`
self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)
`


## Code analysis

## Configuration
Which configuration file is used is specified in main_start.py here.
```python
CODED_CONFIGURATION_PATH= './configuration/XXX.conf'
```
In the configuration files there are several options the same configuration
keys which are in the given config files can be used as command line parameters
also. 

At the beginning a common singleton configuration object is created, 
which allows to access configuration global.

Configuration can be accessed in each class of the project without 
passing it through the constructors from the root class. In a
non root-class the configuration can be initialised like this. 

```python
from akf_corelib.configuration_handler import ConfigurationHandler

class Example(object):
    def __init__(self):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
```

## Custom logging function
For general overview in the program output, custom logging functionality
was created. It's recommended to use this and initialize it in the constructor
of each class. 

```python

        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_PARSER_AKF_FN_TWO, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

        self.cpr.print("init akf parsing functions two")
```
Logging with the cpr.print function adds a tag (here the class name) at the start of each 
output. It only logs if the PRINT_SEGMENT_PARSER_AKF_FN_TWO from config is set to 'True'. 

In this way you can toggle logging each class or even more specific areas by
defining configuration parameters.

The warning and exception level tags will allow logging even if the base
'PRINT...' parameter is not true. The cpr.printex and cpr.printw functions provide
colored output to hint exceptions (red) and warnings (yellow). 

Copyright and License
--------

Copyright (c) 2017 Universitätsbibliothek Mannheim

Author: 
 * [Jan Kamlah](https://github.com/jkamlah)
 * [Johannes Stegmüller](https://github.com/Hyper-Node) 

**docxstruct** is Free Software. You may use it under the terms of the Apache 2.0 License.
See [LICENSE](./LICENSE) for details.


Acknowledgements
-------

The tools are depending on some third party libraries:


[akf-link]: https://github.com/UB-Mannheim/Aktienfuehrer-Datenarchiv-Tools "Aktienfuehrer-Datenarchiv-Tools "
[ocromore-link]: https://github.com/UB-Mannheim/ocromore "ocromore"