from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from .data_helper import DataHelper as dh
from .akf_parsing_functions_common import AKFCommonParsingFunctions as cf

import regex


class AkfParsingFunctionsTwo(object):

    def __init__(self, endobject_factory, output_analyzer):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_PARSER_AKF_FN_TWO, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

        self.cpr.print("init akf parsing functions two")

        self.ef = endobject_factory
        self.output_analyzer = output_analyzer

    def parse_zahlstellen(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        split_post = origpost_red.split(';')
        DEFAULT_ENTRY = 1
        ADDITIONAL_INFO_BOTH = 2      # beide - two previous
        ADDITIONAL_INFO_ALL_PREV = 3  # sämtl. - all previous

        final_entries = []
        for index, entry in enumerate(split_post):
            entry_stripped = entry.strip()

            if "beide" in entry_stripped:
                entry_final = regex.sub(r"beide\s?\.?", "", entry_stripped).strip()
                final_entries.append((ADDITIONAL_INFO_BOTH, entry_final, "", ""))
                continue
            if "sämtl" in entry_stripped:
                entry_final = regex.sub(r"sämtl\s?\.?", "", entry_stripped).strip()
                final_entries.append((ADDITIONAL_INFO_ALL_PREV, entry_final, "", ""))
                continue

            entry_split = entry_stripped.split(',')
            bank = ""
            city = ""
            title = ""
            rest_info = ""
            for fragment_index, fragment in enumerate(entry_split):
                if fragment_index == 0:
                    bank = fragment
                elif fragment_index == 1:
                    city = fragment
                elif fragment_index >= 2:
                    rest_info += fragment
            final_entries.append((DEFAULT_ENTRY, bank, city, title))

        # reverse list for better processing
        reverse_fe = final_entries.__reversed__()
        current_additional_info = ""
        current_info_index = None
        current_entry_type = None
        final_list = []
        for item_index, item in enumerate(reverse_fe):
            entry_type, entryorbank, city, title = item
            # change current additional info
            if entry_type == ADDITIONAL_INFO_BOTH or entry_type == ADDITIONAL_INFO_ALL_PREV:
                current_info_index = item_index
                current_additional_info = entryorbank
            elif entry_type == DEFAULT_ENTRY:
                templist = [(entryorbank, city, title, current_additional_info)]
                templist.extend(final_list)
                final_list = templist

            # end 'beide'-entry because it's over after 2 iterations
            if current_entry_type == ADDITIONAL_INFO_BOTH and item_index-current_info_index >= 1:
                current_info_index = None
                current_additional_info = ""

        # finally note the entries to output
        only_add_if_value = True
        for entry in final_list:
            bank, city, title, add_info = entry
            if add_info != "" and add_info != None:
                city += add_info
            self.ef.add_to_my_obj("bank", bank, object_number=element_counter, only_filled=only_add_if_value)
            self.ef.add_to_my_obj("city", city, object_number=element_counter, only_filled=only_add_if_value)
            self.ef.add_to_my_obj("title", title, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1

        return True

    def parse_grundkapital(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

    def parse_ordnungsnrdaktien(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)


    def parse_grossaktionaer(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)
