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
        ADDITIONAL_INFO_CITY = 2    # beide - two previous
        ADDITIONAL_INFO_CITY_2 = 3  # sämtl. - all previous

        final_entries = []
        for index, entry in enumerate(split_post):
            entry_stripped = entry.strip()

            if "beide" in entry_stripped:
                additional_city_info = entry_stripped
                final_entries.append((ADDITIONAL_INFO_CITY, additional_city_info))
                continue
            if "sämtl" in entry_stripped:
                additional_city_info = entry_stripped
                final_entries.append((ADDITIONAL_INFO_CITY_2, additional_city_info))
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
            final_entries.append((DEFAULT_ENTRY,bank,city,title))

        return