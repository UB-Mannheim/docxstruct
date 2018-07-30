from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from lib.segment_holder_akf import SegmentHolder

import inspect

class SegmentClassifier(object):
    """
    This is the basic handler for classification
    which get's accessed from root/-outside classes.
    """

    def __init__(self):

        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_CLASSIFIER, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL)
        self.cpr.print("init segment classifier")

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
        self.number_of_lines = number_of_lines
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

        oldlen = len(self.index_field)
        #stop_index = start_index+ 5 # just a test
        self.index_field[start_line_index:stop_line_index] = [segment_tag] * (stop_line_index-start_line_index+1)

        newlen = len(self.index_field)
        if oldlen != newlen:
            print("asd")

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
                start_updated = segment_class.match_start_condition(line, line_text, line_index, features, self.number_of_lines)
            if not segment_class.is_stop_segmented():
                stop_updated = segment_class.match_stop_condition(line, line_text, line_index, features,self.number_of_lines)

            if start_updated or stop_updated:
                # there was a change -> update the indices fields
                self.update_index_field(segment_class)


