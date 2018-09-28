from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from lib.akf_segment_holder import SegmentHolder
from lib.data_helper import DataHelper as dh
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
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)
        self.cpr.print("init segment classifier")

    def classify_file_segments(self, ocromore_data):
        lines = ocromore_data['lines']
        feats = ocromore_data['line_features']
        all_file_segments = AllSegments(len(lines), self.cpr, self.config)

        prev_line = None
        prev_text = None
        for current_line_index, current_line in enumerate(lines):
            current_features = feats[current_line_index]
            current_text = current_line['text']
            current_index = current_line['line_index']
            # create a combined lined object with optimized (removed) separation
            combined_line = None
            if prev_line is not None:
                combined_lines = dh.join_separated_lines([prev_text, current_text])
                combined_line = dh.join_joined_lines(combined_lines)
            else:
                combined_line = current_text
            # pass parameters to matching functions
            all_file_segments.match_my_segments(current_line, current_text, current_index, current_features, 
                                                prev_line, combined_line)
            prev_line = current_line
            prev_text = current_text

        if self.config.MATCH_UNTIL_NEXT_START_THEN_STOP_CONDITION:
            self.adapt_non_explicit_indices(all_file_segments)
        else:
            all_file_segments.correct_overlaps_index_field(only_start_tags=True)

        self.adapt_stop_index_in_last_segment(all_file_segments)

        ocromore_data['segmentation'] = all_file_segments
        return ocromore_data


    def adapt_stop_index_in_last_segment(self, all_file_segments):
        """
        Sets the stop_index for the last recognized segment, which
        is a special case and is usually not filled beforehand, because
        there is no next start index
        :param all_file_segments: holder object for segment classes and other info
        :return: None
        """

        # search for last segment
        saved_start_index = -1
        saved_last_segment = None
        for segment in all_file_segments.my_classes:
            # only count segmented segments
            if segment.start_was_segmented is False:
                continue

            if segment.start_line_index >= saved_start_index:
                saved_start_index = segment.start_line_index
                saved_last_segment = segment

        if saved_last_segment is None:
            return

        # adapt the last stop index of last segment
        saved_last_segment.stop_line_index = all_file_segments.number_of_lines-1
        saved_last_segment.stop_was_segmented = True # todo think about if this is necessary?





    def adapt_non_explicit_indices(self, all_file_segments):

        # update start and explicit stop tags first
        all_file_segments.correct_overlaps_index_field(only_start_tags=True)

        # fill undefined stop regions until next start region
        all_file_segments.fill_start_index_until_next_stop()


class AllSegments(object):
    """
    Accessor class for the segmentation of a file
    """

    def __init__(self, number_of_lines, cpr, config):
        # init all internal-classification classes
        self.index_field = []
        self.my_classes = []
        self.my_only_indices = []
        self.instantiate_classification_classes()
        self.number_of_lines = number_of_lines
        self.initialize_index_field(number_of_lines)
        self.cpr = cpr
        self.config = config
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
        self.index_field = []

        for ctr in range(0, number_of_lines):
            self.index_field.append(False)

    def correct_overlaps_index_field(self, only_start_tags=False):
        """
        Debugging function to correct areas which are overlapping with stop taq the next start tag
        Attention: This reinitializes (overwrites) the existing index field
        :return:
        """

        # reinitialize index field
        self.initialize_index_field(self.number_of_lines)

        # iterate classes - this not using only classes cause it's more for bigger sets of classes
        for segment_class_index, segment_class in enumerate(self.my_classes):
            if not segment_class.enabled:
                continue

            self.update_index_field(segment_class, only_start_tags=True)

        if only_start_tags is True:
            return self

        # iterate again and update the stop tags in manner that they are only updated until the next start tag
        for segment_class_index, segment_class in enumerate(self.my_classes):
            if not segment_class.enabled:
                continue
            if not segment_class.is_start_segmented():
                continue

            self.update_stop_tags(segment_class)


        return self

    def fill_start_index_until_next_stop(self):
        """
        Fills all segments start to next segments stop, if they don't have explicitly defined stop tags
        Adapts index field and the segment stop properties
        :return:
        """
        for segment_class_index, segment_class in enumerate(self.my_classes):
            if not segment_class.enabled:
                continue
            if segment_class.is_start_segmented() is False:
                # the segment wasn't found at all so no filling needed
                continue
            if segment_class.is_stop_segmented() is True:
                # class already has stop and therefore doesn't need to be filled
                continue

            # search until next found tag
            for index in range(segment_class.start_line_index+1, len(self.index_field)):
                current_field_item = self.index_field[index]
                if current_field_item is not False:
                    # next item begins, done with filling
                    segment_class.set_stop_segmented(index-1) # toggles stop_segmented, sets index
                    break
                else:
                    # field item is False, fill with the current segment tag
                    self.index_field[index] = segment_class.segment_tag


    def update_index_field(self, segmentation_class, only_start_tags=False):
        segment_tag = segmentation_class.segment_tag
        start_line_index = segmentation_class.start_line_index
        stop_line_index = segmentation_class.stop_line_index

        # if no start condition set - no update
        if start_line_index == -1:
            return

        # if start condition but no endcondition just update 1st line
        if stop_line_index == -1:
            stop_line_index = start_line_index + 1

        # fix some index glitches
        if start_line_index > stop_line_index:
            stop_line_index = start_line_index

        if start_line_index == stop_line_index:
            stop_line_index = start_line_index +1

        # special option for debugging purposes
        if only_start_tags is True:
            stop_line_index = start_line_index

        for index in range(start_line_index, stop_line_index+1):
            self.index_field[index] = segment_tag

    def update_stop_tags(self, segmentation_class):
        segment_tag = segmentation_class.segment_tag
        start_line_index = segmentation_class.start_line_index
        stop_line_index = segmentation_class.stop_line_index
        index_field_len = len(self.index_field)
        # if segment_tag is "Verwaltung":
        #    print("aqd")

        for index in range(start_line_index+1, index_field_len):

            # update until the next defined field appeads
            if self.index_field[index] is not False:
                break

            self.index_field[index] = segment_tag

    def instantiate_classification_classes(self):
        dict_test = SegmentHolder.__dict__.items()

        for key, value in dict_test:
            if inspect.isclass(value):
                my_instance = value()
                self.my_classes.append(my_instance)

    # overall function for iterating over all matches
    def match_my_segments(self, line, line_text, line_index, features, prev_line, combined_line):

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


            if self.config.REMATCH_START_CONDITION_UNTIL_ZERO_ERROR is True:
                # do segmenting until error rate of zero is reached
                start_error_number_before_match = segment_class.get_start_error_number()
                if not segment_class.is_start_segmented() or segment_class.get_start_error_number() >= 1:
                    start_updated = segment_class.match_start_condition(line, line_text, line_index, features,
                                                                        self.number_of_lines, prev_line, combined_line)
                    start_error_number_after_match = segment_class.get_start_error_number()
                    if start_error_number_before_match <= start_error_number_after_match:
                        # only update if the recognized number is lower
                        start_updated = False

                stop_error_number_before_match = segment_class.get_stop_error_number()
                if not segment_class.is_stop_segmented() or segment_class.get_stop_error_number() >= 1:
                    stop_updated = segment_class.match_stop_condition(line, line_text, line_index, features,
                                                                      self.number_of_lines, prev_line, combined_line)
                    stop_error_number_after_match = segment_class.get_stop_error_number()
                    if stop_error_number_before_match <= stop_error_number_after_match:
                        # only update if the recognized number is lower
                        stop_updated = False

            else:
                # just hit the first match and stop matching then -> standard  mode
                if not segment_class.is_start_segmented():
                    start_updated = segment_class.match_start_condition(line, line_text, line_index, features,
                                                                        self.number_of_lines, prev_line, combined_line)
                if not segment_class.is_stop_segmented():
                    stop_updated = segment_class.match_stop_condition(line, line_text, line_index, features,
                                                                      self.number_of_lines, prev_line, combined_line)

            if start_updated or stop_updated:
                # there was a change -> update the indices fields
                self.update_index_field(segment_class)


