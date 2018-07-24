from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from akf_corelib.random import Random
import re
import abc
import sys
import inspect
##
# notes to regex
# re.match("c", "abcdef")    # No match
# re.search("c", "abcdef")   # Match


class Segment(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, segment_tag):
        self.start_was_segmented = False
        self.stop_was_segmented = False
        self.start_index = -1
        self.stop_index = -1
        self.segment_tag = segment_tag

    @abc.abstractmethod
    def match_start_condition(self, line, line_text, line_index, features):
        return

    @abc.abstractmethod
    def match_stop_condition(self, line, line_text, line_index, features):
        # by default it's the same line as stop line as start line recognized
        self.stop_index = self.start_index
        return

    def start_or_stop_segmented(self):
        if self.start_was_segmented or self.stop_was_segmented:
            return True
        else:
            return False

class SegmentHolder():
    class SegmentSitz(Segment):

        def __init__(self):
            super().__init__("Sitz")

        def match_start_condition(self, line, line_text, line_index, features):
            #current_text = "SOMET" + line_text
            #match = re.match(r"Sitz\s?:.+", current_text)
            #match2 = re.fullmatch(r"Sitz\s?:.+", current_text)
            match_sitz = re.search(r"^Sitz\s?:.+", line_text)
            if match_sitz is not None:
                self.start_index = line_index
                self.start_was_segmented = True




class AllSegments():

    # idea indices mathed
    index_field = [
        False,
        False,
        True,

    ]

    def __init__(self):
        # init all internal-classification classes
        self.my_classes = []
        self.instantiate_classification_classes()

    def instantiate_classification_classes(self):
        dict_test = SegmentHolder.__dict__.items()

        for key, value in dict_test:
            if inspect.isclass(value):
                my_instance = value()
                self.my_classes.append(my_instance)



    # overall function for iterating over all matches
    def match_my_segments(self, line, line_text, line_index, features):
        for segment_class in self.my_classes:
            if segment_class.start_or_stop_segmented() is True:
                continue

            segment_class.match_start_condition(line, line_text, line_index, features)
            segment_class.match_stop_condition(line, line_text, line_index, features)










class SegmentClassifier():

    def __init__(self):
        print("init segment classifier")

        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_CLASSIFIER, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL)


    def classify_file_segments(self, ocromore_data):
        all_file_segments = AllSegments()
        lines = ocromore_data['lines']
        feats = ocromore_data['line_features']



        for current_line_index, current_line in enumerate(lines):
            current_features = feats[current_line_index]
            current_text = current_line['text']
            current_index = current_line['line_index']

            all_file_segments.match_my_segments(current_line, current_text, current_index, current_features)


            #print("asd")

        ocromore_data['segmentation'] = all_file_segments
        return ocromore_data