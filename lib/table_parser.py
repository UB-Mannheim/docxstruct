import numpy as np
import regex
from akf_corelib.configuration_handler import ConfigurationHandler

class TableRegex(object):
    """Compiled regex pattern for TP"""
    def __init__(self):
        self.assets_stop = regex.compile(r"(?:" + "kaptial|Passiva" + "){e<=" + str(2) + "}")
        self.columnheader = regex.compile(r"\d\d[- /.]\d\d[- /.]\d\d\d\d|\d\d\d\d\/\d\d|\d\d\d\d")
        self.balancetype = regex.compile(r"(?:" + "Aktiva|Passiva" + "){e<=" + str(2) + "}")

class TableInfo(object):
    """Helper dataclass - Information storage for TP"""
    def __init__(self, toolbbox=None, regexdict=None):
        self.start = False
        self.row = ""
        self.col = None
        self.lborder = None
        self.fst_order = None
        self.maxgap = 0
        self.nrow = None
        self.lidx = 0
        self.widx = 0
        self.gapidx = -1
        self.separator = None
        self.rborder = None
        self.balancetype = "Aktiva"
        self.currency = False
        self.toolbbox = toolbbox
        self.regex = TableRegex()
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
        self.info = TableInfo(toolbbox)

    ###### ANALYSE ######
    def analyse_structure(self, content_lines, feature_lines, template="datatable"):
        """Analyse the structure of table with the help from the template information and extract some necessary parameter"""
        if template in ["datatable", "datatable_money"]:
            for content, features in zip(content_lines, feature_lines):
                # Append the default values to the structure list
                self._append_defaults(content)
                # Checks if any text was recognized
                if isinstance(features, bool):
                    continue
                # Checks if line is evaluable
                self._check_evaluability(content,features)
                # Checks the current balance type (asset or liabilities)
                self._check_balancetype(content)
                # Iterate over all words and search for valid separator values
                self._find_separator(features, content)
        self.info.start = False
        return

    def _append_defaults(self, content):
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
        if self.info.balancetype == "Aktiva" and self.info.regex.assets_stop.search(content["text"]) is not None:
            self.info.balancetype = "Passiva"
            self.structure["btype"][-1] = self.info.balancetype
        return self.info.balancetype

    def _check_evaluability(self, content, features):
        if features.counters_alphabetical_ratios[features.counter_words - 1] < 0.5 or any([True for char in content["text"][:-2] if char.isdigit()]):
            self.structure["eval"][-1] = True
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
                self.structure["separator"][-1] = int(((content["words"][maxgap + 1]['hocr_coordinates'][3] -
                                                            content["words"][maxgap + 1]['hocr_coordinates'][1]) +
                                                           content["words"][maxgap]['hocr_coordinates'][2]))
                self.structure["gapsize"][-1] = int(xgaps[maxgap])
                self.structure["gapidx"][-1] = maxgap
            self._vali_date(features, content)
        return

    def _vali_date(self, features, content:dict):
        """Checks if the string contains a valid date"""
        if features.counter_numbers > 5 and \
                (features.counter_alphabetical < 3 or self.info.regex.balancetype.search(content["text"]) is not None) and \
                self.info.regex.columnheader.search(content["text"]):
            self.structure["date"][-1] = True
            self.info.start = True
        return


    ###### EXTRACT ######
    def extract_content(self, content_lines:list, feature_lines:list, template="datatable"):
        """Extracts the table information in a structured manner in a the 'content'-dict with the analyse information"""
        self.info.nrow = len(feature_lines)
        # get the col header from date lines
        startidx = self._columnheader(content_lines)
        self.info.start = True
        next_date = list(np.nonzero(self.structure["date"][startidx:])[0])
        if not next_date:
            next_date = self.info.nrow
        else:
            next_date = next_date[0]+startidx
        self.info.separator = int(np.median(self.structure["separator"][startidx:next_date]))
        for lidx, [entry, features] in enumerate(zip(content_lines, feature_lines)):
            self.info.lidx = lidx
            if entry["text"] == "" or lidx < startidx:
                continue
            # read the number of columns the currency of the attributes
            if self.info.lborder is None or self.structure["date"][lidx] and self.info.fst_order is not None:
                idx = np.argmax(self.structure["next_section"][lidx:])
                offset = 2
                if lidx+idx+2 > len(self.structure["date"]) or self.structure["date"][lidx+1] is True:
                    offset = 1
                self.info.lborder = min(self.structure["lborder"][lidx+idx:lidx+idx+offset])
                self.info.fst_order = self.info.lborder+int((entry["hocr_coordinates"][3]-entry["hocr_coordinates"][1])*0.25)
                self.info.rborder = max(self.structure["rborder"][lidx+idx:lidx+idx+offset])
            if self.info.fst_order is not None and self.info.fst_order < entry["words"][0]["hocr_coordinates"][0]:
                self.structure["order"][lidx] = 2
            # If no date was found in the beginning..
            """
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
                    for idx in range(0,len(self.info.col)):
                        if "DM" in entry["text"].replace(" ", "") and "1000" in entry["text"].replace(" ", ""):
                            entry["text"] = "in 1000 DM"
                        else:
                            entry["text"] = entry["text"].replace("(", "").replace(")", "")
                            for btype in set(self.structure["btype"]):
                                self.content[btype][idx]["currency"] = entry['text']
                        self.info.start = True
                self.info.row = ""
            """
            if self.info.start is True:
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
                extractlevel = "bbox"
                if not (self.structure["separator"][lidx]-self.structure["gapsize"][lidx]/2) < self.info.separator < (self.structure["separator"][lidx]+self.structure["gapsize"][lidx]/2):
                    extractlevel = "text"
                # Get the content in structured manner
                self._extract_content(entry, features, extractlevel)
                self.info.row = ""
        return

    def _columnheader(self, content_lines) -> int:
        """"Helper to find the column headers"""
        lines = np.nonzero(self.structure["date"])[0].tolist()
        if not lines:
            self.info.col = [0,1]
            self._additional_columninfo("")
            separator_idx = np.argwhere(np.array(self.structure["separator"]) > -1)[0].tolist()
            if separator_idx is not None and \
                    separator_idx[0] < 5:
                return separator_idx[0]
            else:
                return 3
        for line in lines:
            self.info.col = content_lines[line]['text'].replace("+)", "").strip().split(" ")
            if len(self.info.col) == 2:
               break
        else:
            for line in lines:
                result = self.info.regex.columnheader.findall(content_lines[line]['text'])
                if result is not None:
                    self.info.col = result
                    break
            else:
                self.info.col = [0,1]
        #Todo check if only one column..
        if len(lines) > 1:
            for line in lines[1:]:
                if line <= lines[0]+2:
                    lines[0] = line
        if lines[0] < 5:
            nextitem = np.argwhere(self.structure["next_section"])[0].tolist()
            if nextitem is not None and lines[0]+2 <= nextitem[0]:
                self._additional_columninfo(content_lines[lines[0]+1]['text'])
                return lines[0]+2
            else:
                self._additional_columninfo("")
                return lines[0]+1
        else:
            self._additional_columninfo("")
        return 0

    def _additional_columninfo(self, infotext):
        infotext = infotext.replace("(", "").replace(")", "")
        if "DM" in infotext.replace(" ", "") and "1000" in infotext.replace(" ", ""):
            infotext = "in 1000 DM"
        for btype in set(self.structure["btype"]):
            self.content[btype] = {}
            for col in range(0,len(self.info.col)):
                self.content[btype][col] = {}
                if self.info.col != [1, 0]:
                    self.content[btype][col]["date"] = self.info.col[col]
                self.content[btype][col]["currency"] = infotext

    def _extract_content(self,entry, features, extractlevel) -> bool:
        if extractlevel == "bbox":
            result = self._extract_bboxlevel(entry,features)
        else:
            result = self._extract_textlevel(entry,features)
        return result

    def _extract_bboxlevel(self, entry, features)->bool:
        """"Helper to extract the line information by word bounding box information (default algorithm)"""
        self.content[self.structure["btype"][self.info.lidx]][0][self.info.row] = []
        self.content[self.structure["btype"][self.info.lidx]][1][self.info.row] = []
        for idx in range(0, self.structure["gapidx"][self.info.lidx]+1):
            self.content[self.structure["btype"][self.info.lidx]][0][self.info.row].append(''.join([i for i in ''.join(entry['words'][idx]["text"]) if i.isdigit() or i == " "]))
        self.content[self.structure["btype"][self.info.lidx]][0][self.info.row]= " ".join(self.content[self.structure["btype"][self.info.lidx]][0][self.info.row]).strip()
        for idx in range(self.structure["gapidx"][self.info.lidx]+1, len(entry["words"])):
            self.content[self.structure["btype"][self.info.lidx]][1][self.info.row].append(entry['words'][idx]["text"])
        self.content[self.structure["btype"][self.info.lidx]][1][self.info.row] = " ".join(self.content[self.structure["btype"][self.info.lidx]][1][self.info.row]).strip()
        return True

    def _extract_textlevel(self, entry, features)->bool:
        """"Helper to extract the line information on textlevel (fallback algortihm)"""
        numbers = ''.join([i for i in entry['text'] if i.isdigit() or i == " "]).strip().split(" ")
        # Check if line is date
        if features.counter_alphabetical < 2 and features.counter_special_chars > 3 and features.counter_numbers > 10:
            return False
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
                    return True
        return True

    def _valid_text(self,toolbbox,bbox=[0, 0, 170, 60]):
        toolbbox.imread("/media/sf_ShareVB/many_years_firmprofiles/long/1957/0140_1957_hoppa-405844417-0050_0172bbox_30_40_400_500.jpg")
        toolbbox.snip(bbox)
        # toolbbox.store_bbox("/media/sf_ShareVB/many_years_firmprofiles/long/1957/")
        ocresult = toolbbox.snippet_to_text()
        return

