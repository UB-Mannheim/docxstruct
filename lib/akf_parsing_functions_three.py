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
            found_pretext = False
            entry_strip = entry.strip()
            if entry_strip == "":
                continue

            pre_text_match = regex.search("[^\d]*", entry_strip) # todo check condition
            if pre_text_match:
                pretext = pre_text_match.group().strip()
                entry_strip = entry_strip.replace(pretext, "", 1).strip()
                #found_pretext = True

            # number_match = regex.search("\d*\s?\/?\-?\d*\s?\d*?", entry)  # search numbers
            number_match = regex.search("[\d\s?\/?\-?]*", entry_strip)  # search numbers

            if number_match is not None and number_match.end() > 0:
                number = number_match.group().strip()
                reduced_entry = entry_strip.replace(number, "").strip(".,; ")
                if found_pretext:
                    reduced_entry = reduced_entry.replace(pretext,"").strip()

                if reduced_entry.strip() == "":
                    reduced_entry = pretext
                else:
                    self.ef.add_to_my_obj("additional_info", pretext, object_number=element_counter,
                                          only_filled=only_add_if_value)

                self.ef.add_to_my_obj("number", number, object_number=element_counter,
                                      only_filled=only_add_if_value)
                self.ef.add_to_my_obj("location", reduced_entry, object_number=element_counter,
                                      only_filled=only_add_if_value)
                element_counter += 1
            else:
                reduced_addition = entry_strip.strip(".,; ")
                if number is not None and reduced_addition!="": # number was in previous post
                    reduced_entry += " "+reduced_addition
                    self.ef.add_to_my_obj("location", reduced_entry.strip(), object_number=element_counter,
                                          only_filled=only_add_if_value)
                    element_counter += 1
                else:
                    # just save additional info
                    self.ef.add_to_my_obj("additional_info", pretext, object_number=element_counter,
                                          only_filled=only_add_if_value)
                    #element_counter += 1

                    # self.cpr.printw("unexpected case during parsing of fernschreiber")

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
            value = my_keys[key]
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
            value = my_keys[key]
            for value_sub in value:
                value_split = regex.split(r",|;|und", value_sub) # don't split not really structured through that
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
            value = my_keys[key]
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
            value = my_keys[key]
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
            value = my_keys[key]
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
            value = my_keys[key]
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
            value = my_keys[key]
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
        origpost, origpost_red, element_counter, content_texts_2 = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        content_texts = content_texts_2
        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        only_add_if_value = True  # only add entries to result if they contain values
        complex_parsing = True  # parses some lines in more detailed way

        results = cf.match_common_block(content_texts, content_lines, complex_parsing, ['dividenden','kapital',
                                                                                        'parenthesis', 'beteiligungen'])
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

        return True

    def parse_tochtergesellschaften(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
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
            value = my_keys[key]
            # value_split = regex.split(r",|;", value) # don't split not really structured through that
            if value == "":
                continue
            self.ef.add_to_my_obj(key, value, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1

        return True

    def parse_wertpapier_kenn_nr(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

    def parse_rechte_und_vorzugsaktien(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
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
            value = my_keys[key]
            # value_split = regex.split(r",|;", value) # don't split not really structured through that
            if value == "":
                continue
            self.ef.add_to_my_obj(key, value, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1

        return True

    def parse_aktionaere(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        only_add_if_value = True

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)
        if "Aktionärvertreter" in real_start_tag:

            persons_list = cf.parse_persons(origpost_red)
            for (name, city, title, rest_info) in persons_list:
                self.ef.add_to_my_obj("name", name, object_number=element_counter, only_filled=only_add_if_value)
                self.ef.add_to_my_obj("city", city, object_number=element_counter, only_filled=only_add_if_value)
                self.ef.add_to_my_obj("title", title, object_number=element_counter, only_filled=only_add_if_value)
                self.ef.add_to_my_obj("add_info", rest_info, object_number=element_counter, only_filled=only_add_if_value)
                element_counter += 1

        else:
            self.ef.add_to_my_obj("info", origpost_red, object_number=element_counter, only_filled=only_add_if_value)

        return True

    def parse_anleihen(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        only_add_if_value = True

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # finalize content texts
        entries_adapted = {}
        current_key = "general_0"
        current_counter = 0
        # detect if there are lines with only year and no other info (indicator for multiple entries)
        multi_entries = False
        next_key = None
        emissionsbetrag_index = 0
        for text_index, text in enumerate(content_texts):
            text = text.strip()
            if text == "":
                continue
            if next_key is not None:
                current_key = next_key
                next_key = None

            match_percentage_dot = regex.search("^[\.\d\s\:]{2,7}\%", text)
            if match_percentage_dot:
                current_counter += 1
                current_key = "general_"+str(current_counter)

            match_only_year = regex.search("^([\d\-\/]+)$", text)  # use this as splitter ?
            match_emissionsbetrag, err_number = regu.fuzzy_search("^Emissionsbetrag\s?:", text, err_number=1)
            match_double_dot = regex.search("^.*[^1]+:[^1]*", text)
            if match_emissionsbetrag:
                result_emissionsbetrag = match_emissionsbetrag.group()
                text = text.replace(result_emissionsbetrag, "").strip()
                emissionsbetrag_index += 1
                current_key = "Emissionsbetrag"+str(emissionsbetrag_index)  # use  a normed key for later recognition

                if "Umtauschrecht" in text: # special case (2 keys in same line)
                    next_key = "Umtauschrecht"

            if not match_emissionsbetrag and match_double_dot:
                result_double_dot = match_double_dot.group()
                if "1:1" not in text and "Emissionsbetrag" not in text:
                    text = text.replace(result_double_dot, "").strip()
                    current_key = result_double_dot
            if "Emissionsbetrag" in current_key:
                if current_key not in entries_adapted.keys():
                    entries_adapted[current_key] = ""
                entries_adapted[current_key] += " "+ text
                continue
            if match_only_year and text_index != len(content_texts)-1:
                multi_entries = True
                #current_entry = (current_entry + " " + text).strip()
                #current_key = text.strip()
                #entries_adapted[current_key] = text.strip()
                if current_key not in entries_adapted.keys():
                    entries_adapted[current_key] = ""

                entries_adapted[current_key] = (entries_adapted[current_key] + " " + text).strip()

                #entries_adapted.append(current_entry)

                # if text_index == len(content_texts) - 1:
                #    continue  # jump last index cause not relevant

            else:
                if current_key not in entries_adapted.keys():
                    entries_adapted[current_key] = text.strip()
                else:
                    entries_adapted[current_key] = (entries_adapted[current_key] + " " + text).strip()

        #if current_entry != "":
        #    entries_adapted[current_key] = current_entry

        for key in entries_adapted:
            value = entries_adapted[key]
            if key == "general":
                value_parsed_simple, value_parsed = cf.parse_anleihe(value)
            elif key == "Emissionsbetrag":
                value_parsed = []
                for extra_value in value:
                    value_parsed_simple, value_parsed_once = cf.parse_emissionsbetrag(extra_value)
                    value_parsed.append(value_parsed_once)
            else:
                value_parsed = value

            self.ef.add_to_my_obj(key, value_parsed, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1


        return True

    def parse_kurse_v_zuteilungsrechten(self, real_start_tag, content_texts,
                                        content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        only_add_if_value = True
        # examples
        # Düsseldorf am 10.Okt. 1955: 175,5 %.
        # am 10. Okt. 1955 in Berlin NGS: 31,5%.

        #  Inh.-Akt. 6.10.1955 NGS: 249 DM /n Nam.-Akt. 10.10.1955 NGS: 239 DM.
        #  68,18 % Einz.: NGS am 10.10.1955: \n 20 DM (Berlin)
        #  Berlin am 10.10.1955 NGS: \n Nam.-St.-Akt.Lit.A : 12 DM \n Berlin am 10.10.1955 NGS: \n Nam.-St.-Akt.Lit.B: 7 DM
        #  sometimes it has a block of dividenden (check on if segmentation was ok here)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        """ todo 
        final_entries_new = cf.parse_general_and_keys(content_texts,
                                            join_separated_lines=True, current_key_initial_value="general_info",
                                            abc_sections=True)
        """

        # create segments for results
        final_entries = {}
        current_key = 1  # numeric key for simplicity at first
        append_ctr = 0
        for text_index, text in enumerate(content_texts):
            text_stripped = text.strip()
            if text_stripped == "":
                continue
            current_feats = feature_lines[text_index]
            word_count = current_feats.counter_words
            if append_ctr >= 1 and word_count > 3:
                current_key += 1

            if current_key not in final_entries.keys():
                final_entries[current_key] = []
                final_entries[current_key].append(text_stripped)
            else:
                final_entries[current_key].append(text_stripped)

            append_ctr += 1

        # add results to final json
        for key in final_entries:
            value = final_entries[key]
            for value_sub in value:
                value_parsed_simple, value_parsed = cf.parse_kurs_von_zuteilungsrechten(value_sub)
                change = False
                for key_subsub in value_parsed:
                    value_pp = value_parsed[key_subsub]

                    self.ef.add_to_my_obj(key_subsub, value_pp, object_number=element_counter,
                                        only_filled=only_add_if_value)
                    change = True
                if change is True:
                    element_counter += 1



        return True

    def parse_emissionsbetrag(self, real_start_tag, content_texts,
                                        content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        only_add_if_value = True
        # examples
        #

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)


    def parse_geschaeftslage(self, real_start_tag, content_texts,
                                        content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        only_add_if_value = True
        # examples
        # Produktion und Versand haben in der
        # Umsatz 1953/54: DM 13,241 Müill.
        current_key = "general"
        final_texts = {}
        for text_index, text in enumerate(content_texts):
            match_umsatz = regex.search(r"(Umsatz\s?[\d\-\/]+\s?[:\=]|Umsatz\s?[:\=])", text)

            if match_umsatz:
                umsatz_result = match_umsatz.group()
                text_split = text.split(umsatz_result)
                if len(text_split) == 1:
                    text = text.replace(umsatz_result, "").strip()
                else:
                    text_first = text_split[0]
                    text_second = text_split[1]
                    if current_key not in final_texts.keys():
                        final_texts[current_key] = text_first
                    else:
                        final_texts[current_key] += " " + text_first
                    text = text_second
                current_key = umsatz_result

            if current_key not in final_texts.keys():
                final_texts[current_key] = text
            else:
                final_texts[current_key] += " " + text

        for key in final_texts:
            value = final_texts[key]
            if "Umsatz" in key:
                # parse umsatz
                umsatzp_simple, umsatzp = cf.parse_umsatz(value)
                self.ef.add_to_my_obj(key, umsatzp, object_number=element_counter, only_filled=only_add_if_value)
            else:
                self.ef.add_to_my_obj(key, value.strip(), object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)
