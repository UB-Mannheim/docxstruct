from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from .data_helper import DataHelper as dh
from .akf_parsing_functions_common import AKFCommonParsingFunctions as cf

import regex


class AkfParsingFunctionsOne(object):

    def __init__(self, endobject_factory, output_analyzer):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_PARSER_AKF_FN_ONE, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

        self.cpr.print("init akf parsing functions one")

        self.ef = endobject_factory
        self.output_analyzer = output_analyzer

    def add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter):

        if self.config.ADD_INFO_ENTRY_TO_OUTPUT:
            origpost, origpost_red = dh.create_stringified_linearray(
                content_texts)  # complete text, complete text without \n
            self.ef.add_to_my_obj("origpost", origpost_red, object_number=element_counter)
            self.ef.add_to_my_obj("type", segmentation_class.segment_tag, object_number=element_counter)
            element_counter += 1

        joined_texts = cf.join_separated_lines(content_texts)  # join dash separated texts
        origpost, origpost_red = dh.create_stringified_linearray(joined_texts)   # final reduced array for further processing

        return origpost, origpost_red, element_counter, joined_texts

    def parse_sitz(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        """
         "Sitz": [
                {
                  "origpost": "Mergenthalerallee 79-81, 65760 Eschborn Telefon:(069) 7 50 06-0 Telefax:(069) 7 50 06-111 e-mail:info@3u.net Internetseite:http://www.3u.net ",
                  "type": "Sitz",
                  "street": "Mergenthalerallee",
                  "street_number": "79-81",
                  "zip": "65760",
                  "city": "Eschborn",
                  "phone": "(069) 7 50 06-0",
                  "fax": "(069) 7 50 06-111",
                  "email": [
                    "info@3u.net"
                  ],
                  "www": [
                    "http://www.3u.net"
                  ]
                }
              ],
        """
        # get basic data
        element_counter = 0

        origpost, origpost_red, element_counter, content_texts = \
            self.add_check_element(content_texts, real_start_tag, segmentation_class, element_counter)

        # get relevant info
        num_id, city, street, street_number, additional_info = cf.parse_id_location(origpost_red)

        # add stuff to ef
        only_add_if_value = True
        self.ef.add_to_my_obj("numID", num_id, object_number=element_counter, only_filled=only_add_if_value)
        self.ef.add_to_my_obj("city", city, object_number=element_counter, only_filled=only_add_if_value)
        self.ef.add_to_my_obj("street", street, object_number=element_counter, only_filled=only_add_if_value)
        self.ef.add_to_my_obj("street_number", street_number, object_number=element_counter, only_filled=only_add_if_value)
        self.ef.add_to_my_obj("additional_info", additional_info, object_number=element_counter, only_filled=only_add_if_value)

        return True

    def parse_verwaltung(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # kmy_obj_2 = self.ef.print_me_and_return()
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            self.add_check_element(content_texts, real_start_tag, segmentation_class, element_counter)

        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        if "srat" in real_start_tag:
            # Verwaltungsrat ..
            persons_final = cf.parse_persons(origpost_red)
            only_add_if_filed = True
            for entry in persons_final:
                name, city, title, rest_info = entry
                self.ef.add_to_my_obj("name", name, object_number=element_counter, only_filled=only_add_if_filed)
                self.ef.add_to_my_obj("city", city, object_number=element_counter, only_filled=only_add_if_filed)
                self.ef.add_to_my_obj("title", title, object_number=element_counter, only_filled=only_add_if_filed)
                self.ef.add_to_my_obj("rest", rest_info, object_number=element_counter, only_filled=only_add_if_filed)
                element_counter += 1
            return True
        elif "Verw." in real_start_tag:
            # Verw.
            num_id, city, street, street_number, additional_info = cf.parse_id_location(origpost_red)

            # add stuff to ef
            only_add_if_value = True
            self.ef.add_to_my_obj("numID", num_id, object_number=element_counter, only_filled=only_add_if_value)
            self.ef.add_to_my_obj("city", city, object_number=element_counter, only_filled=only_add_if_value)
            self.ef.add_to_my_obj("street", street, object_number=element_counter, only_filled=only_add_if_value)
            self.ef.add_to_my_obj("street_number", street_number, object_number=element_counter,
                                  only_filled=only_add_if_value)
            self.ef.add_to_my_obj("additional_info", additional_info, object_number=element_counter,
                                  only_filled=only_add_if_value)

            return True
        else:
            # Verwaltung
            final_items = cf.parse_general_and_keys(content_texts,
                                                    join_separated_lines=False,
                                                    current_key_initial_value="General_Info")
            for key in final_items.keys():
                value = final_items[key]
                if value is None or value == "":
                    continue
                self.ef.add_to_my_obj(key, value, object_number=element_counter, only_filled=True)
                element_counter += 1
            return True

    def parse_telefon_fernruf(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):

        # get basic data
        origpost, origpost_red, element_counter, content_texts = self.add_check_element(content_texts,
                                                                         real_start_tag, segmentation_class, 0)

        # substitute in a seperator char to integrate delimiters in next step
        origpost_red = regex.sub(r"(\d\.)", r"\1~~~~", origpost_red)

        # do  matches (sc-separated)
        split_post = regex.split(';|~~~~|\su\.', origpost_red)

        for index, entry in enumerate(split_post):
            entry_stripped = entry.strip()
            if entry_stripped == "":
                continue

            match_word = regex.match(r"(?<Tag>\D*)"
                                     r"(?<Numbers>[\d\s\W]*)"
                                     ,entry_stripped)
            if match_word is not None:
                tag = dh.strip_if_not_none(match_word.group("Tag"),"")
                match_tag = regex.match(r"(?<rest_bef>.*)(?<sanr>Sa\.?\-Nr\.?)(?<rest_end>.*)", tag)
                location = ""
                if match_tag is not None:
                    rest_tag = match_tag.group('rest_bef')
                    rest_tag_2 = match_tag.group('rest_end')
                    # sanr = match_tag.group('sanr') # this is the filtered group
                    location = dh.strip_if_not_none(rest_tag +" "+rest_tag_2,"., ")
                number = dh.strip_if_not_none(match_word.group("Numbers"), "., ")
                self.ef.add_to_my_obj("number_Sa.-Nr.", number, object_number=element_counter)
                self.ef.add_to_my_obj("location", location, object_number=element_counter)
                element_counter += 1



    def parse_vorstand(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):

        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            self.add_check_element(content_texts, real_start_tag, segmentation_class, element_counter)

        # do  matches (;-separated)
        split_post = origpost_red.split(';')

        for index, entry in enumerate(split_post):
            entry_stripped = entry.strip()
            match = regex.match(r"(?<Name>.*)[,]"             # find location string
                                r"(?<Rest>.*+)",              # just get the rest which is usually streetname and number, but has other possibilities
                                entry_stripped)
            if match is None:
                continue

            name = dh.strip_if_not_none(match.group("Name"), ", ")
            rest = dh.strip_if_not_none(match.group("Rest"), ",. ")
            name_split = name.split(',')
            if len(name_split) > 1:
                position = rest
                name = name_split[0]
                city = name_split[1]
            else:
                city = rest
                position = ""

            self.ef.add_to_my_obj("name", name, object_number=element_counter)
            self.ef.add_to_my_obj("city", city, object_number=element_counter)
            self.ef.add_to_my_obj("position", position, object_number=element_counter)

            element_counter += 1

        return True

    def parse_aufsichtsrat(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):

        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            self.add_check_element(content_texts, real_start_tag, segmentation_class, element_counter)

        persons_final = cf.parse_persons(origpost_red)
        only_add_if_filed = True
        for entry in persons_final:
            name, city, title, rest_info = entry
            self.ef.add_to_my_obj("name", name, object_number=element_counter, only_filled= only_add_if_filed)
            self.ef.add_to_my_obj("city", city, object_number=element_counter, only_filled= only_add_if_filed)
            self.ef.add_to_my_obj("title", title, object_number=element_counter, only_filled= only_add_if_filed)
            self.ef.add_to_my_obj("rest", rest_info, object_number=element_counter, only_filled= only_add_if_filed)
            element_counter += 1

        return True

    def parse_arbeitnehmervertreter(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            self.add_check_element(content_texts, real_start_tag, segmentation_class, element_counter)

        persons_final = cf.parse_persons(origpost_red)
        only_add_if_filed = True
        for entry in persons_final:
            name, city, title, rest_info = entry
            self.ef.add_to_my_obj("name", name, object_number=element_counter, only_filled= only_add_if_filed)
            self.ef.add_to_my_obj("city", city, object_number=element_counter, only_filled= only_add_if_filed)
            self.ef.add_to_my_obj("title", title, object_number=element_counter, only_filled= only_add_if_filed)
            self.ef.add_to_my_obj("rest", rest_info, object_number=element_counter, only_filled= only_add_if_filed)
            element_counter += 1

        return True

    # Gruendung
    def parse_gruendung(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            self.add_check_element(content_texts, real_start_tag, segmentation_class, element_counter)

        year = dh.strip_if_not_none(origpost_red, ".,\s")
        self.ef.add_to_my_obj("year", year, object_number=element_counter, only_filled=True)


    # Tätigkeitsgebiet
    def parse_taetigkeitsgebiet(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            self.add_check_element(content_texts, real_start_tag, segmentation_class, element_counter)

        final_items = cf.parse_general_and_keys(content_texts,
                                                join_separated_lines=False,
                                                current_key_initial_value="General_Info")

        for key in final_items.keys():
            value = final_items[key]
            if value is None or value == "":
                continue
            self.ef.add_to_my_obj(key, value, object_number=element_counter, only_filled=True)
            element_counter += 1