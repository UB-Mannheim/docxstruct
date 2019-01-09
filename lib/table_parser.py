import numpy as np
import regex
from akf_corelib.configuration_handler import ConfigurationHandler
import glob
import json
from skimage import filters, color, measure, io
from PIL import ImageDraw
import logging
from scipy import stats, signal

class Table(object):
    """This class helps to deal with tables
    - Analyse structure
    - Extract information"""

    def __init__(self):
        self.content = {}
        self.structure = {}
        self.info = {}

    ###### ANALYSE ######

    def _check_evaluability(self, content, features):
        if features.counters_alphabetical_ratios[features.counter_words - 1] < 0.5 or \
                any([True for char in content["text"][:-2] if char.isdigit()]):
            self.structure["eval"][-1] = True
        return

    def _del_empty_lines(self, content_lines, feature_lines,delitem):
        delidxs = list(np.argwhere(np.array(self.structure[delitem]) == -1))
        if delidxs:
            for delidx in reversed(delidxs):
                del content_lines[delidx[0]]
                del feature_lines[delidx[0]]
                for skey in self.structure.keys():
                    del self.structure[skey][delidx[0]]
        self.info.start = False

    ###### EXTRACT ######

    def _reocr(self, bbox):
        if self.info and self.info.snippet.crop(bbox):
            if self.info.config.SAVE_SNIPPET:
                self.info.snippet.save(self.info.config.IMAGE_PATH)
            self.info.snippet.to_text()
            return self.info.snippet.text
        return ""

    def _read_dictionary(self,tabletype):
        test = glob.glob(f"{self.info.config.INPUT_TABLE_DICTIONARY}*{tabletype}.json")
        if test:
            with open(test[0], "r") as file:
                self.info.dictionary = json.load(file)
        return

    def var_occurence(self,template):
        if self.info.config.OCCURENCES_TABLETYPE == "all":
            addition = "_"+template
        else:
            addition = ""
        from os import path
        if path.isfile(f'./logs/var_occurences{addition}.json'):
            with open(f'./logs/var_occurences{addition}.json') as f:
                data = json.load(f)
        else:
            data = {}
        for type in self.content:
            if not isinstance(self.content[type][0], str):
                for content_keys in self.content[type][0].keys():
                    if content_keys in data.keys():
                        data[content_keys] += 1
                    else:
                        data[content_keys] = 0
        with open(f'./logs/var_occurences{addition}.json', 'w') as outfile:
            json.dump(data, outfile,indent=4,ensure_ascii=False)
        return

    def logger(self, logname, msg=f'Info: %(message)s'):
        """
        Creates a logging object and returns it
        """
        if self.info.snippet:
            msg = msg + f" - Filename:{self.info.snippet.imgname} "
        else:
            msg = "Fname: Unknown "+msg
        logger = logging.getLogger(logname)
        logger.setLevel(logging.INFO)

        # create the logging file handler
        fh = logging.FileHandler(f"./logs/{logname}.log")

        fmt = msg
        formatter = logging.Formatter(fmt)
        fh.setFormatter(formatter)

        # add handler to logger object
        logger.addHandler(fh)
        return logger

class DatatableRegex(object):
    """Compiled regex pattern for TP"""

    def __init__(self):
        self.columnheader = regex.compile(r"\d\d[- /.]\d\d[- /.]\d\d\d\d|\d\d\d\d\/\d\d|\d\d\d\d")
        self.notcompleteitemname = regex.compile(r"Beteiligung"+"{e<=" + str(1) + "}")
        self.balancetype = regex.compile(r"(?:" + "Aktiva|Passiva" + "){e<=" + str(2) + "}")
        self.assets_stop = regex.compile(r"(?:" + "kaptial|Passiva" + "){e<=" + str(2) + "}")
        self.assets_stop_exceptions = regex.compile(r"(?:" + "Grundkapital" + "){e<=" + str(2) + "}")
        self.incometype = regex.compile(r"(?:" + "ertrag|erträge|ergebnis|einnahme|erlöse|erlös" + "){e<=" + str(1) + "}")
        self.lastidxnumber = regex.compile(r"(\d|\d.)$")
        self.amount = regex.compile(r"\S?in{e<=" + str(1) + "}.{0,3}\d.?[0|Ö|O]{2,3}")
        self.amountmio = regex.compile(r"\S?in{e<=" + str(1) + "}.Mio")
        self.additional_info = regex.compile(
            r"(^[+][\)]|Bilanzposten|Erinnerungswert|Verlustausweis){e<=" + str(1) + "}")

class DatatableInfo(object):
    """Helper dataclass - Information storage for TP"""

    def __init__(self, snippet=None):
        self.start = False
        self.row = ""
        self.col = None
        self.lborder = None
        self.order = None
        self.fst_order = None
        self.maxgap = 0
        self.nrow = None
        self.lidx = 0
        self.lastmainitem= None
        self.widx = 0
        self.gapidx = -1
        self.separator = None
        self.rborder = None
        self.type = None
        self.amount = None
        self.snippet = snippet
        self.regex = DatatableRegex()
        self.config = ConfigurationHandler(first_init=False).get_config()
        self.dictionary = None

class Datatable(Table):

    def __init__(self, snippet=None):
        Table.__init__(self)
        self.structure = {"eval": [],
                          "date": [],
                          "next_section": [],
                          "type": [],
                          "order": [],
                          "lborder": [],
                          "separator": [],
                          "gapsize": [],
                          "gapidx": [],
                          "rborder": []}
        self.info = DatatableInfo(snippet)

    ###### ANALYSE ######
    def analyse_structure(self, content_lines, feature_lines, template="datatable"):
        """Analyse the structure of table with the help from the template information and extract some necessary parameter"""
        if template == "datatable_balance":
            self.info.type = "Aktiva"
        if template == "datatable_income":
            self.info.type = "Verlust"
        for content, features in zip(content_lines, feature_lines):
            # Append the default values to the structure list
            self._append_defaults(content, type=self.info.type)
            # Checks if any text was recognized
            if isinstance(features, bool):
                continue
            # Checks if line is evaluable
            self._check_evaluability(content, features)
            # Checks the current template type (balance= Aktiva/Passiva,income=Gewinn/Verlust)
            self._check_type(content, template)
            # Iterate over all words and search for valid separator values (based on bbox)
            if features.counter_numbers > 3:
                self._find_separator(features, content)
        # check if date is over more than one line
        self._check_multiline_date(content_lines)
        # delete unnecassary lines
        self._del_empty_lines(content_lines, feature_lines,"lborder")
        return

    def _append_defaults(self, content, type=None):
        default_dict = {"eval": False,
                        "date": False,
                        "next_section": False,
                        "type": type,
                        "order": 0,
                        "separator": -1,
                        "gapsize": -1,
                        "gapidx": -1}

        for param, default in default_dict.items():
            self.structure[param].append(default)
        if content["text"] == "":
            self.structure["rborder"].append(-1)
            self.structure["lborder"].append(-1)
        else:
            self.structure["rborder"].append(content["words"][len(content["words"]) - 1]['hocr_coordinates'][2])
            self.structure["lborder"].append(content["words"][0]['hocr_coordinates'][0])
        return

    def _check_type(self, content, template):
        if template == "datatable_balance":
            if self.info.type == "Aktiva" and self.info.regex.assets_stop.search(content["text"]) is not None \
                    and not self.info.regex.assets_stop_exceptions.search(content["text"]):
                self.info.type = "Passiva"
                self.structure["type"][-1] = self.info.type
        if template == "datatable_income":
            if self.info.regex.incometype.search(content["text"]) is not None:
                self.structure["type"][-1] = "Gewinn"
        return self.info.type

    def _find_separator(self, features, content):
        for widx, wordratio in enumerate(reversed(features.counters_alphabetical_ratios)):
            if wordratio > 0.5:
                if widx >= 1:
                    if widx != features.counter_words:
                        if content["words"][features.counter_words - widx - 1]["text"][-1].isdigit():
                            widx -= 1
                    xgaps = np.append(np.zeros(features.counter_words - widx),
                                      features.x_gaps[features.counter_words - widx:])
                    maxgap = int(np.argmax(xgaps))
                    self.structure["separator"][-1] = int(((content["words"][maxgap + 1]['hocr_coordinates'][3] -
                                                            content["words"][maxgap + 1]['hocr_coordinates'][1]) +
                                                           content["words"][maxgap]['hocr_coordinates'][2]))
                    self.structure["gapsize"][-1] = int(xgaps[maxgap])
                    self.structure["gapidx"][-1] = maxgap
                    offset = 0
                    if len(content["text"]) > 3:
                        offset = -3
                    # Todo: maybe search for amount to fuzzy?
                    if not self._vali_date(features, content):
                        if self.info.start is True and self.info.regex.lastidxnumber.search(
                                content["text"][offset:]) \
                                and not self.info.regex.amount.findall(content["text"]):
                            self.info.start = False
                            self.structure["next_section"][-1] = True
                            # if the line contains min. 5 number and less than 3 alphabetical or "Aktiva/Passiva"
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

    def _vali_date(self, features, content: dict):
        """Checks if the string contains a valid date"""

        if features.counter_numbers > 5 and \
                (features.counter_alphabetical < 5 or self.info.regex.balancetype.search(content["text"]) is not None) \
                and self.info.regex.columnheader.search(content["text"]):
            self.structure["date"][-1] = True
            self.info.start = True
        return False

    def _check_multiline_date(self,content_lines):
        old_date = None
        for date in list(np.nonzero(np.array(self.structure["date"])))[0]:
            if not old_date:
                old_date = date
                continue
            if self.info.regex.amount.search(content_lines[date]["text"]) or self.info.regex.amountmio.search(content_lines[date]["text"]):
                self.structure["date"][date] = False
                continue
            if date - old_date < 3:
                if not any(self.structure["next_section"][old_date:date + 1]):
                    for idx in range(old_date + 1, date + 1):
                        self.structure["lborder"][idx] = -1

    ##### EXTRACT #####

    def extract_content(self, content_lines: list, feature_lines: list, template="datatable"):
        """Extracts the table information in a structured manner in a the 'content'-dict with the analyse information"""
        if self.info.config.USE_TABLE_DICTIONARY:
            self._read_dictionary(template.split("_")[-1])
        self.info.nrow = len(feature_lines)
        # Get the columnheader information based on date lines
        if not self.info.col or any(self.structure["date"][:4]):
            self.info.separator = None
            startidx = self._columnheader(content_lines)
        else:
            #Todo: Check if there is another way
            if self.info.amount == "":
                self.info.amount = "n.k."
            self._additional_columninfo([], [1,0], infotext=self.info.amount)
            startidx = 2
        self.info.start = True
        next_date = list(np.nonzero(self.structure["date"][startidx:])[0])
        if not next_date:
            next_date = self.info.nrow
        else:
            next_date = next_date[0] + startidx
        # Calculate first separator
        if not self.info.separator:
            if len(self.info.col) > 1:
                if self.info.config.USE_SNIPPET:
                    self.info.separator = self._imgseparator(content_lines, startidx, next_date)
                # Beware of second statement (RLY GOOD CHOICE ONLY FOR "AKTIENFÜHRER")
                separr = [val for val in self.structure["separator"][startidx:next_date] if val > -1]
                if separr and (not self.info.separator or (self.info.separator < 600 and 600< int(np.median(separr)) <800)):
                    self.info.separator = int(np.median([val for val in self.structure["separator"][startidx:next_date] if val > -1]))
            else:
                self.info.separator = int(np.median(self.structure["rborder"]))
        else:
            separatorlist = [val for val in self.structure["separator"][startidx:next_date] if val > -1]
            if separatorlist and abs(self.info.separator-int(np.median(separatorlist))) > 250:
                self.info.separator = self._imgseparator(content_lines, startidx, next_date)
        # Extract content of each line
        for lidx, [entry, features] in enumerate(zip(content_lines, feature_lines)):
            self.info.lidx = lidx
            self.info.order = 1
            if entry["text"] == "" or lidx < startidx:
                continue
            if self.info.regex.additional_info.findall(entry["text"]):
                self.content["additional_info"] = ""
                for info_entry in content_lines[lidx:]:
                    self.content["additional_info"] += info_entry["text"]
                break
            # read the number of columns the currency of the attributes
            if self.info.lborder is None:  # or (self.structure["date"][lidx] and self.info.fst_order is not None):
                idx = np.argmax(self.structure["next_section"][lidx:])
                offset = 2
                if lidx + idx + 2 > len(self.structure["date"]) or self.structure["date"][lidx + 1] is True:
                    offset = 1
                self.info.lborder = min(self.structure["lborder"][lidx + idx:lidx + idx + offset])
                self.info.fst_order = self.info.lborder + int(
                    (entry["hocr_coordinates"][3] - entry["hocr_coordinates"][1]) * 0.25)
                self.info.rborder = max(self.structure["rborder"][lidx + idx:lidx + idx + offset])
            if self.info.fst_order is not None and self.info.fst_order < entry["words"][0]["hocr_coordinates"][0]:
                self.structure["order"][lidx] = 2
            # If no date was found in the beginning..
            if self.info.start is True:
                if features.counter_numbers < 2 and not self.info.regex.lastidxnumber.findall(entry['text']):
                    self.info.row += ''.join(
                        [i for i in entry['text'] if i not in list("()")]).strip() + " "
                    #TODO:control firste regex statement
                    if self.info.regex.notcompleteitemname.search(self.info.row) or (self.info.dictionary and not self._valid_itemname(lidx=lidx)):
                        continue
                else:
                    self.info.row += ''.join([i for i in entry['text'] if i not in list("0123456789()")]).strip()
                    self._valid_itemname(lidx=lidx)
                if self.info.order == 1 and any([True for char in self.info.row if char.isalpha()]):
                    self.info.lastmainitem = self.info.row
                if self.structure["date"][lidx] is True or self.info.row == "":
                    next_sections = list(np.nonzero(self.structure["next_section"][lidx:])[0])
                    if next_sections:
                        next_section = next_sections[0] + lidx
                        offset = (self.info.lborder - min(self.structure["lborder"][next_section:]))
                        self.info.separator -= offset
                        self.info.lborder -= offset
                        self.info.fst_order -= offset
                        self.info.rborder -= offset
                    self.info.row = ""
                    continue
                extractlevel = "bbox"
                if not (self.structure["separator"][lidx] - self.structure["gapsize"][
                    lidx] / 2) < self.info.separator < (
                               self.structure["separator"][lidx] + self.structure["gapsize"][lidx] / 2):
                    extractlevel = "text"
                # Find special cases
                if self.info.row == "ohne Vortrag":
                    if extractlevel == "bbox":
                       entry["words"][0]["text"]= ""
                    else:
                        entry["text"] = entry["text"][8:]
                # Get the content in structured manner
                self._extract_content(entry, features, extractlevel)
                self.info.row = ""

        # Get all var names
        if self.info.config.STORE_OCCURENCES and \
                (template == self.info.config.OCCURENCES_TABLETYPE or "all" == self.info.config.OCCURENCES_TABLETYPE):
            self.var_occurence(template)
        return

    def _columnheader(self, content_lines) -> int:
        """"Helper to find the column headers"""

        lines = np.nonzero(self.structure["date"])[0].tolist()
        if not lines:
            self.info.col = [0, 1]
            self._additional_columninfo(content_lines, [0, 2])
            if sum(self.structure["separator"]) != len(self.structure["separator"])*-1:
                separator_idx = np.argwhere(np.array(self.structure["separator"]) > -1)[0].tolist()
            else:
                return 3
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
                # ONLY VALID if there can be only two coloumns
                if len(result) == 4:
                    result[0] = result[0]+result[1]
                    result[2] = result[2]+result[3]
                    del result[1]
                    del result[len(result)-1]
                if len(result) == 3:
                    if len(result[0]) > len(result[1]):
                        result[1] = result[1]+result[2]
                        del result[2]
                    else:
                        result[0] = result[0]+result[1]
                        del result[1]
                if result is not None:
                    for idx,res in enumerate(result):
                        if len(res) == 8 and "." not in res and "/" not in res:
                            result[idx] = res[:2]+"."+res[2:4]+"."+res[4:]
                    self.info.col = result
                    break
            else:
                self.info.col = [0, 1]
        # Todo check if only one column..
        infotext, offset = self._additional_columninfo(content_lines, (lines[0] - 1, lines[0] + 1, lines[0] + 2))
        return lines[0] + offset

    def _additional_columninfo(self, content_lines, lidxs, infotext=""):
        offset = 1
        if self.info.amount:
            infotext = self.info.amount
        if infotext == "":
            for counter, lidx in enumerate(lidxs):
                if content_lines[lidx]['text'] == "":
                    counter += 1
                    lidx += 1
                amount = self.info.regex.amount.search(content_lines[lidx]['text'])
                if amount:
                    infotext = ("in 1 000 " + "".join([char for char in content_lines[lidx]['text'][amount.regs[0][1]:].replace("8","$").replace("\n","") if not char.isdigit()])).replace("  "," ")
                    offset += counter
                    break
                amountmio = self.info.regex.amountmio.search(content_lines[lidx]['text'])
                if amountmio:
                    infotext = ("in Mio " + "".join([char for char in content_lines[lidx]['text'][amountmio.regs[0][1]:].replace("8","$").replace("\n","") if not char.isdigit()])).replace("  "," ")
                    offset += counter
                    break
            else:
                if not self.structure["next_section"][lidxs[1]]:
                    offset = 2
            if infotext == "" and len(lidxs) > 1:
                # Try to catch amount info with reocr
                reinfo = self._reocr(list(content_lines[lidxs[1]]["hocr_coordinates"]))
                amount = self.info.regex.amount.search(reinfo)
                if amount:
                    infotext = ("in 1 000 " + "".join([char for char in content_lines[lidx]['text'][amount.regs[0][1]:].replace("8","$").replace("\n","") if not char.isdigit()])).replace("  "," ")
                amountmio = self.info.regex.amountmio.search(reinfo)
                if amountmio:
                    infotext = ("in Mio " + "".join([char for char in content_lines[lidx]['text'][amountmio.regs[0][1]:].replace("8","$").replace("\n", "") if not char.isdigit()])).replace("  ", " ")
        for type in set(self.structure["type"]):
            self.content[type] = {}
            for col in range(0, len(self.info.col)):
                self.content[type][col] = {}
                if self.info.col != [1, 0]:
                    self.content[type][col]["date"] = self.info.col[col]
                self.info.amount = infotext.replace("(","").replace(")","")
                self.content[type][col]["amount"] = self.info.amount
        return infotext, offset

    def _extract_content(self, entry, features, extractlevel) -> bool:
        if extractlevel == "bbox":
            result = self._extract_bboxlevel(entry)
        else:
            result = self._extract_textlevel(entry, features)
        return result

    def _extract_bboxlevel(self, entry) -> bool:
        """"Helper to extract the line information by word bounding box information (default algorithm)"""

        self.content[self.structure["type"][self.info.lidx]][0][self.info.row] = []
        self.content[self.structure["type"][self.info.lidx]][1][self.info.row] = []

        for idx in range(0, self.structure["gapidx"][self.info.lidx] + 1):
            self.content[self.structure["type"][self.info.lidx]][0][self.info.row].append(
                ''.join([i for i in ''.join(entry['words'][idx]["text"]) if i.isdigit() or i == " "]))

        fst_num = " ".join(self.content[self.structure["type"][self.info.lidx]][0][self.info.row]).strip()

        for idx in range(self.structure["gapidx"][self.info.lidx] + 1, len(entry["words"])):
            self.content[self.structure["type"][self.info.lidx]][1][self.info.row].append(entry['words'][idx]["text"])

        snd_num = " ".join(self.content[self.structure["type"][self.info.lidx]][1][self.info.row]).strip()

        # Validate the number
        bbox = [val - 5 if pos < 2 else val + 5 for pos, val in enumerate(list(entry["hocr_coordinates"]))]
        fst_num, snd_num = self._valid_num_reocr(fst_num, snd_num, bbox)

        self.content[self.structure["type"][self.info.lidx]][0][self.info.row] = fst_num
        self.content[self.structure["type"][self.info.lidx]][1][self.info.row] = snd_num

        return True

    def _extract_textlevel(self, entry, features) -> bool:
        """"Helper to extract the line information on textlevel (fallback algortihm)"""

        numbers = ''.join([i for i in entry['text'] if i.isdigit() or i == " "]).strip()
        # If one column just parse
        if len(self.info.col) == 1:
            #if self.info.row == "Bilanzsumme":
            #    self.content["Bilanzsumme"][0] = " ".join(numbers)
            #else:
            self.content[self.structure["type"][self.info.lidx]][0][self.info.row] = " ".join(numbers)
            return True

        # First try to solve the problem with reocr the bbox
        if self.info.snippet:
            if self._extract_reocrlevel(entry, numbers):
                return True
        if numbers == "" and self.info.lidx == self.info.nrow-1:
            return False
        numbers = numbers.split(" ")

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
                self.content[self.structure["type"][self.info.lidx]][count_years][self.info.row] = (
                            numbergrp + " " + number).strip()
                number = ""
                count_years -= 1
                if count_years == 0:
                    self.content[self.structure["type"][self.info.lidx]][count_years][self.info.row] = " ".join(
                        numbers[:len(numbers) - grpidx - 1])
                    return True
        return True

    def _extract_reocrlevel(self, entry, numbers):
        if self.info.separator < entry["hocr_coordinates"][2]:
            try:
                bbox = [val - 5 if pos < 2 else val + 5 for pos, val in enumerate(list(entry["hocr_coordinates"]))]
                snd_reocr = self._reocr_num(bbox,0)
                if snd_reocr == "": return False
                if any(True for char in snd_reocr if str(char).isalpha() and str(char).upper() not in ["U", "E", "Y"]): return False
                # Check if the result has more than 2 numbers otherwise compare directly
                if len(snd_reocr)>2:
                    findings = regex.compile(r"(?:" + snd_reocr + "){e<=" + str(1) + "}").findall(numbers)
                else:
                    if numbers[-len(snd_reocr):] == snd_reocr :
                        findings = [snd_reocr]
                    else:
                        findings = None
                if findings:
                    snd_num = findings[-1]
                    fst_num = numbers[:-len(snd_num)]
                    fst_num, snd_num = self._valid_num_reocr(fst_num,snd_num,bbox,snd_alt=snd_reocr)
                    self.content[self.structure["type"][self.info.lidx]][0][self.info.row] = fst_num.strip()
                    self.content[self.structure["type"][self.info.lidx]][1][self.info.row] = snd_num.strip()
                    return True
            except:
                print("Reocr did not work!")
        return False

    def _imgseparator(self, content_lines, startidx, next_date):
        # Find a representativ area of the table
        sections = list(np.nonzero(self.structure["next_section"])[0])
        if sections:
            fst_section = sections[0]
        else:
            fst_section = startidx + 1
        if next_date - fst_section > 3:
            snd_section = fst_section + 3
        else:
            snd_section = next_date - 1
        if snd_section <= fst_section:
            snd_section = fst_section+1
        lborder = min(self.structure["lborder"][fst_section:snd_section + 1])
        rborder = max(self.structure["rborder"][fst_section:snd_section + 1])
        tablebbox = [lborder, content_lines[fst_section]["words"][0]["hocr_coordinates"][1], rborder,
                     content_lines[snd_section - 1]["words"][-1]["hocr_coordinates"][3]]
        # Cut the area out of the image and find the biggest whitespace areas
        if self.info.snippet.crop(tablebbox):
            tableimg = color.rgb2gray(np.array(self.info.snippet.snippet))
            thresh = filters.threshold_otsu(tableimg)
            threshed = tableimg > thresh
            threshed_red = np.sum(threshed, axis=0) > threshed.shape[0] * 0.95
            whitespace = {}
            whitespace["label"] = measure.label(threshed_red)
            whitespace["area"] = np.bincount(whitespace["label"].ravel())
            # Generate list with occurences without black areas and the first left and right area
            whitespace["biggest"] = sorted(whitespace["area"] [2:len(whitespace["area"])-1], reverse=True)[:2]
            if whitespace["biggest"][0] * 0.3 > whitespace["biggest"][1]:
                whitespace["selected"] = whitespace["biggest"][0]
            else:
                whitespace["selected"] = [area for area in whitespace["area"] if area in whitespace["biggest"]][1]
            gapidx = np.argwhere(whitespace["area"] == whitespace["selected"])[-1][0]
            gap = np.nonzero(whitespace["label"] == gapidx)[0]
            separator = int(gap[0] + len(gap) * 0.35)
            if self.info.config.DRAW_SEPARATOR:
                draw = ImageDraw.Draw(self.info.snippet.snippet)
                draw.line((separator,0,separator,threshed.shape[0]),fill=128)
                self.info.snippet.save(self.info.config.IMAGE_PATH)
            return separator + tablebbox[0]
        return None

    def _valid_num_reocr(self, fst_num, snd_num,bbox,fst_alt=None,snd_alt=None):
        if not self._valid_numpattern(fst_num) or abs(len(fst_num)-len(snd_num))>1:
            if fst_alt:
                fst_num = fst_alt
            else:
                reocr_num = self._reocr_num(bbox,2)
                if self._valid_numpattern(reocr_num):
                    fst_num = reocr_num
        if not self._valid_numpattern(snd_num) or abs(len(fst_num)-len(snd_num))>0:
            if snd_alt:
                snd_num = snd_alt
            else:
                reocr_num = self._reocr_num(bbox,0)
                if self._valid_numpattern(reocr_num):
                    snd_num = reocr_num
        return fst_num,snd_num

    def _reocr_num(self,bbox,separator_position):
        """Reocr the number"""

        reocr_bbox = bbox[:]
        reocr_bbox[separator_position] = self.info.separator + 13
        self.info.snippet.crop(reocr_bbox)
        reocr_text = self._reocr(reocr_bbox).replace("\n", "").replace("+)", "").replace("."," ").replace(","," ")
        reocr_num = ''.join([i for i in reocr_text if i.isdigit() or i == " "]).strip()
        return reocr_num

    def _valid_numpattern(self, text):
        """ Validate the number pattern """

        numbergrps = ''.join([i for i in text if i.isdigit() or i == " "]).strip().split(" ")
        for grpidx, numbergrp in enumerate(reversed(numbergrps)):
            if len(numbergrp) > 3 or (grpidx != len(numbergrps)-1 and len(numbergrp) < 3):
                return False
        return True

    def _valid_itemname(self,lidx=None):
        self.info.row = self.info.row.replace("- ", "")
        if "Zusatz" not in self.info.dictionary.keys(): return False
        item = self.info.row
        subitemflag = False
        if len(item) > 3:
            add = ""
            for additive in self.info.dictionary["Zusatz"].keys():
                oldlen = len(item)
                item = item.replace(additive+" ", "")
                if oldlen != len(item) and additive in ["darunter","davon"]:
                    subitemflag = True
                elif oldlen != len(item) and additive not in ["Passiva","Aktiva"]:
                    add += additive+" "
            item = "".join([char for char in item.lower() if char != " "])
            fuzzy_range = len(item)//8
            itemregex = regex.compile(r"^(?:"+regex.escape(item)+"){e<=" + str(fuzzy_range) + "}")
            for itemlvl in ["Unterpunkte","Hauptpunkte"]:
                for itemname in list(self.info.dictionary[itemlvl].keys()):
                    if len(item)-3<len(itemname)<len(item)+3:
                        if itemregex.search(itemname.lower().replace(" ","")):
                            # Check if the last chars are there or if the itemname is split in 2 lines
                            if regex.compile(r"(?:"+regex.escape(item[-4:])+"){e<=" + str(2) + "}").search(regex.escape(itemname.lower().replace(" ","")[-4:])):
                                self.info.row = add+self.info.dictionary[itemlvl][itemname]
                                if subitemflag or (itemlvl == "Unterpunkte" and self.info.lastmainitem and lidx and self.info.fst_order < self.structure["lborder"][lidx]):
                                    if itemname == "Barmittel" and self.info.lastmainitem != "Umlaufvermögen" and self.structure["order"][self.info.lidx] == 1:
                                        self.info.order = 1
                                    if itemname == "Beteiligungen" and self.info.lastmainitem != "Anlagevermögen":
                                        continue
                                    else:
                                        self.info.order = 2
                                        self.info.row = f"{self.info.lastmainitem} ({self.info.row})"
                                return True
        return False

class SharetableRegex(object):
    """Compiled regex pattern for TP"""

    def __init__(self):
        self.date = regex.compile(r"(?:19\d\d)")
        self.alphacurrency= regex.compile(r"(?:\sDM\s){e<=1}")
        self.startingdatereg = regex.compile(r"(?:ab[.\s]\d\d[- /.]\d\d[- /.]\d\d\d\d)")
        self.noticereg = regex.compile(r"(?:(Stücknotiz\sfür\s|per\sStück\szu){e<=2})")
        self.conversion = regex.compile(r"(?:(/+.\sumgerechnet){e<=2})")
        self.addinforeg = regex.compile(r"(?:(/+.\sKurs){e<=2})")
        self.sharetypereg = regex.compile(
            r"(?:(aktien|akt\.|\s[a-z]*\.a\.|Genußscheine|lit\.[\s][a-g]|sch\.|gr\.st\.|kl\.st\.|gruppe\s[a-z]){e<=1}|(\srm\s\d\d\d|\salt\s|\sjung))")
        self.numbergrpreg = regex.compile(r"(?:(\s\d*\s))")
        self.greptable = regex.compile(r"((?P<year>19\d\d|[4-7]\d|19\d\d|[4-7]\d/\d\d)\s*"
                                    r"(?P<amount>\d*[,?|\.?|/?]?\d*|-)[\s]?"
                                    r"(?P<currency>%|DM)?)")
        self.greptable2col = regex.compile(r"((?P<year>19\d\d|[4-7]\d)\s*"
                                    r"(?P<amount1>\d*[,?|\.?|/?]?\d*|-)[\s]?"
                                    r"(?P<currency1>%|DM)\s"
                                    r"(?P<amount2>\d*[,?|\.?|/?]?\d*|-)[\s]?"
                                    r"(?P<currency2>%|DM))")
        self.bracketfinder = regex.compile(r"(?:\(.[^\(]*\))")
        self.closingdate = regex.compile(r"(?:([0-3]\d[\.|,].[^)]{1,4}))")

class SharetableInfo(object):
    """Helper dataclass - Information storage for TP"""

    def __init__(self, snippet=None):
        self.separator = None
        self.start = False
        self.row = ""
        self.col = None
        self.lborder = None
        self.order = None
        self.fst_order = None
        self.subtables = 0
        self.nrow = None
        self.lidx = 0
        self.lastmainitem= None
        self.widx = 0
        self.gapidx = -1
        self.rborder = None
        self.type = None
        self.amount = None
        self.snippet = snippet
        self.regex = SharetableRegex()
        self.config = ConfigurationHandler(first_init=False).get_config()
        self.dictionary = None
        self.notice = ""
        self.closing_date = ""
        self.starting_date = ""
        self.addinfo = None
        self.comment = None
        self.sharetypes = None
        self.sharetypelidx = None
        self.datagroups = None
        self.reocrcount= 0

class Sharetable(Table):
    def __init__(self, snippet=None):
        Table.__init__(self)
        self.structure = {"eval": [],
                          "data": [],
                          "bbox_separator": [],
                          "order": [],
                          "currency":[],
                          "lborder": [],
                          "separator": [],
                          "gapsize": [],
                          "gapidx": [],
                          "rborder": []}
        self.info = SharetableInfo(snippet)

    ##### ANALYSE #####
    def analyse_structure(self, content_lines, feature_lines):
        """Analyse the structure of table with the help from the template information and extract some necessary parameter"""
        for lidx, (content, features) in enumerate(zip(content_lines, feature_lines)):
            self.info.lidx = lidx
            # Append the default values to the structure list
            self._append_defaults(content)
            # Checks if any text was recognized
            if isinstance(features, bool):
                continue
            # Checks if line is evaluable
            self._check_evaluability(content, features)
            # Checks the current template type (balance= Aktiva/Passiva,income=Gewinn/Verlust)
            if lidx > 1 or "RM" not in content["text"]:
                offset = len(self.info.regex.alphacurrency.findall(content["text"]))*2
                #TODO: Special case
                if 'Ratensch.' in content["text"]:
                    offset = 12
                if 'ab' in content["text"][:2]:
                    offset = -5
                if self._check_data(features,addalpha = offset) and \
                        self.info.snippet:
                    self._find_separator(content)
        # delete unnecassary lines
        self._del_empty_lines(content_lines, feature_lines,"lborder")
        return

    def _append_defaults(self, content):
        default_dict = {"eval": False,
                        "data": False,
                        "bbox_separator": False,
                        "currency": None,
                        "order": 0,
                        "separator": None,
                        "gapsize": -1,
                        "gapidx": -1}

        for param, default in default_dict.items():
            self.structure[param].append(default)
        if content["text"] == "":
            self.structure["rborder"].append(-1)
            self.structure["lborder"].append(-1)
        else:
            self.structure["rborder"].append(content["words"][len(content["words"]) - 1]['hocr_coordinates'][2])
            self.structure["lborder"].append(content["words"][0]['hocr_coordinates'][0])
        return

    def _check_data(self, features,addalpha=0):
        if features.counter_alphabetical < 9+addalpha and (features.counter_numbers >= 4 or features.numbers_ratio > 0.8):
            self.structure["data"][-1] = True
            return True
        return False

    def _find_separator(self,content):
        if "DM" in content["text"] or "%" in content["text"]:
            bbox_separator = []
            visual_separator = []
            markerflag = False
            lastwidx = 0
            self.structure["currency"][self.info.lidx]= []
            bbox = list(content["hocr_coordinates"])
            for widx, word in enumerate(content["words"]):
                if self.info.regex.date.search(word["text"]):
                    lastwidx = widx
                    markerflag = True
                elif lastwidx<widx-2 or all(False for char in word["text"] if char.isdigit()):
                    markerflag = False
                if not word["text"] or len(word["text"]) <2: continue
                if word["text"] in ["DM","%"] or word["text"][-1] in ["%"] or word["text"][-2:] in ["DM"]:
                    if markerflag and lastwidx+2==widx:
                        bbox_separator.append([int(np.mean([content["words"][widx-2]["hocr_coordinates"][2],
                            np.mean([content["words"][widx-1]["hocr_coordinates"][0],content["words"][widx-2]["hocr_coordinates"][2]])])),
                                            int(np.mean([word["hocr_coordinates"][0],content["words"][widx-1]["hocr_coordinates"][2]])),
                                            word["hocr_coordinates"][2]])
                        #visual_separator.append([content["words"][widx]["hocr_coordinates"][0],word["hocr_coordinates"][2]])
                        if word["text"][-1] == "%":
                            self.structure["currency"][self.info.lidx].append(["%"])
                        else:
                            self.structure["currency"][self.info.lidx].append(["DM"])
                    bbox[2] = word["hocr_coordinates"][2]
                    visual_separator.append(self._generate_separator(bbox))
                    bbox[0] = bbox[2]
            if not self.info.subtables:
                bbox = list(content["hocr_coordinates"])
                sepfind = regex.compile(r":?(DM|%)")
                #textall = len(sepfind.findall(content["text"]))
                reocr_text = self._reocr(bbox).strip()
                self.info.reocrcount += 1
                reocrall = len(sepfind.findall(reocr_text))
                if len(visual_separator) < reocrall:
                    lineinfo = self.info.snippet.result[0]
                    bbox_separator = []
                    for widx, word in enumerate(lineinfo["words"]):
                        word = word.strip()
                        if self.info.regex.date.search(word):
                            lastwidx = widx
                        if lastwidx+2 <= widx and word in ["DM", "%"] or word[-1] in ["%"] or word[-2:] in ["DM"]:
                            if lastwidx+2 == widx:
                                bbox_separator.append([int(np.mean([lineinfo["bbox"][widx-2][2],
                                                                    np.mean([lineinfo["bbox"][widx - 1][0],
                                                                             lineinfo["bbox"][widx - 2][2]])])),
                                                       int(np.mean([lineinfo["bbox"][widx][0],
                                                                    lineinfo["bbox"][widx - 1][2]])),
                                                                    lineinfo["bbox"][widx][2]])
                            else:
                                bbox_separator.append([int(np.mean([lineinfo["bbox"][widx][2],
                                                                    lineinfo["bbox"][widx - 1][0]])),
                                                       lineinfo["bbox"][widx][0],
                                                       lineinfo["bbox"][widx][2]])
                    for bidx, bbox_sep in enumerate(bbox_separator):
                        for vidx, val in enumerate(bbox_sep):
                            bbox_separator[bidx][vidx] = val+bbox[0]
                    self.info.subtables = reocrall
            if len(visual_separator) > self.info.subtables:
                self.info.subtables = len(visual_separator)
            self.structure["separator"][self.info.lidx] = {"bbox": bbox_separator, "visual": visual_separator}
        return True

    def _generate_separator(self,tablebbox):
        if self.info.snippet.crop(tablebbox):
            tableimg = color.rgb2gray(np.array(self.info.snippet.snippet))
            thresh = filters.threshold_otsu(tableimg)
            threshed = tableimg > thresh
            threshed_red = np.sum(threshed, axis=0) > threshed.shape[0] * 0.95
            whitespace = {}
            whitespace["label"] = measure.label(threshed_red)
            whitespace["area"] = np.bincount(whitespace["label"].ravel())
            # Generate list with occurences without black areas and the first left and right area
            whitespace["biggest"] = sorted(whitespace["area"][2:], reverse=True)[:2]
            if len(whitespace["biggest"])<2:
                return []
            #    whitespace["biggest"] = whitespace["biggest"][:2]
            whitespace["selected"] = [area for area in whitespace["area"] if area in whitespace["biggest"]]
            #draw = ImageDraw.Draw(self.info.snippet.snippet)
            separator = []
            for selected_area in whitespace["selected"]:
                gapidx = np.argwhere(whitespace["area"] == selected_area)[-1][0]
                gap = np.nonzero(whitespace["label"] == gapidx)[0]
                separator.append(int(gap[0] + len(gap) * 0.35))
                #if self.info.config.DRAW_SEPARATOR:
                #draw.line((separator[-1],0,separator[-1],threshed.shape[0]),fill=128)
            #self.info.snippet.save(self.info.config.IMAGE_PATH)
            return [separator[0] + tablebbox[0], separator[1]+tablebbox[0], tablebbox[2]]
        return []

    ##### EXTRACT #####
    def extract_content(self, content_lines: list, feature_lines: list,visual=True,visual_fast=False):
        """Extracts the table information in a structured manner in a the 'content'-dict with the analyse information"""
        self.info.nrow = len(feature_lines)
        # Find sharetypes and additional infos
        self.content = {"Regexdata":{},"Vbboxdata":{},"Sharedata":{},"additional_info":[]}
        self.info.datagroups = [idx+1 for idx, number in enumerate(self.structure["data"][1:]) if number!=self.structure["data"][idx]]
        self.info.datagroups.append(len(self.structure["data"]))
        if len(self.info.datagroups) == 1:
            self.info.datagroups.append(2)
            self.info.datagroups.sort()
        # Get the columnheader information based on date lines
        if self.info.subtables == 0 and self.info.snippet:
            reocr_text = self._reocr(list(content_lines[self.info.datagroups[0]]["hocr_coordinates"])).strip()
            self.info.reocrcount += 1
            if self.info.regex.greptable.search(reocr_text):
                self.logger("Sharetable_Subtables").log(level=20, msg="Subtables were set to 1!")
                self.info.subtables = 1
                for lidx in range(self.info.datagroups[0],self.info.datagroups[1]):
                    content_lines[lidx]["text"] += "%"
                    content_lines[lidx]["words"][-1]["text"] += "%"
            else:
                self.logger("Sharetable_Subtables").log(level=20, msg="Zero subtables were found!")
        for lidx, content in enumerate(content_lines):
            if not self.structure["data"][lidx]:
                if not self._get_information(content, lidx):
                    self.content = {}
                    return False
            else:
                content["text"] = content["text"].replace(":","").replace(" . ","")
                #print(content["text"])
                self._extract_regexlvl(content["text"].strip(),lidx)
        if self.info.snippet and visual:
            if self.info.subtables == 1:
                sharetype = ""
                year_counter = 0
                last_year = ""
                for lidx, content in enumerate(content_lines):
                    year_counter += 1
                    if self.info.sharetypes and lidx in self.info.sharetypes.keys():
                        sharetype = self.info.sharetypes[lidx][0]
                    if self.structure["data"][lidx]:
                        year_findings = self.info.regex.date.search(content["text"])
                        if not year_findings:
                            year_reocr = self._reocr(list(content["hocr_coordinates"])).strip()
                            self.info.reocrcount += 1
                            year_findings = self.info.regex.date.search(year_reocr)
                            content["text"] = year_reocr.replace("1/2",",5").replace("1/4",",25").replace("3/4",",75")
                        if year_findings:
                            year_counter = 0
                            year = content["text"][year_findings.regs[0][0]:year_findings.regs[0][1]]
                            last_year = year
                            valueidx = year_findings.regs[0][1]
                        else:
                            valueidx = 0
                            year = last_year+str(year_counter)
                        if self.info.closing_date == "" and len(self.info.datagroups) >1 and lidx == self.info.datagroups[1::2][-1]-1:
                            if year_findings:
                                self.info.closing_date = content["text"][:year_findings.regs[0][0]]
                        value = content["text"][valueidx:].strip().replace("+)","").replace("T","").replace("G","").split("(")[0]
                        amount = "".join([char for char in value if char.isdigit() and char not in [" ","/",".",","]])
                        if amount == "" or all([False for char in value if char.isdigit()]):
                            continue
                        currency, unit = "", 1
                        if "DM" in value[len(amount):]:
                            currency = "DM"
                        else:
                            unit = "%"
                        self.content["Vbboxdata"][str(lidx)+" "+str(0)] = \
                            {"Year": year,
                             "ClosingDate": self.info.closing_date,
                             "Amount": amount,
                             "Currency": currency,
                             "Unit": unit,
                             "Kind": "ultimo",
                             "Notice": self.info.notice,
                             "Comment": sharetype}
            #if self.info.subtables == 2 and datacount[1]-datacount[0] == 1:
            if self.info.subtables == 2:
                sharetypeidx = None
                for lidx, content in enumerate(content_lines):
                    if self.info.sharetypes and lidx in self.info.sharetypes.keys():
                        sharetypeidx =lidx
                    elif self.info.sharetypes:
                        sharetypeidx = list(self.info.sharetypes.keys())[0]
                    if self.structure["data"][lidx]:
                        year_findings = self.info.regex.date.search(content["text"])
                        if not year_findings:
                            continue
                        year = content["text"][year_findings.regs[0][0]:year_findings.regs[0][1]]
                        if self.info.closing_date == "" and len(self.info.datagroups) > 1 and lidx == self.info.datagroups[1::2][-1]-1:
                            self.info.closing_date = content["text"][:year_findings.regs[0][0]]
                        for sidx,char in enumerate(content["text"][year_findings.regs[0][1]:].replace("+)", "").replace("T","").replace("G", "")):
                            if not char.isdigit() and char not in [" ","/",".",","]:
                                sidx = sidx+2+year_findings.regs[0][1]
                                break
                        else:
                            reocr_text = self._reocr(list(content["hocr_coordinates"])).replace("1/2",",5").replace("1/4",",25").replace("3/4",",75").strip()
                            self.info.reocrcount += 1
                            year_findings = self.info.regex.date.search(reocr_text)
                            if not year_findings:
                               continue
                            else:
                                for sidx, char in enumerate(
                                        reocr_text[year_findings.regs[0][1]:].replace("+)", "").replace("T",
                                                                                                             "").replace(
                                                "G", "")):
                                    if not char.isdigit() and char not in [" ","/",".",","]:
                                        sidx = sidx + 2 + year_findings.regs[0][1]
                                        content["text"] = reocr_text
                                        break
                                else:
                                    sidx = year_findings.regs[0][1]
                        for idxs,cidx in (([year_findings.regs[0][1],sidx],0),([sidx,len(content["text"])],1)):
                            value = content["text"].replace("+)", "").replace("T","").replace("G", "")[idxs[0]:idxs[1]].strip()
                            amount = "".join([char for char in value if char.isdigit() or char in ["/",".",","]])
                            if amount != "" and any([True for char in value if char.isdigit()]):
                                lastdigit = regex.search(r'([0-9])[^0-9]*$', value).regs[1][1]
                            else:
                                continue
                            currency,unit = "", 1
                            if "DM" in value[lastdigit:]:
                                currency = "DM"
                            else:
                                unit = "%"
                            if self.info.sharetypes and len(list(self.info.sharetypes[sharetypeidx].keys())) == 2:
                                sharetype = self.info.sharetypes[sharetypeidx][cidx]
                            else:
                                if cidx==0:
                                    sharetype = "A"
                                else:
                                    sharetype = "B"

                            self.content["Vbboxdata"][str(lidx)+" "+str(cidx)] = \
                                {"Year": year,
                                 "ClosingDate": self.info.closing_date,
                                 "Amount": amount,
                                 "Currency": currency,
                                 "Unit": unit,
                                 "Kind": "ultimo",
                                 "Notice": self.info.notice,
                                 "Comment": sharetype}
            if self.info.subtables == 3:
                if visual_fast:
                    for lidx, content in enumerate(content_lines):
                        if self.structure["data"][lidx]:
                            #print(lidx)
                            bbox = list(content["words"][0]["hocr_coordinates"])
                            bbox[2] = content["words"][-1]["hocr_coordinates"][2]
                            textline = self._reocr(bbox[:]).strip()
                            self._extract_regexlvl(textline,lidx,type="Vbboxdata")
                else:
                    # Calculate separator
                    offset = 0
                    if self.info.datagroups[0]+1 != self.info.datagroups[1]:
                        offset = 1
                    x_max = np.max(self.structure["rborder"][self.info.datagroups[0]:self.info.datagroups[1]-offset])
                    x_min = np.min(self.structure["lborder"][self.info.datagroups[0]:self.info.datagroups[1]-offset])
                    size = x_max-x_min
                    calculated_sep = [x_min + (size)// 3, x_min + size*2//3, x_max]
                    # Find bbox/visual separator
                    for lidx, content in enumerate(content_lines):
                        if self.structure["separator"] and self.structure["separator"][lidx]:
                            if self.structure["separator"][lidx]["bbox"] and len(
                                    self.structure["separator"][lidx]["bbox"]) and \
                                    len(self.structure["separator"][lidx]["bbox"]) == self.info.subtables:
                                self.structure["bbox_separator"][lidx] = True
                                self.info.separator = self.structure["separator"][lidx]["bbox"]
                            elif not self.info.separator and self.structure["separator"][lidx]["visual"] and len(
                                    self.structure["separator"][lidx]["visual"]) == self.info.subtables:
                                self.info.separator = self.structure["separator"][lidx]["visual"]
                    # Calculate mean separator value
                    if self.info.separator:
                        self.info.separator[0][2] = (self.info.separator[0][2]+calculated_sep[0])//2
                        self.info.separator[1][2] = (self.info.separator[1][2]+calculated_sep[1])//2
                        self.info.separator[2][2] = calculated_sep[2]
                    else:
                        #print("log this file")
                        self.logger("Sharetable_Separator").log(level=20, msg="Only Regex used!")
                        return False
                    #Read the share values
                    for lidx, content in enumerate(content_lines):
                        #print(lidx)
                        sharetype = ""
                        if self.structure["data"][lidx]:
                            bbox = list(content["words"][0]["hocr_coordinates"])
                            for cidx,subtable in enumerate(self.info.separator):
                                subtable = sorted(subtable)
                                if bbox[0] >= subtable[0]:
                                    bbox[0] = min(self.structure["lborder"])
                                bbox[2] = subtable[0]
                                year = self._reocr(bbox[:]).strip()
                                #self.info.reocrcount += 1
                                if len(year) == 2:
                                    year = "19"+year
                                bbox[0] = bbox[2]
                                bbox[2] = subtable[2]
                                value = self._reocr(bbox[:]).replace("1/2",",5").replace("1/4",",25").replace("3/4",",75").strip()
                                #self.info.reocrcount += 1
                                amount = "".join([char for char in value if char.isdigit()])
                                currency, unit = "", 1
                                if "DM" in value[len(amount):]:
                                    currency = "DM"
                                else:
                                    unit = "%"
                                if amount == "" or all([False for char in amount if char.isdigit()]):
                                    continue
                                self.content["Vbboxdata"][str(lidx)+" "+str(cidx)] = \
                                    {"Year":year,
                                     "Deadline": "",
                                     "Amount":amount,
                                     "Currency":currency,
                                     "Unit":unit,
                                     "Kind":"ultimo",
                                     "Notice":"",
                                     "Comment": sharetype}
                                bbox[0] = subtable[2]+10
            # Todo: Combine Regex and Vbboxdata and Sharedata set
        if self.content["Regexdata"] and self.content["Vbboxdata"]:
            self.combine_datasets()
        elif not self.content["Regexdata"]:
            self.content["Regexdata"] = self.content["Vbboxdata"]
        if not self.content["Regexdata"] and not self.content["Vbboxdata"]:
            return False
        self.create_sharedataset()
        # Delete useless content
        del self.content["Regexdata"]
        del self.content["Vbboxdata"]
        return True

    def _get_information(self,content,lidx):
        # Extract informations
        """
                    LÖSCHE G und T aus Tabelle
                    Aktienkurs(DM per Stück)
                    (p. St.)

                    1967 Lit. A   40%
                         Lit. B   50%

                    a) Inhaber - Aktien // b) Namens - Aktien
                    Stammaktien // Vorzugsaktien
                    Stammaktien // Vorz.-Aktien
                    gr.St.      // kl.St.
                    St.A.       // V.A.
                    A           // B
                    alt         // jung
                    St.-Akt.    // Vorz.-Akt.
                    Inh.-Akt.   // Nam.-Akt.
                    Inh.RM      // Nam.-St.-Akt.
                    St.-Akt.    // Gen.Sch.
                    Lit. A      // Lit. C
                    Lit. A      // Lit. B
                    C           // D // E(ohne Currency)
                    RM 300      // 400 // 500
        """
        if lidx == 0:
            # Delete "Aktienkurs" out of the first line
            linetext = content["text"].replace("Aktienkurse","").replace("Aktienkurs","").replace("p.Stück","").replace("(p.St.)","").replace("(","").replace(")","").replace(":","")
        else:
            linetext = content["text"]
        if self.info.regex.sharetypereg.search(linetext.lower()):
            sharetypes = self.info.regex.sharetypereg.finditer(linetext.lower())
            if not self.info.sharetypes:
                self.info.sharetypes = {}
            self.info.sharetypes[lidx] = {}
            self.info.sharetypelidx = lidx
            startidx = 0
            for sharetype in sharetypes:
                if " RM" in linetext:
                    # TODO:Log this file
                    print("log this file")
                    self.logger("Sharetable_Information").log(level=20, msg="RM")
                    for number in self.info.regex.numbergrpreg.findall(linetext[sharetype.regs[0][1]:]):
                        self.info.sharetypes[lidx][len(self.info.sharetypes[lidx])] = ("RM"+number).strip()
                    return False
                else:
                    if " zu " in content["text"] or " mit " in content["text"] or " ohne " in content["text"]:
                        self.info.sharetypes[lidx][len(self.info.sharetypes[lidx])] = linetext[startidx:].replace(",",".").split(".")[0].split(")")[-1]
                    else:
                        self.info.sharetypes[lidx][len(self.info.sharetypes[lidx])] = \
                        linetext[startidx:sharetype.regs[0][1]].split(")")[-1]
                    startidx = sharetype.regs[0][1]
        else:
            if lidx > 3 and self.info.closing_date == "" and linetext.strip()[0] == "(" and linetext.strip()[-1] == ")":
                self.info.closing_date = linetext[1:-1]
            if self.info.regex.startingdatereg.search(linetext):
                sdidx = self.info.regex.startingdatereg.search(linetext).regs[0]
                self.content["additional_info"].append("Starting date: "+linetext[sdidx[0]:sdidx[1]])
            if self.info.regex.noticereg.search(linetext):
                self.info.notice = linetext[self.info.regex.noticereg.search(linetext).regs[0][1]:].replace(".",",").split(",")[0]
            #linetext = '+) umgerechnet auf DM-Basis:162,86 %.'
            if self.info.regex.conversion.search(linetext):
                if self.info.sharetypes:
                    for type in reversed(list(self.info.sharetypes.keys())):
                        for idx in self.info.sharetypes[type].keys():
                            self.info.sharetypes[type][idx] += linetext[2:]
                        break
                else:
                    self.content["additional_info"].append(linetext[2:])
            elif self.info.regex.addinforeg.search(linetext):
                # Search for the next data line?
                self.content["additional_info"].append(linetext[2:])

        return True

    def _extract_regexlvl(self,textline,lidx,type="Regexdata"):
        """Extracts the information only based on regexpattern"""
        try:
            tableregex = self.info.regex.greptable
            sharetypes = {0: ""}
            if self.info.sharetypes:
                if len(self.info.sharetypes[list(self.info.sharetypes.keys())[-1]]) == 2:
                    tableregex = self.info.regex.greptable2col
                sharetypes = self.info.sharetypes[list(self.info.sharetypes.keys())[-1]]
                #else:
                #    sharetypes = self.info.sharetypesself.info.sharetypes[list(self.info.sharetypes.keys())[-1]]
            # clear bracket content
            brackets = self.info.regex.bracketfinder.findall(textline)
            closing_date = ""
            if lidx+1 in self.info.datagroups or lidx+2 in self.info.datagroups:
                date = self.info.regex.closingdate.findall(textline[:10])
                if date and closing_date == "":
                    closing_date = date[0].strip()
            for bracket in brackets:
                date = self.info.regex.closingdate.findall(bracket)
                if date and closing_date == "":
                    closing_date = date[0]
                textline.replace(bracket,"").replace("   "," ").replace("  "," ")
            textline = textline.replace("1/2",",5").replace("1/4",",25").replace("3/4",",75")
            textline = textline.replace(" 1/", "1/").replace(" ,", ",")
            gtables = tableregex.findall(textline.replace("+)", "").replace("T", "").replace("G", "").replace("  ", " "))
            cidx = 0
            for idx,gtable in enumerate(gtables):
                gtable = list(gtable)
                if gtable[2] == "" and len(gtable[1])>1 and gtable[1][:2] != "19":
                    # If year is missing numbers will be false postive year
                    gtable[2] = gtable[1]
                    gtable[1] = "-1"
                if gtable[1] == "":
                    gtable[1] = "-1"
                if len(gtable[1]) == 2 and gtable[1] != "-1":
                    gtable[1] = "19" + gtable[1]
                elif len(gtable[1]) > 4:
                    gtable[1] = gtable[1][:4]
                offset = 0
                if idx == len(gtables)-1:
                    self.info.closing_date = closing_date
                currency, unit = "", 1
                if "DM" in gtable[3 + offset]:
                    currency = "DM"
                else:
                    unit = "%"
                for idx, sharetype in sharetypes.items():
                    self.content[type][str(lidx)+" "+str(cidx)] = \
                        {"Year": gtable[1],
                         "ClosingDate": "",
                         "Amount": gtable[2 + offset],
                         "Currency": currency,
                         "Unit": unit,
                         "Kind": "ultimo",
                         "Notice": self.info.notice,
                         "Comment": sharetype}
                    cidx += 1
                    offset = 2
                    #print(gtable)
                self.info.closing_date = ""
        except Exception as e:
            self.logger(f"Sharetable_{type}").log(level=20,msg=e)
            pass
        return

    def _uid_item_array(self,type,item,convert=float):
        array = {"UID":[],item:[]}
        for uid in self.content[type].keys():
            num = self.content[type][uid][item]
            num = num.replace(",", ".")
            if num == "-" or num == " ":
                continue
            if "/" in num:
                num = num[:num.index("/")-1]
            try:
                array[item].append(convert(num))
                array["UID"].append(uid)
            except Exception as e:
                print(f"Couldnt convert {num}")
        return array

    def combine_datasets(self):
        #del self.content["Regexdata"][0]
        regexdata = self._uid_item_array("Regexdata","Amount")
        visualdata = self._uid_item_array("Vbboxdata","Amount")
        # Running Mean (not outlier roboust!!!)
            # rmean = np.convolve(regexval, np.ones((3,)) / 3)
            # rmean = np.concatenate(([sum(rmean[:2])],rmean[2:-2],[sum(rmean[-2:])]))
        #Filtered Median with kernel size of 3
        regexdata["Run_median"] = signal.medfilt(regexdata["Amount"], kernel_size=3)
        #IQR
        regexdata["IQR"] = stats.iqr(regexdata["Amount"])*1.5
        for idx, (uid, val) in enumerate(zip(regexdata["UID"],regexdata["Amount"])):
            if not (regexdata["Run_median"][idx]-(regexdata["IQR"]) < val < regexdata["Run_median"][idx]+(regexdata["IQR"])):
                if uid in visualdata["UID"]:
                    vuid = visualdata["UID"].index(uid)
                    if (regexdata["Run_median"][idx]-(regexdata["IQR"]) < visualdata["Amount"][vuid] < regexdata["Run_median"][idx]+(regexdata["IQR"])):
                        self.content["Regexdata"][uid]["Amount"] = self.content["Vbboxdata"][uid]["Amount"]
                    elif ((regexdata["Run_median"][idx]-(regexdata["IQR"]))*0.005 < val < (regexdata["Run_median"][idx]+(regexdata["IQR"]))*500):
                        self.content["Regexdata"][uid]["Amount"] = "-"
                    if self.content["Regexdata"][uid]["Year"] == "-1":
                        self.content["Regexdata"][uid]["Year"] = self.content["Vbboxdata"][uid]["Year"]
        for uid in set(visualdata["UID"]).difference(set(regexdata["UID"])):
            self.content["Regexdata"][uid] = self.content["Vbboxdata"][uid]
        return

    def create_sharedataset(self):
        # del self.content["Regexdata"][0]
        sharedata = self._uid_item_array("Regexdata", "Year",convert=int)
        idxset = np.argsort(sharedata["Year"])
        #uid = sharedata["UID"][idxset[-1]]
        last_year = self.content["Regexdata"][sharedata["UID"][idxset[-1]]]["Year"]
        for uidx in idxset:
            uid = sharedata["UID"][uidx]
            self.content["Sharedata"][len(self.content["Sharedata"])] = self.content["Regexdata"][uid]
            if last_year == self.content["Regexdata"][uid]["Year"]:
                self.content["Sharedata"][len(self.content["Sharedata"])-1]["ClosingDate"] = self.info.closing_date
        return

class DividendtableRegex(object):
    """Compiled regex pattern for TP"""

    def __init__(self):
        self.date = regex.compile(r"(?:19\d\d)")
        self.insgesamt = regex.compile(r"insgesamt{e<=" + str(1) + "}")
        self.bonus = regex.compile(r"([\d\%\sDMhflYen\,\.]*)Bonus{e<=1}")
        self.currency = regex.compile(r"([a-zA-Z]{2,}|\$)")
        self.dividend = regex.compile(r"(?:\d[\d\,\.\s]*)")
        self.talon = regex.compile(r"Talon{e<=" + str(1) + "}")
        self.divschnr= regex.compile(r"([\d\-]{1,})")

class DividendtableInfo(object):
    """Helper dataclass - Information storage for TP"""

    def __init__(self, snippet=None):
        self.snippet = snippet
        self.regex = DividendtableRegex()
        self.config = ConfigurationHandler(first_init=False).get_config()


class Dividendtable(Table):
    def __init__(self, snippet=None):
        Table.__init__(self)
        self.info = DividendtableInfo(snippet)

    ##### ANALYSE #####
    def analyse_structure(self, content_lines, feature_lines):
        """Analyse the structure of table with the help from the template information and extract some necessary parameter"""
        skip = False
        self.structure["input"] = []
        self.structure["data"] = []
        for lidx, (content, features) in enumerate(zip(content_lines, feature_lines)):
            if skip: continue
            text = content["text"]
            # Append the default values to the structure list
            if "(" in text and ")" not in text:
                if "(" not in content_lines[lidx+1]["text"] and ")" in content_lines[lidx+1]["text"]:
                    skip = True
                    self.structure["input"].append(text+content_lines[lidx+1]["text"])
                    if features.alphabetical_ratio > 0.5:
                        self.structure["data"].append(0)
                    else:
                        self.structure["data"].append(1)
                    continue
            self.structure["input"].append(text)
            if features.alphabetical_ratio > 0.5:
                self.structure["data"].append(0)
            else:
                self.structure["data"].append(1)

        return

    ##### ANALYSE #####
    def extract_content(self,content_lines, feature_lines):
        """Extract the dividend information"""
        self.structure["output"] = []
        comment = ""
        for valid,line in zip(self.structure["data"],self.structure["input"]):
            if "Dividend" in line: continue
            if not valid:
                comment += line+" "
                continue
            content = {}
            fragments = None
            #line = line.replace("(+")
            if "(" in line:
                fragments = line.rsplit("(",1)
                if len(fragments) > 1:
                    self.extract_bracket_info(fragments[1], content)
                line = fragments[0].strip()
            if ":" in line:
                fragments = line.split(":",1)
            elif self.info.regex.dividend.search(line):
                    regs = None
                    #hey = self.info.regex.dividend.finditer(line)
                    for res in self.info.regex.dividend.finditer(line):
                        regs = res.regs[0]
                    if regs:
                        fragments = [line[:regs[0]],line[regs[0]:]]
            else:
                continue
            if fragments:
                content["Year"] = fragments[0]
                self.extract_dividend_info(fragments[1], content)
            if content:
                self.content[len(self.content)] = content
        if comment != "":
            self.content["Comment"] = comment.strip()
        return

    def extract_bracket_info(self, data,content):
        divschnr = self.info.regex.divschnr.findall(data)
        if divschnr:
            content["Div_Sch_Nr"] = ",".join(divschnr)
        if self.info.regex.talon.match(data):
            content["Div_Sch_Nr"] = content.get("Div_Sch_Nr","")+"Talon"
        return

    def extract_dividend_info(self,data,content):
        data = data.replace("je","")
        if self.info.regex.insgesamt.search(data):
            content["comment"] = data
            return
        #data = data+"+ 50 % Bonus"
        if self.info.regex.bonus.search(data):
             result = self.info.regex.bonus.search(data)
             content["Bonus"] = data[result.regs[1][0]:result.regs[1][1]].strip()
             data = data.replace(data[result.regs[0][0]:result.regs[0][1]],"").replace("+","").strip()
        if "%" in data:
            result = self.info.regex.dividend.findall(data)[0]
            content["Dividend"] = result.strip()
        else:
            if self.info.regex.currency.search(data):
                result = self.info.regex.currency.search(data)
                content["Currency"] = data[result.regs[0][0]:result.regs[0][1]].strip()
                content["St_G"] = self.get_number(data[result.regs[0][1]:])
            else:
                content["Dividend"] = self.get_number(data)
        return

    def get_number(self,data):
        return "".join([char for char in data if char.isdigit() or char in [".",","]])