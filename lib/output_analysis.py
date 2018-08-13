from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from akf_corelib.filehandler import FileHandler as fh

import re

class OutputAnalysis(object):
    """
    Provides various methods to analyze the akf-hocrparser output
    and intermediary results for correctness
    """

    def __init__(self):

        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_OUTPUT_ANALYSIS, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

        self.cpr.print("init output analysis")
        self.analysis_root = self.config.OUTPUT_ROOT_PATH + "/analysis/"
        self.clear_output_folder()

        # starts with at least X or more alphabetical chars (and arbitrary amount of other chars)  [to exclude years 1999: xxx and so on]
        # has then a ':' has optional trailing chars (get tag as reference group)
        self.regex_advanced_segtest = re.compile(r"(?P<TAG>^[a-zA-Z]{2,}.*):.*")
        # more simple for verification, arbitrary chars then : then some other chars
        self.regex_simple_segtest = re.compile(r"(?P<TAG>^.+):.*")

    def clear_output_folder(self):
        """
        Deletes folder content of output/analysis
        :return:
        """
        fh.delete_directory_tree(self.analysis_root)

    def log_segmentation_simple(self, ocromore_data, seperator='¦¦'):
        lines = ocromore_data['lines']
        index_field = ocromore_data['segmentation'].index_field
        final_text_lines = []

        for line_index, line in enumerate(lines):
            segment_tag = str(index_field[line_index])
            line_text = line['text']
            final_line_text = ('%-30s%-30s' % (segment_tag, seperator+line_text))
            final_text_lines.append(final_line_text)

        self.write_array_to_root("segmentation_simple/", final_text_lines, ocromore_data)

    def log_unsegmentated(self, ocromore_data):
        """
        Log unsegmentated areas in ocromore data
        :param ocromore_data:
        :return:
        """
        self.create_test_segmentation(ocromore_data)


    def create_test_segmentation(self, ocromore_data):
        """
        Creates a simple segmentation dictionary for this file
        which assumes each leading characters before a ':' are
        segmentation tags
        :param ocromore_data:
        :return:
        """
        ADVANCED_MODE = False # True is preferred
        segmentation_dict = {}

        lines = ocromore_data['lines']
        previous_line_text = ""

        for line in lines:
            line_text = line['text']
            if ADVANCED_MODE is True:
                result = self.regex_advanced_segtest.search(line_text)
            else:
                result = self.regex_simple_segtest.search(line_text)

            if result is not None:
                tag = result.group('TAG')  # get the tag

                len_pre_line = len(previous_line_text)
                if len_pre_line >=1 and \
                        previous_line_text[len_pre_line-1] == "-":
                    tag = previous_line_text[0:len_pre_line-1] + tag  # add previous line text to tag (w/o dash)
                if tag in segmentation_dict.keys():
                    segmentation_dict[tag] = segmentation_dict[tag]+1
                else:
                    segmentation_dict[tag] = 1
            previous_line_text = line_text.strip()

        print("asd")

    def write_array_to_root(self, base_path, text_lines, ocromore_data):
        """
        Writes a line-array to the base path in root path with ocromore data file and db name
        :param base_path:
        :param text_lines:
        :param ocromore_data:
        :return:
        """

        dbpath = ocromore_data['file_info'].dbpath
        tablename = ocromore_data['file_info'].tablename

        full_dir = self.analysis_root + base_path + dbpath+"/"
        full_path = full_dir + tablename + ".txt"
        fh.create_directory_tree(full_dir)

        my_file = open(full_path, 'w')

        for text_line in text_lines:
            my_file.write(text_line+"\n")

        my_file.close()