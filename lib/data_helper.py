from akf_corelib.filehandler import FileHandler as fh


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

            if len_text >= 1 and text[len_text-1] == ":":
                text = text[0:len_text-1]

        return text

    @staticmethod
    def write_array_to_root(base_path, text_lines, ocromore_data, analysis_root):
        """
        Writes a line-array to the base path in root path with ocromore data file and db name
        :param base_path:
        :param text_lines:
        :param ocromore_data:
        :return:
        """

        dbpath = ocromore_data['file_info'].dbpath
        tablename = ocromore_data['file_info'].tablename

        full_dir = analysis_root + base_path + dbpath+"/"
        full_path = full_dir + tablename + ".txt"
        fh.create_directory_tree(full_dir)

        my_file = open(full_path, 'w')

        for text_line in text_lines:
            my_file.write(text_line+"\n")

        my_file.close()