from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from .data_helper import DataHelper as dh
from .akf_parsing_functions_common import AKFCommonParsingFunctions as cf
from akf_corelib.regex_util import RegexUtil as regu

import regex


class AkfParsingFunctionsThree(object):

    def __init__(self, endobject_factory, output_analyzer):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_PARSER_AKF_FN_THREE, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

        self.cpr.print("init akf parsing functions three")

        self.ef = endobject_factory
        self.output_analyzer = output_analyzer

    def parse_something(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)



    def parse_beratende_mitglieder(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)


    def parse_sekretaere(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)



    def parse_geschaeftsleitung(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

    def parse_generaldirektion(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

    def parse_fernschreiber(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
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

    def parse_filialen(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # this is not active at the moment # todo use this maybe somewhen later
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)
        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)


    def parse_auslandsvertretungen(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
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


    def parse_kommandite_und_bank(self, real_start_tag, content_texts, content_lines, feature_lines,
                                   segmentation_class):
        # this is not active at the moment
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

    def parse_niederlassungen(self, real_start_tag, content_texts, content_lines, feature_lines,
                                   segmentation_class):
        # this is not active at the moment
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # prefilter entries
        filtered_content_texts = []
        for entry in content_texts:
            if "nd Geschäftsstellen" in entry:

                entry_new = regex.sub("nd\s?Geschäftsstellen\s?:","",entry).strip()
                if entry_new == "":
                    continue
                entry = entry_new

            filtered_content_texts.append(entry)

        # add in generalized form, there is not much structure over years
        only_add_if_value = True
        my_keys = cf.parse_general_and_keys(filtered_content_texts,
                                            join_separated_lines=True, current_key_initial_value="general_info",
                                            abc_sections=True)
        for key in my_keys:
            value = my_keys[key]
            self.ef.add_to_my_obj(key, value, object_number=element_counter,
                                  only_filled=only_add_if_value)
            element_counter += 1

        # parse the entries fill end-array
        """
        only_add_if_value = True

        for entry_f in filtered_content_texts:
            if ";" in entry_f:
                print("entry")


            else:
                split_entry = regex.split(',|und|u\.', entry_f)
                for entry_fs in split_entry:
                    self.ef.add_to_my_obj("location", entry_fs, object_number=element_counter,
                                          only_filled=only_add_if_value)
                    element_counter += 1
        """

        return True

    def parse_erzeugnisse(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # get categories
        my_keys = cf.parse_general_and_keys(content_texts,
                                            join_separated_lines=True, current_key_initial_value="general_info",
                                            abc_sections=True)
        only_add_if_value = True
        # parse each value to the result if filled
        for key in my_keys:
            value = my_keys[key].strip()
            # value_split = regex.split(r",|;", value) # don't split not really structured through that
            if value == "":
                continue
            self.ef.add_to_my_obj(key, value, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1


        return True

    def parse_haupterzeugnisse(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # get categories
        my_keys = cf.parse_general_and_keys(content_texts,
                                            join_separated_lines=True, current_key_initial_value="general_info",
                                            abc_sections=True)
        only_add_if_value = True
        # parse each value to the result if filled
        for key in my_keys:
            value = my_keys[key].strip()
            value_split = regex.split(r",|;|und", value) # don't split not really structured through that
            entry_counter = 0
            for entry in value_split:
                entry = entry.strip()
                if entry == "":
                    continue
                self.ef.add_to_my_obj(key+"_"+str(entry_counter), entry,
                                      object_number=element_counter, only_filled=only_add_if_value)
                element_counter += 1
                entry_counter += 1

        return True

    def parse_spezialitaeten(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # get categories
        my_keys = cf.parse_general_and_keys(content_texts,
                                            join_separated_lines=True, current_key_initial_value="general_info",
                                            abc_sections=True)
        only_add_if_value = True
        # parse each value to the result if filled
        for key in my_keys:
            value = my_keys[key].strip()
            # value_split = regex.split(r",|;", value) # don't split not really structured through that
            if value == "":
                continue
            self.ef.add_to_my_obj(key, value, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1

        return True


    def parse_anlagen(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # get categories
        my_keys = cf.parse_general_and_keys(content_texts,
                                            join_separated_lines=True, current_key_initial_value="general_info",
                                            abc_sections=True)
        only_add_if_value = True
        # parse each value to the result if filled
        for key in my_keys:
            value = my_keys[key].strip()
            # value_split = regex.split(r",|;", value) # don't split not really structured through that
            if value == "":
                continue
            self.ef.add_to_my_obj(key, value, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1

        return True

    def parse_zweigniederlassungen(self, real_start_tag, content_texts, content_lines,
                                   feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # get categories
        my_keys = cf.parse_general_and_keys(content_texts,
                                            join_separated_lines=True, current_key_initial_value="general_info",
                                            abc_sections=True)
        only_add_if_value = True
        # parse each value to the result if filled
        for key in my_keys:
            value = my_keys[key].strip()
            # value_split = regex.split(r",|;", value) # don't split not really structured through that
            if value == "":
                continue
            self.ef.add_to_my_obj(key, value, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1

        return True


    def parse_werke_betriebsstaetten(self, real_start_tag, content_texts, content_lines,
                                   feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # get categories
        my_keys = cf.parse_general_and_keys(content_texts,
                                            join_separated_lines=True, current_key_initial_value="general_info",
                                            abc_sections=True)
        only_add_if_value = True
        # parse each value to the result if filled
        for key in my_keys:
            value = my_keys[key].strip()
            # value_split = regex.split(r",|;", value) # don't split not really structured through that
            if value == "":
                continue
            self.ef.add_to_my_obj(key, value, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1

        return True

    def parse_betriebsanlagen(self, real_start_tag, content_texts, content_lines,
                                   feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # get categories
        my_keys = cf.parse_general_and_keys(content_texts,
                                            join_separated_lines=True, current_key_initial_value="general_info",
                                            abc_sections=True)
        only_add_if_value = True
        # parse each value to the result if filled
        for key in my_keys:
            value = my_keys[key].strip()
            # value_split = regex.split(r",|;", value) # don't split not really structured through that
            if value == "":
                continue
            self.ef.add_to_my_obj(key, value, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1

        return True


    def parse_beteiligungsgesellschaften(self, real_start_tag, content_texts, content_lines,
                                   feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        return False

    def parse_beteiligungen(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        only_add_if_value = True  # only add entries to result if they contain values
        complex_parsing = True  # parses some lines in more detailed way
        

        results = cf.match_common_block(content_texts, content_lines, complex_parsing, ['dividenden','kapital',
                                                                                        'parenthesis'])
        # log results to output
        for entry in results:
            change = False
            for key in entry.keys():
                value = entry[key]
                self.ef.add_to_my_obj(key, value,
                                      object_number=element_counter, only_filled=only_add_if_value)
                change = True
            if change:
                element_counter += 1

        return False

