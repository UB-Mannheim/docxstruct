from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from akf_corelib.filehandler import FileHandler as fh
from lib.data_helper import DataHelper as dh
from lib.akf_known_uncategories import KnownUncategories
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
        self.known_ucs = KnownUncategories()
        self.ocromore_data = None

    def set_current_data(self, data):
        self.ocromore_data = data

    def clear_output_folder(self):
        """
        Deletes folder content of output/analysis
        :return:
        """
        fh.delete_directory_tree(self.analysis_root)

    def log_parsed_output(self, ocromore_data, separator='¦¦'):
        if self.config.LOG_PARSED_SEGMENTED_OUTPUT is False:
            return
        results = ocromore_data['results']
        file_info = ocromore_data['file_info'].name
        # iterate the recognized tags
        for key in results.my_object:
            value_json = results.export_as_json_at_key(key)
            lines_json = value_json.split('\n')
            final_text_lines = []

            # add dividers to the lines
            final_text_lines.append(key + ": " + file_info + "------------------------------------------------")
            final_text_lines.extend(lines_json)
            final_text_lines.append("")
            final_text_lines.append("")

            key = key.replace("/", "_")  # fix to prevent folder hop in filename

            # print to file finally (append style)
            dh.write_array_to_root_simple("parsed_output", key,
                                          final_text_lines, self.analysis_root, append_mode=True)

    def log_original_to_segment_diff(self, ocromore_data, use_delimiters=True):
        if self.config.LOG_SEGMENTED_TO_ORIG_DIFF_PER_FILE is False:
            return

        diff_info = {}  # diff info object which is used for accumulated report

        # fetch the rest text from ocromore data
        rest_texts = ocromore_data['analysis_to_orig']['original_rest']
        rest_text = ""
        for text in rest_texts:

            rest_text += text
            if use_delimiters:
                rest_text += "\n"  # delimiters are optional

        # get the segmented data
        # wwwww = self.eg.diff_seg_to_orig_at_key(ocromore_data)

        segmented_texts = []
        complete_text = ""  # unused atm
        for inst_class in ocromore_data['segmentation'].my_classes:
            if not inst_class.is_start_segmented():
                continue
            start_line_index = inst_class.start_line_index
            stop_line_index = inst_class.stop_line_index

            for index in range(start_line_index,stop_line_index+1):
                text = ocromore_data['lines'][index]['text']
                segmented_texts.append(text)
                complete_text += text

        # rest texts 123
        # segmented texts 100
        # sort segmented texts after length
        segmented_texts.sort(key=lambda s: len(s))
        segmented_texts.reverse()

        for text_subtr in segmented_texts:
            # texlen_before = len(rest_text)
            rest_text = rest_text.replace(text_subtr, "", 1)  # only replace once
            # texlen_after = len(rest_text)
            # if texlen_before == texlen_after:
            #     print("asd")

        file_name = ocromore_data['file_info'].name
        db_path = ocromore_data['file_info'].dbpath
        db_name = ocromore_data['file_info'].dbname

        info_to_write = []
        info_to_write.append("File:"+file_name+"---------------")
        info_to_write.extend(rest_text)
        info_to_write.append("")
        info_to_write.append("")

        # log information
        dh.write_array_to_root_simple("orig_to_seg_difference"+db_path+"/", "rests_"+db_name, info_to_write
                                      , self.analysis_root, append_mode=True)

        # create the diff info object and return for accumulated report
        diff_info['file_name'] = file_name
        diff_info['db_name'] = db_name
        diff_info['original_length'] = len(complete_text)
        diff_info['rest'] = rest_text
        diff_info['rest_length'] = len(rest_text)

        return diff_info

    def log_segmentation_diff_for_categories(self, ocromore_data):
        """
        Takes the current ocromore_data for a table and for each
        occuring key logs the rest text and the difference
        within a diff info object which is returned (and can
        from which be accumulated later for multiple tables/files)

        there is a flag in config which also allows to write the
        actual output in the diff info which is the subtractor
        element in the diff for better checking.
        :param ocromore_data: input data for table
        :return: diff info object contains texts and rests per found tag (
        """
        if self.config.LOG_PARSED_TO_ORIG_DIFF_PER_CATEGORY is False:
            return

        diff_info = {}
        results = ocromore_data['results']
        file_info = ocromore_data['file_info'].name
        diff_info['file_info'] = file_info
        diff_info['keys'] = {}
        # iterate the recognized tags
        for key in results.my_object:
            if key is 'overall_info':
                continue # skip special key which has different structure (in case it's enabled)
            rest_text, original_text = results.diff_parsed_to_orig_at_key(key)
            diff_info['keys'][key] = {}
            diff_info['keys'][key]['rest_text'] = rest_text
            diff_info['keys'][key]['original_text'] = original_text

            value_json = None
            if self.config.LOG_PARSED_TO_ORIG_ADD_OUTPUT_JSON:
                value_json = results.export_as_json_at_key(key, remove_first_object=True)

            final_text_lines = []

            # add dividers to the lines
            final_text_lines.append(key + ": " + file_info + "------------------------------------------------")
            final_text_lines.append("Rest:" + rest_text)
            final_text_lines.append("Original:" + original_text)

            if value_json != None:
                final_text_lines.append("Parsed-Json:" + value_json)

            final_text_lines.append("")
            final_text_lines.append("")

            key = key.replace("/", "_")  # fix to prevent folder hop in filename

            # print to file finally (append style)
            dh.write_array_to_root_simple("parsed_to_orig_difference", key,
                                          final_text_lines, self.analysis_root, append_mode=True)

        return diff_info

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


    def log_segment_information(self, segment_tag, text_lines, real_segment_tag):
        """
        Logs an array with a given tag append wise into a file with the name
        of segment_tag in 'output/analysis/segmentation_segments' can be used
        to have a look on specific segments to understand the parsing better
        :param segment_tag: tag for filename
        :param text_lines: array of lines which get's logged
        :param real_segment_tag: can differ to segment tag, is given on each append
        :return:
        """

        final_text_lines = []
        file_name = self.ocromore_data['file_info'].name

        # add dividers to the lines
        final_text_lines.append(real_segment_tag + ": " + file_name + "------------------------------------------------")
        final_text_lines.extend(text_lines)
        final_text_lines.append("")
        final_text_lines.append("")

        segment_tag = segment_tag.replace("/", "_")  # fix to prevent folder hop in filename

        # print to file finally (append style)
        dh.write_array_to_root_simple("segmentation_segments", segment_tag,
                                      final_text_lines, self.analysis_root, append_mode=True)

    def log_unsegmentated(self, ocromore_data):
        """
        Log unsegmentated areas in ocromore data
        :param ocromore_data:
        :return:
        """
        main_seg = self.create_dict_main_segmentation(ocromore_data)
        # test_seg_simple = self.create_dict_test_segmentation(ocromore_data, simple_mode=True)
        test_seg_advan = self.create_dict_test_segmentation(ocromore_data)
        diff_info = self.create_diff_segmetation(main_seg, test_seg_advan, skip_multi_keys=False)
        linified_diff_info = self.diff_data_to_array(diff_info)
        dh.write_array_to_root("diff_info/", linified_diff_info, ocromore_data, self.analysis_root)
        return diff_info

    def log_accumulated_unsegmentated(self, accumulated_diff_info, ocromore_data):
        acc_diff_array = self.acc_diff_data_to_array(accumulated_diff_info)
        dh.write_array_to_root("diff_info/", acc_diff_array, ocromore_data, \
                               self.analysis_root, accumulated=True)

    def log_accumulated_categories(self, accumulated_diff_info, ocromore_data):
        acc_diff_array = self.acc_origindiff_data_to_array(accumulated_diff_info)
        dh.write_array_to_root("parsed_to_orig_difference/", acc_diff_array, ocromore_data, \
                               self.analysis_root, accumulated=True)

    def log_accumulated_orig_to_segment(self, accumulated_diff_info, ocromore_data):
        acc_diff_array = self.acc_segmentdiff_data_to_array(accumulated_diff_info)
        dh.write_array_to_root("orig_to_seg_difference/", acc_diff_array, ocromore_data, \
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

    def accumulate_diff_info_output_to_orig(self, ocromore_data, diff_info, accumulated_diff_info):

        for key in diff_info['keys']:
            value = diff_info['keys'][key]
            rest_text = value['rest_text']
            original_text = value['original_text']
            if key not in accumulated_diff_info.keys():
                accumulated_diff_info[key] = {'rest_chars': 0, 'original_chars': 0}

            accumulated_diff_info[key]['rest_chars'] += len(rest_text)
            accumulated_diff_info[key]['original_chars'] += len(original_text)

        return accumulated_diff_info
    
    
    def accumulate_diff_info_orig_to_segmentation(self, ocromore_data, diff_info, accumulated_diff_info):

        file_name = diff_info['file_name']
        # db_name = diff_info['db_name'] # maybe use later
        rest_text = diff_info['rest']
        len_rest_text = diff_info['rest_length']
        len_orig_text = diff_info['original_length']

        if 'acc_len_rest_text' not in accumulated_diff_info.keys():
            accumulated_diff_info['acc_len_rest_text'] = len_rest_text
        else:
            accumulated_diff_info['acc_len_rest_text'] += len_rest_text

        if 'acc_rest_text' not in accumulated_diff_info.keys():
            accumulated_diff_info['acc_rest_text'] = rest_text
        else:
            accumulated_diff_info['acc_rest_text'] += rest_text

        if 'len_orig_text' not in accumulated_diff_info.keys():
            accumulated_diff_info['len_orig_text'] = len_orig_text
        else:
            accumulated_diff_info['len_orig_text'] += len_orig_text

        if 'filenames' not in accumulated_diff_info.keys():
            accumulated_diff_info['filenames'] = []

        accumulated_diff_info['filenames'].append(file_name)

        return accumulated_diff_info


    def acc_segmentdiff_data_to_array(self, accumulated_diff_info):
        """
        creates an text-line-array of accumulated_diff_info for print out
        for difference of segmented output to origin
        :param accumulated_diff_info:
        :return: final lines array
        """
        final_lines = []

        separators = '%-30s%-30s'
        final_lines.append(separators % ("Overall Rest Length in Chars: ", str(accumulated_diff_info['acc_len_rest_text'])))
        final_lines.append(separators % ("Original Length in Chars: ", str(accumulated_diff_info['len_orig_text'])))
        final_lines.append("Overall Rest Text: " + accumulated_diff_info['acc_rest_text'])

        return final_lines
    
    def acc_origindiff_data_to_array(self, accumulated_diff_info):
        """
        creates an text-line-array of accumulated_diff_info for print out
        for difference of parsed output to rest info - at
        the moment logs numbers of chars in original and rest after subtraction
        with the related key
        :param accumulated_diff_info:
        :return: final lines array
        """
        final_lines = []

        for key in accumulated_diff_info:
            value = accumulated_diff_info[key]
            rest_chars = value['rest_chars']
            orig_chars = value['original_chars']

            final_line_text = (
                    '%-45s%-30s%-30s' % ("Key: " + key, "Rest-Chars:  " + str(rest_chars),
                                         "Original-Chars:  " + str(orig_chars)))

            final_lines.append(final_line_text)

        return final_lines

    def acc_diff_data_to_array(self, accumulated_diff_info, separator='¦¦', shorten_tablenames=True):
        """
        creates an text-line-array of accumulated_diff_info for print out
        :param accumulated_diff_info:
        :param separator: separator char of columns in output
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
            for info_tag in reference_dict:
                info_obj = reference_dict.get(info_tag)

                # if the tag is in one of the filtered list, which indicate no category, don't append to lines
                if self.config.FILTER_UNCATEGORIES_OVERALL:
                    is_uc = self.known_ucs.check_uncategories(info_tag)
                    if is_uc:
                        continue

                counter_str = str(info_obj.counter)
                table_all_str = ""

                for table in info_obj.tables:
                    table_occurence = str(info_obj.tables.get(table))
                    # cut the long tablenames like 0001_1956_230-6_B_049_0005_msa_best
                    if shorten_tablenames:
                        table = table.split('_')[0]
                    table_str = table + "(" + table_occurence + ");"
                    table_all_str += table_str

                # format the line in two columns with a separator
                final_line_text = (
                        '%-90s%-15s%-30s' % (info_tag, separator + counter_str, separator + table_all_str))
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

    def diff_data_to_array(self, diff_info, separator='¦¦'):
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


    def diff_data_to_array_categories(self, diff_info, separator='¦¦'):
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

        def append_multi(ref_list, value, count):
            for i in range(0, count):
                ref_list.append(value)
            return ref_list

        same_keys = []
        missing_keys = []
        additional_keys = []

        for key_test in test_seg.keys():
            value_test = test_seg[key_test]

            # ignore multi entries if toggled, assuming they are second order elements
            if skip_multi_keys and value_test > 1:
                continue
            if key_test in main_seg.keys():
                value_main = main_seg[key_test]
                same_overlap = min(value_main, value_test)
                same_keys = append_multi(same_keys, key_test, same_overlap)
            else:
                missing_keys = append_multi(missing_keys, key_test, value_test)

        for key_main in main_seg.keys():
            value_main = main_seg[key_main]

            if key_main not in test_seg.keys():
                 additional_keys = append_multi(additional_keys, key_main, value_main)

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

