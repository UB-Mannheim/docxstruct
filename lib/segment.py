import abc



class Segment(object):
    """
    Root segment class for a classification segments,
    child specialized sgments are stored in SegmentHolder
    class.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, segment_tag):
        self.start_was_segmented = False
        self.stop_was_segmented = False
        self.start_error_number = 1000   # initialized very high to trigger potential update
        self.stop_error_number = 1000    # initialized very high to trigger potential update

        self.enabled = True
        self.only = False
        self.start_line_index = -1
        self.stop_line_index = -1
        self.key_tag_cindex_start = -1 # character index of keytag: 'Vorstand: Name' ---> 0
        self.key_tag_cindex_stop = -1  # character index of keytag: 'Vorstand: Name' ---> 9
        self.restcontent_in_start_line = -1
        self.segment_tag = segment_tag
        self.snippet = None
        self.info_handler = None

    def disable(self):
        self.enabled = False

    def set_only(self):
        self.only = True

    def set_start_error_number(self, start_error_number):
        self.start_error_number = start_error_number

    def get_start_error_number(self):
        return self.start_error_number

    def set_stop_error_number(self, stop_error_number):
        self.stop_error_number = stop_error_number

    def get_stop_error_number(self):
        return self.stop_error_number

    def get_start_line_index(self):
        return self.start_line_index

    def get_stop_line_index(self):
        return self.stop_line_index

    def get_segment_tag(self):
        return self.segment_tag

    def do_match_work(self, start_or_stop, match, line_index, match_errors):
        if start_or_stop is True: # it's a start match
            self.set_keytag_indices(match) # this separates keytag from rest of line
            self.start_line_index = line_index
            self.start_was_segmented = True
            self.set_start_error_number(match_errors)
        else:
            self.stop_line_index = line_index
            self.stop_was_segmented = True
            self.set_stop_error_number(match_errors)

    @abc.abstractmethod
    def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
        return  # 0  # return number 0 for indication undefined, don't return this in overwritten conditions

    @abc.abstractmethod
    def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
        # by default don't assign any stop condition, leave at initial value
        # self.stop_line_index = self.start_line_index
        return  # 0  # return number 0 for indication undefined, don't return this in overwritten conditions

    def start_or_stop_segmented(self):
        if self.start_was_segmented or self.stop_was_segmented:
            return True
        else:
            return False

    def is_start_segmented(self):
        return self.start_was_segmented

    def is_stop_segmented(self):
        return self.stop_was_segmented

    def set_stop_segmented(self, stop_index):
        self.stop_line_index = stop_index
        self.stop_was_segmented = True

    def set_start_segmented(self, start_index):
        self.start_line_index = start_index
        self.start_was_segmented = True

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