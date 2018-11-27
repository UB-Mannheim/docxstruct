from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from .akf_parsing_functions_one import AkfParsingFunctionsOne
from .akf_parsing_functions_two import AkfParsingFunctionsTwo
from .akf_parsing_functions_three import AkfParsingFunctionsThree
from .akf_parsing_functions_jk import AkfParsingFunctionsJK

from .akf_parsing_functions_tables_one import AkfParsingFunctionsTablesOne

from .data_helper import DataHelper
from .segment_parser_endobject_factory import EndobjectFactory
from lib.data_helper import DataHelper as dh
from lib.snippet_ocr import Snippet
import glob
import os


class FunctionMapAKF(object):
    """
    This is a holder class which maps segment
    tags to parsing functions (here for AKF-Projekt)
    can be swapped for other projects
    """

    def __init__(self, endobject_factory, output_analyzer):
        self.ef = endobject_factory
        self.akf_one = AkfParsingFunctionsOne(endobject_factory, output_analyzer)
        self.akf_two = AkfParsingFunctionsTwo(endobject_factory, output_analyzer)
        self.akf_three = AkfParsingFunctionsThree(endobject_factory, output_analyzer)
        self.akf_jk = AkfParsingFunctionsJK(endobject_factory, output_analyzer)

        self.akf_tables_one = AkfParsingFunctionsTablesOne(endobject_factory, output_analyzer)

        # for the keys use the keys from 'akf_segment_holder' or similar

        self.function_map = {
            "Firmenname": self.akf_one.parse_firmenname,
            "Sitz": self.akf_one.parse_sitz,
            "Verwaltung": self.akf_one.parse_verwaltung,
            "Telefon/Fernruf": self.akf_one.parse_telefon_fernruf,
            "Vorstand": self.akf_one.parse_vorstand,
            "Aufsichtsrat": self.akf_one.parse_aufsichtsrat,
            "Gründung": self.akf_one.parse_gruendung,
            "Arbeitnehmervertreter": self.akf_one.parse_arbeitnehmervertreter,
            "Tätigkeitsgebiet": self.akf_one.parse_taetigkeitsgebiet,
            "Zahlstellen": self.akf_two.parse_zahlstellen,
            "Grundkapital": self.akf_two.parse_grundkapital,
            "OrdnungsNrAktien": self.akf_two.parse_ordnungsnrdaktien,
            "Großaktionär": self.akf_two.parse_grossaktionaer,
            "Geschäftsjahr": self.akf_two.parse_geschaeftsjahr,
            "StimmrechtAktien": self.akf_two.parse_stimmrechtaktien,
            "Börsennotiz": self.akf_two.parse_boersennotiz,
            "Stückelung": self.akf_two.parse_stueckelung,
            "Aktienkurse": self.akf_jk.parse_aktienkurse,
            "Dividenden": self.akf_tables_one.parse_dividenden, # is table
            "DividendenAufXYaktien": self.akf_tables_one.parse_dividenden_auf_xyaktien, # is table
            "BeratendeMitglieder": self.akf_three.parse_beratende_mitglieder,           # not in first 500 files 1956??
            "Sekretäre": self.akf_three.parse_sekretaere,                               # not in first 500 files 1956??
            "Geschäftsleitung": self.akf_three.parse_geschaeftsleitung,                 # not in first 500 files 1956??
            "Generaldirektion": self.akf_three.parse_generaldirektion,                  # not in first 500 files 1956??
            "Direktionskomitee": self.akf_three.parse_something,                        # not in first 500 files 1956??
            "Vizegeneraldirektoren": self.akf_three.parse_something,                    # not in first 500 files 1956??
            "Fernschreiber": self.akf_three.parse_fernschreiber,
            "Filialen": self.akf_three.parse_filialen,                                  # not a category in 1956 -> #todo maybe use later
            "Auslandsvertretungen": self.akf_three.parse_auslandsvertretungen,          # not a category in 1956 -> #todo maybe use later
            "KommanditeUndBank": self.akf_three.parse_kommandite_und_bank,              # not a category in 1956 -> #todo maybe use later
            "Niederlassungen": self.akf_three.parse_niederlassungen,
            "Erzeugnisse": self.akf_three.parse_erzeugnisse,
            "Haupterzeugnisse": self.akf_three.parse_haupterzeugnisse,
            "Spezialitäten": self.akf_three.parse_spezialitaeten,
            "Anlagen": self.akf_three.parse_anlagen,
            "Zweigniederlassungen": self.akf_three.parse_zweigniederlassungen,
            "Werke/Betriebsstätten": self.akf_three.parse_werke_betriebsstaetten,
            "Betriebsanlagen": self.akf_three.parse_betriebsanlagen,
            "Beteiligungsgesellschaften": self.akf_three.parse_beteiligungsgesellschaften,                # not a category in 1956 -> #todo maybe use later
            "Beteiligungen": self.akf_three.parse_beteiligungen,
            "Tochtergesellschaften": self.akf_three.parse_tochtergesellschaften,
            "Wertpapier-Kenn-Nr": self.akf_three.parse_wertpapier_kenn_nr,              # not a category in 1956 -> #todo maybe use later
            "RechteVorzugsaktien": self.akf_three.parse_rechte_und_vorzugsaktien,
            "Aktionäre": self.akf_three.parse_aktionaere,
            "Anleihen": self.akf_three.parse_anleihen,
            "KursVonZuteilungsrechten": self.akf_three.parse_kurse_v_zuteilungsrechten,
            "Emissionsbetrag": self.akf_three.parse_emissionsbetrag,
            "AusDenKonsolidiertenBilanzen": self.akf_jk.parse_bilanzen,                 # table
            "AusDenBilanzen": self.akf_jk.parse_bilanzen,                               # table
            "Konsolid.Gewinn-u.Verlustrechnungen": self.akf_jk.parse_gewinn_und_verlust,          # table
            "AusGewinnVerlustrechnungen": self.akf_jk.parse_gewinn_und_verlust,                   # @jk last element works now
            "Bezugsrechte": self.akf_three.parse_something,
            "ZurGeschäftslage": self.akf_three.parse_geschaeftslage
        }

    def get_function_map(self):
        return self.function_map




class SegmentParser(object):
    """
    Parse the classified segments segment by segment,
    each segment defined code the parser points to.
    """

    def __init__(self, output_analyzer,ocromore_data=None):

        self.ef = EndobjectFactory()
        # map which maps tags to functions for parsing -> change constuctor for other project
        fmap = FunctionMapAKF(self.ef, output_analyzer)

        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_PARSER, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

        self.function_map = fmap.get_function_map()
        self.result_root = self.config.OUTPUT_ROOT_PATH + "/results/"

    def clear_result(self, output_analyzer,ocromore_data=None):
        # create a new end object factory, new content
        self.ef = EndobjectFactory()
        # map to the new ef object which has been recreated
        fmap = FunctionMapAKF(self.ef, output_analyzer)
        self.function_map = fmap.get_function_map()


    def parse_segments(self, ocromore_data):
        self.ocromore_data = ocromore_data
        segmentation = ocromore_data['segmentation']
        segmentation_classes = segmentation.my_classes

        # add all text from original file if activated (i.e. for debugging purposes)
        if self.config.ADD_FULLTEXT_ENTRY:
            all_texts = self.get_all_text(ocromore_data)
            self.ef.set_current_main_list("overall_info")
            self.ef.add_to_my_obj("fulltexts",all_texts)
        # add a duplicate of the original text from which in the below analysis case the files get subtracted
        if self.config.LOG_SEGMENTED_TO_ORIG_DIFF_PER_FILE:
            if self.config.ADD_FULLTEXT_ENTRY:
                ocromore_data['analysis_to_orig'] = {}
                original_rest, complete_text = self.get_all_text(ocromore_data, join_separated_lines=True)
                ocromore_data['analysis_to_orig']['original_rest'] = original_rest
                ocromore_data['analysis_to_orig']['original_length_initial'] = len(complete_text)
            else:
                self.cpr.printw("activated segment to orig diff, but no saving of origin activate ADD_FULLTEXT_ENTRY "
                                "in config for this functionality")



        #Init toolbbox
        snippet = None
        if self.config.USE_SNIPPET:
            if "./" in self.config.IMGPATH:
                ipath = os.path.dirname(ocromore_data["file_info"].path)+self.config.IMGPATH[1:]
            else:
                ipath = os.path.normcase(self.config.IMGPATH)
            results = glob.glob(ipath+ocromore_data["file_info"].name.split(".")[0].replace("_msa_best","")+"*",recursive=True)
            if results:
                snippet = Snippet()
                snippet.imread(results[0])
            else:
                self.config.USE_TOOLBBOX = False
        info_handler = {}
        # start parsing for each successfully segmented area
        for segmentation_class in segmentation_classes:

            # if the class segment was recognized ...
            if segmentation_class.is_start_segmented():
                # get the unique identifier for this class
                segment_tag = segmentation_class.get_segment_tag()
                segmentation_class.snippet = snippet
                segmentation_class.info_handler = info_handler
                self.trigger_mapped_function(segment_tag, segmentation_class, ocromore_data)


        # add and return result
        ocromore_data['results'] = self.ef
        return ocromore_data

    def trigger_mapped_function(self, segment_tag, segmentation_class, ocromore_data):

        if segment_tag not in self.function_map.keys():
            return
        #todo: fileinfo -> parsing
        real_start_tag, content_texts, content_lines, feature_lines = self.prepare_parsing_info(segmentation_class, ocromore_data)

        # switch the object to save context
        segment_tag = segmentation_class.segment_tag
        self.ef.set_current_main_list(segment_tag)

        # call the mapped function, which fills the end-factory
        self.function_map[segment_tag].__call__(real_start_tag, content_texts, content_lines, feature_lines, segmentation_class)

    def prepare_parsing_info(self, segmentation_class, ocromore_data):
        lines = ocromore_data['lines']
        line_features = ocromore_data['line_features']
        real_start_tag, content_texts, content_lines, feature_lines = \
            DataHelper.get_content(lines,line_features, segmentation_class)

        return real_start_tag, content_texts, content_lines, feature_lines

    def get_all_text(self, ocromore_data, join_separated_lines=False):
        """
        Gets all text lines in ocromore_data as
        array and as joined string
        :param ocromore_data: data from which the text is extracted
        :return: texts list, complete text
        """
        all_texts = []
        complete_text = ""
        for line in ocromore_data['lines']:
            text = line['text']
            all_texts.append(text)
            complete_text += text

        if join_separated_lines:
            complete_text = ""
            all_texts = dh.join_separated_lines(all_texts)
            for text in all_texts:
                complete_text += text

        return all_texts, complete_text

    def write_result_to_output(self, as_json, ocromore_data):
        if as_json is True:
            my_json = self.ef.export_as_json()
            my_json_lines = my_json.split("\n")
            dh.write_array_to_root("result_json/", my_json_lines, ocromore_data, self.result_root)