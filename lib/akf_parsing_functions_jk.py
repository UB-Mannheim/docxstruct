from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from .data_helper import DataHelper as dh
from .akf_parsing_functions_common import AKFCommonParsingFunctions as cf
from akf_corelib.regex_util import RegexUtil as regu

import regex


class AkfParsingFunctionsJK(object):

    def __init__(self, endobject_factory, output_analyzer):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_PARSER_AKF_FN_THREE, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

        self.cpr.print("init akf parsing functions three")

        self.ef = endobject_factory
        self.output_analyzer = output_analyzer

    def xparse_something(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)


    def xparse_fernschreiber(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        split_post = regex.split(',|;|\.|\n|u\.', origpost)

        only_add_if_value = True
        number = None
        reduced_entry = None

        for entry in split_post:
            # number_match = regex.search("\d*\s?\/?\-?\d*\s?\d*?", entry)  # search numbers
            number_match = regex.search("[\d\s?\/?\-?]*", entry)  # search numbers

            if number_match is not None and number_match.end() > 0:
                number = number_match.group().strip()
                reduced_entry = entry.replace(number, "").strip(".,; ")
                self.ef.add_to_my_obj("number", number, object_number=element_counter,
                                      only_filled=only_add_if_value)
                self.ef.add_to_my_obj("location", reduced_entry, object_number=element_counter,
                                      only_filled=only_add_if_value)
                element_counter += 1
            else:
                reduced_addition = entry.strip(".,; ")
                if number is not None and reduced_addition!="": # number was in previous post
                    reduced_entry += " "+reduced_addition
                    self.ef.add_to_my_obj("location", reduced_entry.strip(), object_number=element_counter,
                                          only_filled=only_add_if_value)
                    element_counter += 1
                else:
                    self.cpr.printw("unexpected case during parsing of fernschreiber")

        return True

    def xparse_auslandsvertretungen(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # this is not active at the moment
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        only_add_if_value = True
        split_post = regex.split(',|und', origpost_red)
        for entry in split_post:
            entry_stripped = entry.strip(".,; ")
            self.ef.add_to_my_obj("location", entry_stripped, object_number=element_counter,
                                  only_filled=only_add_if_value)
            element_counter += 1

    def parse_bilanzen(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # init
        only_add_if_string = True
        geschaeftslage = origpost_red.replace("- ", "")

        #parsing
        table_start = False
        table_dict = {}
        for entry, features in zip(content_lines,feature_lines):
            # read the number of coloumns the currency of the attributes
            if table_start is False:
                if features.counter_special_chars > 3 and features.counter_numbers > 10:
                    years = entry['text'].split(" ")
                    for idx, year in enumerate(years):
                        # Count the coloumns 0,1,2,...
                        table_dict[idx] = {'year':year}
                elif table_dict is not None:
                    for idx in table_dict.keys():
                        table_dict[idx]["currency"] = entry['text']
                        table_start = True
                colname = ""
            elif table_start and entry['text'] != "":
                if features.counter_numbers < 2:
                    colname = entry['text']+" "
                    continue
                colname += ''.join([i for i in entry['text'] if not i.isdigit()]).strip()
                numbers = ''.join([i for i in entry['text'] if i.isdigit() or i == " "]).strip().split(" ")
                # Check if line is date
                if features.counter_alphabetical < 2 and features.counter_special_chars > 3 and features.counter_numbers > 10:
                    continue

                count_years = len(years)-1
                count_numbers = 0
                number = ""
                for grpidx, numbergrp in enumerate(reversed(numbers)):
                    # Check and clean artifacts
                    count_numbers += len(numbergrp)
                    if len(numbergrp) > 3 and grpidx > 0:
                        if numbergrp[3:] == list(reversed(numbers))[grpidx-1][:len(numbergrp[3:])]:
                            numbergrp = numbergrp[:3]
                    if len(numbergrp) == 3 and grpidx != len(numbers) and count_numbers < (features.counter_numbers/2):
                        number = (numbergrp+" "+number).strip()
                        continue
                    else:
                        count_numbers = 0
                        table_dict[count_years][colname] = (numbergrp+" "+number).strip()
                        number = ""
                        count_years -= 1

                colname = ""

        self.ef.add_to_my_obj("balances", table_dict, object_number=element_counter,only_filled=only_add_if_string)

    def parse_gewinn_und_verlust(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # init
        only_add_if_string = True
        geschaeftslage = origpost_red.replace("- ", "")

        #parsing
        self.ef.add_to_my_obj("business situation", geschaeftslage, object_number=element_counter,
                              only_filled=only_add_if_string)

    def parse_bezugsrechte(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # init
        only_add_if_string = True
        geschaeftslage = origpost_red.replace("- ", "")

        #parsing
        self.ef.add_to_my_obj("business situation", geschaeftslage, object_number=element_counter,
                              only_filled=only_add_if_string)

    def parse_geschaeftslage(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # init
        only_add_if_string = True
        geschaeftslage = origpost_red.replace("- ", "")

        #parsing
        self.ef.add_to_my_obj("business situation", geschaeftslage, object_number=element_counter,
                              only_filled=only_add_if_string)