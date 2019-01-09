from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from .akf_parsing_functions_common import AKFCommonParsingFunctions as cf
from lib.table_parser import Datatable, Sharetable, Dividendtable
import time

def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % \
                  (method.__name__, (te - ts) * 1000))
        return result

    return timed

class AkfParsingFunctionsJK(object):

    def __init__(self, endobject_factory, output_analyzer, dictionary_handler, ocromore_data=None):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_PARSER_AKF_FN_THREE, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

        self.cpr.print("init akf parsing functions three")

        self.ef = endobject_factory
        self.output_analyzer = output_analyzer
        self.ocromore_data = ocromore_data
        self.dictionary_handler = dictionary_handler

    def parse_bilanzen(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # init
        only_add_if_string = True
        if self.config.LOG_SIMPLE:
            geschaeftslage = origpost_red.replace("- ", "")

            #parsing
            self.ef.add_to_my_obj("balances", geschaeftslage, object_number=element_counter,only_filled=only_add_if_string)
            return True
        #parsing
        table = Datatable(snippet=segmentation_class.snippet)
        table.analyse_structure(content_lines,feature_lines, template="datatable_balance")
        table.extract_content(content_lines, feature_lines, template="datatable_balance")

        # Write information for income table parsing
        segmentation_class.info_handler["income"] = {}
        segmentation_class.info_handler["income"]["amount"] = table.info.amount
        segmentation_class.info_handler["income"]["col"] = table.info.col
        segmentation_class.info_handler["income"]["separator"] = table.info.separator

        # Parsing the tables based on whitespace and number of numbers of each group
        # This should be the last option to parse (error-prone)
        self.ef.add_to_my_obj("balances", table.content, object_number=element_counter,only_filled=only_add_if_string)

    def parse_gewinn_und_verlust(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # init
        only_add_if_string = True
        if self.config.LOG_SIMPLE:
            geschaeftslage = origpost_red.replace("- ", "")

            #parsing
            self.ef.add_to_my_obj("income", geschaeftslage, object_number=element_counter,only_filled=only_add_if_string)
            return True

        # parsing
        table = Datatable(snippet=segmentation_class.snippet)
        table.analyse_structure(content_lines, feature_lines, template="datatable_income")
        if segmentation_class.info_handler and "income" in set(segmentation_class.info_handler.keys()):
            table.info.col = segmentation_class.info_handler["income"]["col"]
            table.info.amount = segmentation_class.info_handler["income"]["amount"]
            table.info.separator = segmentation_class.info_handler["income"]["separator"]

        table.extract_content(content_lines, feature_lines, template="datatable_income")


        #parsing
        self.ef.add_to_my_obj("income", table.content, object_number=element_counter,
                              only_filled=only_add_if_string)

    def parse_aktienkurse(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # init
        only_add_if_string = True
        #self.config.LOG_SIMPLE = True
        if self.config.LOG_SIMPLE:
        #    self.config.LOG_SIMPLE = False
            skip = origpost_red.replace("- ", "")

            # parsing
            self.ef.add_to_my_obj("shares", skip, object_number=element_counter,
                                  only_filled=only_add_if_string)
            return True

        # parsing
        table = Sharetable(snippet=segmentation_class.snippet)
        table.analyse_structure(content_lines, feature_lines)
        table.extract_content(content_lines, feature_lines)
        #from timeit import timeit
        #print(timeit(test))
        # parsing
        self.ef.add_to_my_obj("shares", table.content, object_number=element_counter,
                              only_filled=only_add_if_string)

    def parse_dividend(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # init
        only_add_if_string = True
        # self.config.LOG_SIMPLE = True
        if self.config.LOG_SIMPLE:
            #    self.config.LOG_SIMPLE = False
            skip = origpost_red.replace("- ", "")

            # parsing
            self.ef.add_to_my_obj("dividende", skip, object_number=element_counter,
                                  only_filled=only_add_if_string)
            return True

        # parsing
        table = Dividendtable(snippet=segmentation_class.snippet)
        table.analyse_structure(content_lines, feature_lines)
        table.extract_content(content_lines, feature_lines)
        # from timeit import timeit
        # print(timeit(test))
        # parsing
        self.ef.add_to_my_obj("dividende", table.content, object_number=element_counter,
                              only_filled=only_add_if_string)
