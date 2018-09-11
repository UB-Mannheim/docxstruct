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

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^((Verwaltung(:?srat\s?|\s?))|Verw\.\s?):", line_text, err_number=0)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True
```


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