from akf_corelib.filehandler import FileHandler as fh


class DataHelper(object):
    """
    Class with helper functions for handling the data block
    """

    @staticmethod
    def get_real_tag_from_segment(segment, start_line, remove_trailing_colon=True):
        """
        Extracts the recognized tag string from the line object from the corresponding segment
        :param segment: segment class instance
        :param line: line-object from data
        :param remove_trailing_colon: indicator if results trailing colons ':' are removed
        :return: string of tag
        """
        start = segment.key_tag_cindex_start
        stop = segment.key_tag_cindex_stop

        text = start_line['text'][start:stop]
        len_text = len(text)

        # remove trailing ':'
        if remove_trailing_colon:

            if len_text >= 1 and text[len_text-1] == ":":
                text = text[0:len_text-1]

        return text


    @staticmethod
    def get_rest_content_start_line(segmentation_class, start_line, trim=True):
        text = start_line['text']
        stop = segmentation_class.key_tag_cindex_stop
        rest_start = text[stop:]
        if trim:
            rest_start = rest_start.strip()
        return rest_start

    @staticmethod
    def get_content(segment_lines, feature_lines, segmentation_class):
        start_index = segmentation_class.get_start_line_index()
        stop_index = segmentation_class.get_stop_line_index()
        selected_start_line = segment_lines[start_index]
        feature_start_line = feature_lines[start_index]
        real_tag = DataHelper.get_real_tag_from_segment(segmentation_class, selected_start_line)
        rest_content_start_line = DataHelper.get_rest_content_start_line(segmentation_class, selected_start_line)

        # if there are no further line, return obtained content
        if start_index == stop_index:
            return real_tag, [rest_content_start_line], [selected_start_line], [feature_start_line]

        # otherwise fetch the rest of the content
        other_rest_content_texts = []
        other_rest_content_lines = []
        other_rest_feature_lines = []

        other_rest_content_texts.append(rest_content_start_line)
        other_rest_content_lines.append(selected_start_line)
        other_rest_feature_lines.append(feature_start_line)

        for current_index in range(start_index+1, stop_index+1):
            current_line = segment_lines[current_index]
            current_feature_lines = feature_lines[current_index]
            other_rest_content_texts.append(current_line['text'])
            other_rest_content_lines.append(current_line)
            other_rest_feature_lines.append(current_feature_lines)

        return real_tag, other_rest_content_texts, other_rest_content_lines, other_rest_feature_lines

    @staticmethod
    def write_array_to_root(base_path, text_lines, ocromore_data, analysis_root, accumulated=False):
        """
        Writes a line-array to the base path in root path with ocromore data file and db name
        :param base_path:
        :param text_lines:
        :param ocromore_data:
        :param analysis_root: root path in base directory
        :param accumulated: file is accumulated file naming different
        :return:
        """

        dbpath = ocromore_data['file_info'].dbpath
        tablename = ocromore_data['file_info'].tablename

        full_dir = analysis_root + base_path + dbpath+"/"
        if accumulated is False:
            full_path = full_dir + tablename + ".txt"
        else:
            full_path = full_dir +"accumulated_report"+".txt"

        fh.create_directory_tree(full_dir)

        my_file = open(full_path, 'w')

        for text_line in text_lines:
            my_file.write(text_line+"\n")

        my_file.close()