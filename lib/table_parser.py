import numpy as np
import regex
from akf_corelib.configuration_handler import ConfigurationHandler

class Tableinfo(object):
    """Helper dataclass - Information storage for tableparsing"""

    def __init__(self, toolbbox=None, regexdict=None):
        self.start = False
        self.row = ""
        self.col = None
        self.lborder = None
        self.maxgap = 0
        self.lidx = 0
        self.widx = 0
        self.gapidx = -1
        self.separator = None
        self.rborder = None
        self.balancetype = "Aktiva"
        self.currency = False
        self.toolbbox = toolbbox
        self.config = ConfigurationHandler(first_init=False).get_config()

class Table(object):
    """This class helps to deal with tables
    - Analyse structure
    - Extract information"""

    def __init__(self, toolbbox=None):
        self.content = {}
        self.structure ={"eval":[],
                         "date":[],
                         "next_section":[],
                         "btype":[],
                         "order": [],
                         "lborder":[],
                         "separator":[],
                         "gapsize":[],
                         "gapidx":[],
                         "rborder":[]}
        self.info = Tableinfo(toolbbox)

    ###### ANALYSE ######
    def analyse_structure(self, content_lines, feature_lines, template="datatable"):
        """Analyse the structure of table with the help from the template information and extract some necessary parameter"""
        if template in ["datatable", "datatable_money"]:
            for content, features in zip(content_lines, feature_lines):
                # Sets the default values to the structure list
                self._set_defaults(content)
                # Checks if any text was recognized
                if isinstance(features, bool):
                    continue
                # Checks if numbers in the line
                self._check_eval(content,features)
                # Checks the current balance type (asset or liabilities)
                self._check_balancetype(content)
                # Iterate over all words and search for valid separator values
                self._find_separator(features, content)
        self.info.start = False
        return

    def _set_defaults(self, content):
        default_dict = {"eval": False,
                        "date": False,
                        "next_section": False,
                        "btype": self.info.balancetype,
                        "order": 0,
                        "separator": -1,
                        "gapsize": -1,
                        "gapidx": -1}

        for param, default in default_dict.items():
            self.structure[param].append(default)
        self.structure["rborder"].append(content["words"][len(content["words"]) - 1]['hocr_coordinates'][2])
        self.structure["lborder"].append(content["words"][0]['hocr_coordinates'][0])
        return

    def _check_balancetype(self, content):
        reg_assets_stop = regex.compile(r"(?:" + "kaptial|Passiva" + "){e<=" + str(2) + "}")
        if not self.info.balancetype == "Aktiva" and reg_assets_stop.search(content["text"]) is not None:
            self.info.balancetype = "Passiva"
            self.structure["btype"][-1] = self.info.balancetype
        return

    def _check_eval(self, content, features):
        if features.counters_alphabetical_ratios[features.counter_words - 1] < 0.5 or any([True for char in content["text"][:-2] if char.isdigit()]):
            self.structure["eval"][-1] = True
        return

    def _vali_date(self, features, content:dict):
        """Checks if the string contains a valid date"""
        reg_col = regex.compile(r"\d\d[- /.]\d\d[- /.]\d\d\d\d|\d\d\d\d\/\d\d|\d\d\d\d")
        reg_assets = regex.compile(r"(?:" + "Aktiva|Passiva" + "){e<=" + str(2) + "}")
        if features.counter_numbers > 5 and \
                (features.counter_alphabetical < 3 or reg_assets.search(content["text"]) is not None) and \
                reg_col.search(content["text"]):
            self.structure["date"][-1] = True
            self.info.start = True
        return

    def _find_separator(self,features, content):
        for widx, wordratio in enumerate(reversed(features.counters_alphabetical_ratios)):
            if wordratio > 0.5:
                if widx >= 1:
                    xgaps = np.append(np.zeros(features.counter_words - widx)[0],
                                      features.x_gaps[features.counter_words - widx:])
                    maxgap = int(np.argmax(xgaps))
                    self.structure["separator"][-1] = int(((content["words"][maxgap + 1]['hocr_coordinates'][3] -
                                                            content["words"][maxgap + 1]['hocr_coordinates'][1]) +
                                                           content["words"][maxgap]['hocr_coordinates'][2]))
                    self.structure["gapsize"][-1] = int(xgaps[maxgap])
                    self.structure["gapidx"][-1] = maxgap
                    if self.info.start is True:
                        self.info.start = False
                        self.structure["next_section"][-1] = True
                        # if the line contains min. 5 number and less than 3 alphabetical or "Aktiva/Passiva"
                    self._vali_date(features, content)
                return
            elif widx == len(features.counters_alphabetical_ratios) - 1 and widx >= 1:
                if widx > 1 and widx + 1 < features.counter_words:
                    xgaps = np.append(np.zeros(features.counter_words - widx - 1)[0],
                                      features.x_gaps[features.counter_words - widx - 1:])
                else:
                    xgaps = [features.x_gaps[0]]
                maxgap = int(np.argmax(xgaps))
                self.structure["separator"][-1] = int((content["words"][maxgap + 1]['hocr_coordinates'][0] +
                                                       content["words"][maxgap]['hocr_coordinates'][2]) / 2)
                self.structure["gapsize"][-1] = int(xgaps[maxgap])
                self.structure["gapidx"][-1] = maxgap
            self._vali_date(features, content)
        return


    ###### EXTRACT ######
    def extract_content(self, content_lines:list, feature_lines:list, template="datatable"):
        """Extracts the table information in a structured manner in a the 'content'-dict with the analyse information"""
        # get the colnames from date lines
        self._find_colname(content_lines)
        for btype in set(self.structure["btype"]):
            self.content[btype] = {}
            for col in range(0, len(self.info.col)):
                self.content[btype][col] = {}
        for lidx, [entry, features] in enumerate(zip(content_lines, feature_lines)):
            if entry["text"] == "":
                continue
            self.info.lidx = lidx
            btype = self.structure["btype"][lidx]
            # read the number of columns the currency of the attributes
            if self.info.start is True and self.info.lborder is None:
                offset = 2
                if self.structure["date"][lidx+1] is False:
                    offset = 1
                self.info.lborder = min(self.structure["lborder"][lidx:lidx+offset])
                self.info.rborder = max(self.structure["rborder"][lidx:lidx+offset])
            # If no date was found in the beginning..
            if self.info.start is False and self.structure["eval"][lidx] is True and any(self.structure["date"][:3]) is False:
                self.info.separator = self.structure['separator'][lidx]
                for btype in set(self.structure["btype"]):
                    for col in range(0,2):
                        self.content[btype][col] = {}
                self.info.col = [0,1]
                self.info.start = True
            # Search for date and currency
            if self.info.start is False:
                # Get new separator value
                if self.structure["date"][lidx] is True:
                    self.info.col = entry['text'].replace("+)","").strip().split(" ")
                    if len(entry['words']) == 1:
                        self.info.col = [self.info.col[:],self.info.col[:]]
                    if len(entry['words']) == 2:
                        self.info.separator = self.structure['separator'][lidx]
                    else:
                        for next in range(lidx+2,len(self.structure["eval"])-1):
                            if self.structure['separator'][next] != -1:
                                self.info.separator = self.structure['separator'][lidx]
                                break
                    for idx, dates in enumerate(self.info.col):
                        # Count the coloumns 0,1,2,...
                        if template in ["datatable","datatable_money"]:
                            for btype in set(self.structure["btype"]):
                                self.content[btype][idx] = {'date': dates}
                            self.info.currency = True
                elif self.info.currency:
                    #todo: fix for loop
                    for idx in [0,1]:
                        if "DM" in entry["text"].replace(" ", "") and "1000" in entry["text"].replace(" ", ""):
                            entry["text"] = "in 1000 DM"
                        else:
                            entry["text"] = entry["text"].replace("(", "").replace(")", "")
                            for btype in set(self.structure["btype"]):
                                self.content[btype][idx]["currency"] = entry['text']
                        self.info.start = True
                self.info.row = ""
            elif self.info.start is True:
                if features.counter_numbers < 2:
                    self.info.row = ''.join(
                        [i for i in entry['text'] if i not in list("()")]).strip() + " "
                    continue
                self.info.row += ''.join([i for i in entry['text'] if i not in list("0123456789()")]).strip()
                self.info.row = self.info.row.replace("- ", "")
                if self.structure["date"][lidx] is True:
                    self.info.separator = self.structure["separator"][lidx]
                    self.info.row = ""
                    continue
                if (self.structure["separator"][lidx]-self.structure["gapsize"][lidx]/2) < self.info.separator < (self.structure["separator"][lidx]+self.structure["gapsize"][lidx]/2):
                    self._extract_wwboxlevel(entry, features)
                else:
                    self._extract_wordlevel(entry, features)
                self.info.row = ""
        return

    def _find_colname(self, content_lines):
        """"Helper to find the column names"""
        reg_col = regex.compile(r"\d\d[- /.]\d\d[- /.]\d\d\d\d|\d\d\d\d\/\d\d|\d\d\d\d")
        lines = np.argwhere(self.structure["date"])
        if lines is None:
            self.info.col = [0,1]
            return
        for line in lines:
            self.info.col = content_lines[line[0]]['text'].replace("+)", "").strip().split(" ")
            if len(self.info.col) == 2:
               return
        for line in lines:
            result = reg_col.findall(content_lines[line[0]]['text'])
            if result is not None:
                self.info.col = result
                return
        self.info.col = [0,1]
        return

    def _extract_wwboxlevel(self, entry, features):
        """"Helper to extract the line information by word bounding box information (default algorithm)"""
        self.content[self.structure["btype"][self.info.lidx]][0][self.info.row] = []
        self.content[self.structure["btype"][self.info.lidx]][1][self.info.row] = []
        for idx in range(0, self.structure["gapidx"][self.info.lidx]+1):
            self.content[self.structure["btype"][self.info.lidx]][0][self.info.row].append(''.join([i for i in ''.join(entry['words'][idx]["text"]) if i.isdigit() or i == " "]))
        self.content[self.structure["btype"][self.info.lidx]][0][self.info.row]= " ".join(self.content[self.structure["btype"][self.info.lidx]][0][self.info.row]).strip()
        for idx in range(self.structure["gapidx"][self.info.lidx]+1, len(entry["words"])):
            self.content[self.structure["btype"][self.info.lidx]][1][self.info.row].append(entry['words'][idx]["text"])
        self.content[self.structure["btype"][self.info.lidx]][1][self.info.row] = " ".join(self.content[self.structure["btype"][self.info.lidx]][1][self.info.row]).strip()
        return

    def _extract_wordlevel(self, entry, features):
        """"Helper to extract the line information on textlevel (fallback algortihm)"""
        numbers = ''.join([i for i in entry['text'] if i.isdigit() or i == " "]).strip().split(" ")
        # Check if line is date
        if features.counter_alphabetical < 2 and features.counter_special_chars > 3 and features.counter_numbers > 10:
            return
        count_years = len(self.info.col) - 1
        count_numbers = 0
        number = ""
        for grpidx, numbergrp in enumerate(reversed(numbers)):
            # Check and clean artifacts
            count_numbers += len(numbergrp)
            if len(numbergrp) > 3 and grpidx > 0:
                if numbergrp[3:] == list(reversed(numbers))[grpidx - 1][:len(numbergrp[3:])]:
                    numbergrp = numbergrp[:3]
            if len(numbergrp) == 3 and grpidx != len(numbers) and count_numbers < (
                    features.counter_numbers / 2):
                number = (numbergrp + " " + number).strip()
                continue
            else:
                count_numbers = 0
                self.content[self.structure["btype"][self.info.lidx]][count_years][self.info.row] = (numbergrp + " " + number).strip()
                number = ""
                count_years -= 1
                if count_years == 0:
                    self.content[self.structure["btype"][self.info.lidx]][count_years][self.info.row] = " ".join(numbers[:len(numbers) - grpidx - 1])
                    return
        return

    def _valid_text(self,toolbbox,bbox=[0, 0, 170, 60]):
        toolbbox.load_image("/media/sf_ShareVB/many_years_firmprofiles/long/1957/0140_1957_hoppa-405844417-0050_0172bbox_30_40_400_500.jpg")
        toolbbox.snip_bbox(bbox)
        # toolbbox.store_bbox("/media/sf_ShareVB/many_years_firmprofiles/long/1957/")
        toolbbox.ocr_snippet()
        return

