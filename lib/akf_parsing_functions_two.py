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

        self.output_analyzer.log_segment_information(origpost_red)

        final_items = cf.parse_general_and_keys(content_texts,
                                                join_separated_lines=False,
                                                current_key_initial_value="General_Info")

        for key in final_items.keys():
            value = final_items[key]
            if value is None or value == "":
                continue
            self.ef.add_to_my_obj(key, value, object_number=element_counter, only_filled=True)
            element_counter += 1