from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from .data_helper import DataHelper as dh

import regex
import json
import os

class DictionaryHandler(object):

    def __init__(self):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_DICTIONARY_HANDLER, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

        self.cpr.print("init dictionary handler")
        self.data_functs = None # storage for json object
        self.data_titles = None # storage for json object
        self.texts_functs = None
        self.texts_titles = None
        if self.config.USE_DICTIONARIES_FOR_PERSON_PARSING:
            self.load_dictionaries()
            # get the rows as sorted list of texts longest first
            if self.data_functs is not None:
                self.texts_functs = self.sort_rows(self.get_rows(self.data_functs)).reverse()
            if self.data_titles is not None:
                self.text_titles = self.sort_rows(self.get_rows(self.data_titles)).reverse()

    def check_if_has_title(self,text_to_check):
        print("asd")




    def load_dictionaries(self):
        base_dict_path = self.get_dict_path()

        filepath_titles_dict = os.path.join(base_dict_path, "dict_titles.json")
        filepath_functs_dict = os.path.join(base_dict_path, "dict_functs.json")

        # load titles
        if os.path.exists(filepath_titles_dict):
            with open(filepath_titles_dict) as f:
                self.data_titles = json.load(f)
        else:
            self.cpr.printex("dictionary dict_titles.json missing at specificied path",filepath_titles_dict)

        # load functs
        if os.path.exists(filepath_functs_dict):
            with open(filepath_functs_dict) as f:
                self.data_functs = json.load(f)
        else:
            self.cpr.printex("dictionary dict_functs.json missing at specificied path",filepath_functs_dict)


    def get_rows(self, dict_data):
        rows = dict_data['rows']
        final_rows = []
        for entry in rows:
            text = entry[0]
            final_rows.append(text)
        return final_rows

    def sort_rows(self, rows):
        sorted_rows = sorted(rows, key=len)
        return sorted_rows

    def path(self):
        return os.getcwd()

    def get_dict_path(self):
        complete = os.path.join(self.path(),"additionals","dictionaries")
        return complete