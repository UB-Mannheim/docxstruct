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
    def match_start_condition(self, line, line_text, line_index, features, num_lines):
        return

    @abc.abstractmethod
    def match_stop_condition(self, line, line_text, line_index, features, num_lines):
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