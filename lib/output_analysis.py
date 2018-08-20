from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from akf_corelib.filehandler import FileHandler as fh
from lib.data_helper import DataHelper as dh
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
        # has then a ':' has optional trailing chars (get tag as reference group), match the first colon from left side as TAG seperator
        self.regex_advanced_segtest = re.compile(r"(?P<TAG>^[a-zA-ZäÄüÜöÖß]{2,}[^:]*)(?=:).*")
        # more simple for verification, arbitrary chars then : then some other chars
        self.regex_simple_segtest = re.compile(r"(?P<TAG>^.+):.*")

    def clear_output_folder(self):
        """
        Deletes folder content of output/analysis
        :return:
        """
        fh.delete_directory_tree(self.analysis_root)

    def log_segmentation_simple(self, ocromore_data, separator='¦¦'):
        lines = ocromore_data['lines']
        index_field = ocromore_data['segmentation'].index_field
        final_text_lines = []

        for line_index, line in enumerate(lines):
            segment_tag = str(index_field[line_index])
            line_text = line['text']
            # format the line in two columns with a separator
            final_line_text = ('%-30s%-30s' % (segment_tag, separator+line_text))
            final_text_lines.append(final_line_text)

        dh.write_array_to_root("segmentation_simple/", final_text_lines, ocromore_data, self.analysis_root)

    def log_unsegmentated(self, ocromore_data):
        """
        Log unsegmentated areas in ocromore data
        :param ocromore_data:
        :return:
        """
        main_seg = self.create_dict_main_segmentation(ocromore_data)
        # test_seg_simple = self.create_dict_test_segmentation(ocromore_data, simple_mode=True)
        test_seg_advan = self.create_dict_test_segmentation(ocromore_data)
        diff_info = self.create_diff_segmetation(main_seg, test_seg_advan, skip_multi_keys=True)
        linified_diff_info = self.diff_data_to_array(diff_info)
        dh.write_array_to_root("diff_info/", linified_diff_info, ocromore_data, self.analysis_root)
        return diff_info

    def log_accumulated_unsegmentated(self, accumulated_diff_info, ocromore_data):
        acc_diff_array =  self.acc_diff_data_to_array(accumulated_diff_info)
        dh.write_array_to_root("diff_info/", acc_diff_array, ocromore_data, \
                               self.analysis_root, accumulated=True)


    def accumulate_diff_info(self, ocromore_data, diff_info, accumulated_diff_info):
        """
        Accumulate diff info for one file to the accumulated diff info object for later logging
        (one accumulated info per akf-year)
        :param ocromore_data:
        :param diff_info:
        :param accumulated_diff_info:
        :return:accumulated_diff_info modified
        """
        table_name = ocromore_data['file_info'].tablename
        (missing_keys, additional_keys, same_keys) = diff_info

        for tag in missing_keys:
            accumulated_diff_info.add_info_at(tag, table_name, True, False, False)
        for tag in additional_keys:
            accumulated_diff_info.add_info_at(tag, table_name, False, True, False)
        for tag in same_keys:
            accumulated_diff_info.add_info_at(tag, table_name, False, False, True)


        return accumulated_diff_info


    def acc_diff_data_to_array(self, accumulated_diff_info, separator='¦¦', shorten_tablenames=True):
        """
        creates an text-line-array of accumulated_diff_info for print out
        :param accumulated_diff_info:
        :param separator: seperator char of columns in output
        :param shorten_tablenames: shorten the tablenames like 0001_1956_230-6_B_049_0005_msa_best
        :return: final lines array
        """
        final_lines = []

        def create_lines(reference_dict):
            """
            Helper function to fetch data from referenced dictionary and format it
            :param reference_dict:
            :return:
            """
            lines_local = []
            for miss_info_tag in reference_dict:
                miss_info_obj = reference_dict.get(miss_info_tag)
                counter_str = str(miss_info_obj.counter)
                table_all_str = ""

                for table in miss_info_obj.tables:
                    table_occurence = str(miss_info_obj.tables.get(table))
                    # cut the long tablenames like 0001_1956_230-6_B_049_0005_msa_best
                    if shorten_tablenames:
                        table = table.split('_')[0]
                    table_str = table + "(" + table_occurence + ");"
                    table_all_str += table_str

                # format the line in two columns with a separator
                final_line_text = (
                        '%-90s%-15s%-30s' % (miss_info_tag, separator + counter_str, separator + table_all_str))
                lines_local.append(final_line_text)

            return lines_local

        # linify missing info accumulated
        final_lines.append("### Missing keys (missing in main-seg, there in test-seg)------------------------")
        lines_missing = create_lines(accumulated_diff_info.missing_tags)
        final_lines.extend(lines_missing)

        # linify additional info accumulated
        final_lines.append("### Additional keys (there in main-seg, missing in test-seg)---------------------")
        lines_additional = create_lines(accumulated_diff_info.additional_tags)
        final_lines.extend(lines_additional)

        # linify same keys + headline accumulated
        final_lines.append("### Same keys (there in main-seg and also in test-seg)---------------------------")
        lines_same = create_lines(accumulated_diff_info.same_tags)
        final_lines.extend(lines_same)


        return final_lines

    def diff_data_to_array(self, diff_info):
        (missing_keys, additional_keys, same_keys) = diff_info
        final_lines = []

        # linify missing keys + headline
        final_lines.append("### Missing keys (missing in main-seg, there in test-seg)------------------------")
        for key in missing_keys:
            final_lines.append(key)
        final_lines.append("")

        # linify additional keys + headline
        final_lines.append("### Additional keys (there in main-seg, missing in test-seg)---------------------")
        for key in additional_keys:
            final_lines.append(key)
        final_lines.append("")

        # linify same keys + headline
        final_lines.append("### Same keys (there in main-seg and also in test-seg)---------------------------")
        for key in same_keys:
            final_lines.append(key)
        final_lines.append("")

        return final_lines

    def create_diff_segmetation(self, main_seg, test_seg, skip_multi_keys=False):

        same_keys = []
        missing_keys = []
        additional_keys = []

        for key_test in test_seg.keys():
            value_test = test_seg[key_test]

            # ignore multi entries if toggled, assuming they are second order elements
            if skip_multi_keys and value_test > 1:
                continue
            if key_test in main_seg.keys():
                same_keys.append(key_test)
            else:
                missing_keys.append(key_test)

        for key_main in main_seg.keys():
            if key_main not in test_seg.keys():
                additional_keys.append(key_main)


        return (missing_keys, additional_keys, same_keys)




    def create_dict_main_segmentation(self, ocromore_data):
        """
        Create a dictionary for segmentation from existing segmentation
        index field
        :param ocromore_data:
        :return:
        """
        segmentation_dict = {}
        seg_data = ocromore_data['segmentation']
        seg_classes = seg_data.my_classes
        lines = ocromore_data['lines']
        for segclass in seg_classes:
            if not segclass.is_start_segmented():
                continue
            start_index = segclass.get_start_line_index()
            # extract the real tag from line
            tag = dh.get_real_tag_from_segment(segclass,lines[start_index])
            if tag in segmentation_dict.keys():
                segmentation_dict[tag] = segmentation_dict[tag] + 1
            else:
                segmentation_dict[tag] = 1

        return segmentation_dict

    def create_dict_test_segmentation(self, ocromore_data, simple_mode=False):
        """
        Creates a simple segmentation dictionary for this file
        which assumes each leading characters before a ':' are
        segmentation tags
        :param ocromore_data:
        :return:
        """
        advanced_mode = True  # default is True
        if simple_mode is True:
            advanced_mode = False

        segmentation_dict = {}

        lines = ocromore_data['lines']
        previous_line_text = ""

        for line in lines:
            line_text = line['text']
            if advanced_mode is True:
                result = self.regex_advanced_segtest.search(line_text)
            else:
                result = self.regex_simple_segtest.search(line_text)

            if result is not None:
                tag = result.group('TAG')  # get the tag

                len_pre_line = len(previous_line_text)
                if len_pre_line >= 1 and \
                        previous_line_text[len_pre_line-1] == "-" and previous_line_text[len_pre_line-2] != '.':
                    tag = previous_line_text[0:len_pre_line-1] + tag  # add previous line text to tag (w/o dash)
                if tag in segmentation_dict.keys():
                    segmentation_dict[tag] = segmentation_dict[tag]+1
                else:
                    segmentation_dict[tag] = 1
            previous_line_text = line_text.strip()

        return segmentation_dict


    class AccumulatedInfo(object):

        class InfoObj(object):
            def __init__(self, tag):
                self.counter = 0  # how often does the tag occur overall
                self.tables = {}  # how often does the tag occur in specific tablename (which is key to this dict)
                self.tag = tag    # related tag

            def add_tag_from_table(self, tag, tablename):
                if tablename in self.tables.keys():
                    self.counter += 1
                    self.tables[tablename] += 1
                else:
                    self.counter += 1
                    self.tables[tablename] = 1

        def __init__(self):
            self.missing_tags = {}
            self.additional_tags = {}
            self.same_tags = {}


        def add_info_at(self, tag, tablename, missing, additional, same):
            """
            Adds or updates infoobjects with
            :param tablename:
            :param tag:
            :param missing:
            :param additional:
            :param same:
            :return:
            """
            def update_ref_dict(tag, tablename, ref_obj):
                if tag in ref_obj.keys():
                    info_obj = ref_obj[tag]
                    info_obj.add_tag_from_table(tag, tablename)
                    ref_obj[tag] = info_obj

                else:
                    info_obj = self.InfoObj(tag)
                    info_obj.add_tag_from_table(tag, tablename)
                    ref_obj[tag] = info_obj
                return ref_obj



            if missing is True:
                updated_ref = update_ref_dict(tag, tablename, self.missing_tags)
                self.missing_tags = updated_ref
            if additional is True:
                updated_ref = update_ref_dict(tag, tablename, self.additional_tags)
                self.additional_tags = updated_ref
            if same is True:
                updated_ref = update_ref_dict(tag, tablename, self.same_tags)
                self.same_tags = updated_ref

