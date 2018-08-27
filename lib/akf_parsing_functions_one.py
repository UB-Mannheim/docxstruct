from .data_helper import DataHelper as dh
import regex

class AkfParsingFunctionsOne(object):


    @staticmethod
    def parse_sitz(real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        """

        :param real_start_tag:
        :param content_texts:
        :param content_lines:
        :param feature_lines:
        :param segmentation_class:
        :return:

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

        origpost, origpost_red = dh.create_stringified_linearray(content_texts)   # complete text, complete text without \n
        print(real_start_tag, ":", origpost_red)

        type = segmentation_class.segment_tag                       # normed tag

        #                            r"(?::(?<Street>.*?))?"                    # find street string, match lazy cause numbers should be in next group
        #                   r"(?::(?<Number>[0-9]+[-\/]*[0-9]*))?",    # find number with greedy quantifier + optional extension (for e.g. 12-13)


        match = regex.match(r"(?<NumID>\(.*?\))"                 # find starting number (non greedy to stop at first closing parenthesis)
                            r"(?<Location>.*?[,\.]|.*?)"             # find location string
                            r"(?<Rest>.*+)",                     # just get the rest which is usually streetname and number, but has other possibilities
                            origpost_red)
        if match is None:
            print("ok")
            return

        numID = dh.strip_if_not_none(match.group("NumID").strip(), "")
        location = dh.strip_if_not_none(match.group("Location"), "")
        rest = dh.strip_if_not_none(match.group("Rest").strip(), "")

        street = ""
        street_number = ""
        additional_info = ""

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


        #number = match.group("Number")
        print(street,"|" ,street_number)

    @staticmethod
    def parse_verwaltung(real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        print("asd")

"""
class EndobjectFactory(object):

    def __init__(self, segment_tag):
        my_object = {}
        my_object.update(segment_tag,[])
    def create_factory
"""