from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from .data_helper import DataHelper as dh

import regex


class AkfParsingFunctionsOne(object):

    def __init__(self, endobject_factory):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_PARSER_AKF_FN_ONE, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

        self.cpr.print("init output analysis")

        self.ef = endobject_factory


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
        origpost, origpost_red = dh.create_stringified_linearray(content_texts)   # complete text, complete text without \n
        self.cpr.print(real_start_tag, ":", origpost_red)
        self.ef.add_to_my_obj("origpost", origpost_red, object_number=0)
        self.ef.add_to_my_obj("type", segmentation_class.segment_tag, object_number=0)


        match = regex.match(r"(?<NumID>\(.*?\))"                 # find starting number (non greedy to stop at first closing parenthesis)
                            r"(?<Location>.*?[,\.]|.*?)"         # find location string
                            r"(?<Rest>.*+)",                     # just get the rest which is usually streetname and number, but has other possibilities
                            origpost_red)
        if match is None:
            return False

        numID = dh.strip_if_not_none(match.group("NumID"), "")
        city = dh.strip_if_not_none(match.group("Location"), "")

        # add stuff to ef
        self.ef.add_to_my_obj("numID", numID, object_number=0)
        self.ef.add_to_my_obj("city", city, object_number=0)

        rest = dh.strip_if_not_none(match.group("Rest").strip(), "")


        # parse the rest if there is some
        if rest != "" and rest is not None:
            match_rest = regex.match(r"(?<Street>.*?)"
                                     r"(?<Number>[0-9]+[-\/]*[0-9]*)"
                                     r"(?<Rest>.*+)",
                                     rest)
            if match_rest is not None:
                street = dh.strip_if_not_none(match_rest.group("Street"),"")
                street_number = dh.strip_if_not_none(match_rest.group("Number"),",\.")
                additional_info = dh.strip_if_not_none(match_rest.group("Rest"),"")
                self.ef.add_to_my_obj("street", street, object_number=0)
                self.ef.add_to_my_obj("street_number", street_number, object_number=0)
                self.ef.add_to_my_obj("additional_info", additional_info, object_number=0)

        # optionally print the object for debugging
        # my_obj_done = self.ef.print_me_and_return()
        return True

    def parse_verwaltung(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        my_obj_2 = self.ef.print_me_and_return()
        print("asd")

    def parse_telefon_fernruf(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        my_obj_2 = self.ef.print_me_and_return()
        print("asd")

    def parse_vorstand(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        origpost, origpost_red = dh.create_stringified_linearray(content_texts)   # complete text, complete text without \n
        self.cpr.print(real_start_tag, ":", origpost_red)
        self.ef.add_to_my_obj("origpost", origpost_red, object_number=0)
        self.ef.add_to_my_obj("type", segmentation_class.segment_tag, object_number=0)


        split_post = origpost_red.split(';')

        counter = 0
        for index, entry in enumerate(split_post):
            match = regex.match(r"(?<Name>.*[,\.])"             # find location string
                                r"(?<Rest>.*+)",                     # just get the rest which is usually streetname and number, but has other possibilities
                                entry)
            if match is None:
                continue

            name = dh.strip_if_not_none(match.group("Name"), ",.")
            city = dh.strip_if_not_none(match.group("Rest"), "")
            self.ef.add_to_my_obj("name", name, object_number=counter)
            self.ef.add_to_my_obj("city", city, object_number=counter)

            counter += 1

        self.ef.print_current_main()
        print("asd")




