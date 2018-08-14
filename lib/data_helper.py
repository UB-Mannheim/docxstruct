class DataHelper(object):
    """
    Class with helper functions for handling the data block
    """

    @staticmethod
    def get_real_tag_from_segment(segment, line, remove_trailing_colon=True):
        """
        Extracts the recognized tag string from the line object from the corresponding segment
        :param segment: segment class instance
        :param line: line-object from data
        :param remove_trailing_colon: indicator if results trailing colons ':' are removed
        :return: string of tag
        """
        start = segment.key_tag_cindex_start
        stop = segment.key_tag_cindex_stop

        text = line['text'][start:stop]
        len_text = len(text)

        # remove trailing ':'
        if remove_trailing_colon:
            if text[len_text-1] == ":":
                text = text[0:len_text-1]

        return text