from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from akf_corelib.random import Random
from akf_corelib.regex_util import RegexUtil as regu

import re
import abc
import sys
import inspect
import regex
##
# notes to regex
# re.match("c", "abcdef")    # No match
# re.search("c", "abcdef")   # Match


class Segment(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, segment_tag):
        self.start_was_segmented = False
        self.stop_was_segmented = False
        self.enabled = True
        self.only = False
        self.start_line_index = -1
        self.stop_line_index = -1
        self.key_tag_cindex_start = -1 # character index of keytag: 'Vorstand: Name' ---> 0
        self.key_tag_cindex_stop = -1  # character index of keytag: 'Vorstand: Name' ---> 9
        self.restcontent_in_start_line = -1
        self.segment_tag = segment_tag

    def disable(self):
        self.enabled = False

    def set_only(self):
        self.only = True

    @abc.abstractmethod
    def match_start_condition(self, line, line_text, line_index, features):
        return

    @abc.abstractmethod
    def match_stop_condition(self, line, line_text, line_index, features):
        # by default it's the same line as stop line as start line recognized
        self.stop_line_index = self.start_line_index
        return

    def start_or_stop_segmented(self):
        if self.start_was_segmented or self.stop_was_segmented:
            return True
        else:
            return False

    def is_start_segmented(self):
        return self.start_was_segmented

    def is_stop_segmented(self):
        return self.stop_was_segmented

    def set_keytag_indices(self, match):
        """
        From regex match set the keytag indices, takes 1st occurence,
        also checks if there is restcontent besides the match in the
        line to check
        :param match: regex match
        :return:
        """
        start_m = match.regs[0][0]
        stop_m = match.regs[0][1]

        self.key_tag_cindex_start = start_m
        self.key_tag_cindex_stop = stop_m
        len_match = stop_m-start_m
        len_rest = len(match.string)-len_match
        if len_rest > 0:
            self.restcontent_in_start_line = len_rest



class SegmentHolder(object):
    """
    This is a simple holder class for the adapted segments which
    contain start and stop recognition conditions, wrapper should
    be kept as simple as possible
    """

    class SegmentSitz(Segment):
        # example recognition line:
        # Sitz: (20a) Peine, Gerhardstr. 10.

        def __init__(self):
            super().__init__("Sitz")
            # self.disable()  # comment out to disable a segment
            # self.set_only() # comment out to segment this segments and other segments with that tag exclusively

        def match_start_condition(self, line, line_text, line_index, features):
            match_sitz = regu.fuzzy_search(r"^Sitz\s?:", line_text)
            if match_sitz is not None:
                self.set_keytag_indices(match_sitz)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):
            if self.start_was_segmented is True:
                self.stop_line_index = self.start_line_index
                self.stop_was_segmented = True
                return True

    class SegmentFernruf(Segment):
        # example recognition:
        # Fernruf: Peine 26 41, 26 09 und \n 2741, \n Grossilsede 5 41.

        def __init__(self):
            super().__init__("Fernruf")

        def match_start_condition(self, line, line_text, line_index, features):
            match_start = regu.fuzzy_search(r"^Fernruf\s?:", line_text)

            if match_start is not None:
                self.set_keytag_indices(match_start)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):
            match_stop = regu.fuzzy_search(r"^Fernschreiber\s?:", line_text)

            if match_stop is not None:
                self.stop_line_index = line_index -1
                self.stop_was_segmented = True
                return True

    class SegmentFernschreiber(Segment):
        # example recognition:
        # Fernruf: Peine 26 41, 26 09 und \n 2741, \n Grossilsede 5 41.

        def __init__(self):
            super().__init__("Fernschreiber")

        def match_start_condition(self, line, line_text, line_index, features):
            match_start = regu.fuzzy_search(r"^Fernschreiber\s?:", line_text)

            if match_start is not None:
                self.set_keytag_indices(match_start)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):
            match_stop = regu.fuzzy_search(r"^Vorstand\s?:", line_text)

            if match_stop is not None:
                self.stop_line_index = line_index -1
                self.stop_was_segmented = True
                return True


    class SegmentVorstand(Segment):
        # example recognition:
        # Vorstand: \n Diedrich Dännemark, Peine; \n Helmuth Heintzmann, Herne; \n ...


        def __init__(self):
            super().__init__("Vorstand")

        def match_start_condition(self, line, line_text, line_index, features):
            match_start = regu.fuzzy_search(r"^Vorstand\s?:", line_text)


            if match_start is not None:
                self.set_keytag_indices(match_start)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):
            match_stop = regu.fuzzy_search(r"^Aufsichtsrat\s?:", line_text)

            if match_stop is not None:
                self.stop_line_index = line_index -1
                self.stop_was_segmented = True
                return True

    class SegmentAufsichtsrat(Segment):
        # example recognition:
        # Aufsichtsrat: Julius Fromme, Peine, Vors.; \n Hermann Beermann, Hannover, 1.stellv. \n


        def __init__(self):
            super().__init__("Aufsichtsrat")


        def match_start_condition(self, line, line_text, line_index, features):
            match_start = regu.fuzzy_search(r"^Aufsichtsrat\s?:", line_text)


            if match_start is not None:
                self.set_keytag_indices(match_start)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):
            match_stop = regu.fuzzy_search(r"^Gründung\s?:", line_text)

            if match_stop is not None:
                self.stop_line_index = line_index -1
                self.stop_was_segmented = True
                return True

    class SegmentGruendung(Segment):
        # example recognition:
        # Gründung: 1858.


        def __init__(self):
            super().__init__("Gründung")

        def match_start_condition(self, line, line_text, line_index, features):
            match_start = regu.fuzzy_search(r"^Gründung\s?:", line_text)


            if match_start is not None:
                self.set_keytag_indices(match_start)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):

            if self.start_was_segmented and not self.stop_was_segmented:
                self.stop_line_index = self.start_line_index
                self.stop_was_segmented = True
                return True

    class SegmentTaetigkeitsgebiet(Segment):
        # example recognition:
        # Tätigkeitsgebiet: \n Erzeugung von: Erze, Kohle, Strom,

        def __init__(self):
            super().__init__("Tätigkeitsgebiet")

        def match_start_condition(self, line, line_text, line_index, features):
            match_start = regu.fuzzy_search(r"^Tätigkeitsgebiet\s?:", line_text)

            if match_start is not None:
                self.set_keytag_indices(match_start)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):

            match_stop = regu.fuzzy_search(r"^Haupterzeugnisse\s?:", line_text)

            if match_stop is not None:
                self.stop_line_index = line_index -1
                self.stop_was_segmented = True
                return True

class AllSegments(object):
    """
    Accessor class for the segmentation of a file
    """

    # idea indices mathed
    index_field = []

    def __init__(self, number_of_lines, cpr):
        # init all internal-classification classes
        self.my_classes = []
        self.my_only_indices = []
        self.instantiate_classification_classes()
        self.initialize_index_field(number_of_lines)
        self.cpr = cpr
        self.get_only_classes()

    def get_only_classes(self):
        """
        Get all classes which are tagged by the only flag
        :return:
        """
        for segment_index, segment_class in enumerate(self.my_classes):
            if segment_class.only is True:
                self.my_only_indices.append(segment_index)

        if len(self.my_only_indices) >= 1:
            self.cpr.print("using only indices, since there is at least one class set to only")

    def initialize_index_field(self, number_of_lines):
        for ctr in range(0, number_of_lines):
            self.index_field.append(False)

    def update_index_field(self, segmentation_class):
        segment_tag = segmentation_class.segment_tag
        start_line_index = segmentation_class.start_line_index
        stop_line_index = segmentation_class.stop_line_index

        if start_line_index == -1 or stop_line_index == -1:
            return

        if start_line_index > stop_line_index:
            stop_index = start_line_index

        #stop_index = start_index+ 5 # just a test
        self.index_field[start_line_index:stop_line_index] = [segment_tag] * (stop_line_index-start_line_index+1)


    def instantiate_classification_classes(self):
        dict_test = SegmentHolder.__dict__.items()

        for key, value in dict_test:
            if inspect.isclass(value):
                my_instance = value()
                self.my_classes.append(my_instance)



    # overall function for iterating over all matches
    def match_my_segments(self, line, line_text, line_index, features):

        # 'only'-tagged class usage
        using_only_classes = False
        if len(self.my_only_indices) >= 1:
            using_only_classes = True

        # iterate classes
        for segment_class_index, segment_class in enumerate(self.my_classes):
            if not segment_class.enabled:
                continue

            if using_only_classes:
                # if at least one class was tagged only, skip all other classes who are only tagged
                if segment_class_index not in self.my_only_indices:
                    continue

            start_updated = False
            stop_updated = False
            if not segment_class.is_start_segmented():
                start_updated = segment_class.match_start_condition(line, line_text, line_index, features)
            if not segment_class.is_stop_segmented():
                stop_updated = segment_class.match_stop_condition(line, line_text, line_index, features)

            if start_updated or stop_updated:
                # there was a change -> update the indices fields
                self.update_index_field(segment_class)







class SegmentClassifier():

    def __init__(self):
        print("init segment classifier")

        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_CLASSIFIER, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL)


    def classify_file_segments(self, ocromore_data):
        lines = ocromore_data['lines']
        feats = ocromore_data['line_features']
        all_file_segments = AllSegments(len(lines), self.cpr)

        for current_line_index, current_line in enumerate(lines):
            current_features = feats[current_line_index]
            current_text = current_line['text']
            current_index = current_line['line_index']

            all_file_segments.match_my_segments(current_line, current_text, current_index, current_features)

        ocromore_data['segmentation'] = all_file_segments
        return ocromore_data