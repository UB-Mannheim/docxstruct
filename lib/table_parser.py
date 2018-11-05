import numpy as np
import regex
from akf_corelib.configuration_handler import ConfigurationHandler
import glob
import json
from skimage import filters, color, measure, io
from PIL import ImageDraw


class TableRegex(object):
    """Compiled regex pattern for TP"""

    def __init__(self):
        self.columnheader = regex.compile(r"\d\d[- /.]\d\d[- /.]\d\d\d\d|\d\d\d\d\/\d\d|\d\d\d\d")
        self.balancetype = regex.compile(r"(?:" + "Aktiva|Passiva" + "){e<=" + str(2) + "}")
        self.assets_stop = regex.compile(r"(?:" + "kaptial|Passiva" + "){e<=" + str(2) + "}")
        self.incometype = regex.compile(r"(?:" + "ertrag|erträge|ergebnis|einnahme" + "){e<=" + str(1) + "}")
        self.lastidxnumber = regex.compile(r"(\d|\d.)$")
        self.amount = regex.compile(r"\S?in{e<=" + str(1) + "}.{0,3}\d.?[0|Ö|O]{2,3}")
        self.amountmio = regex.compile(r"\S?in{e<=" + str(1) + "}.Mio")
        self.additional_info = regex.compile(
            r"(^[+][\)]|Bilanzposten|Erinnerungswert|Verlustausweis){e<=" + str(1) + "}")


class TableInfo(object):
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
        self.regex = TableRegex()
        self.config = ConfigurationHandler(first_init=False).get_config()
        self.dictionary = None

class Table(object):
    """This class helps to deal with tables
    - Analyse structure
    - Extract information"""

    def __init__(self, snippet=None):
        self.content = {}
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
        self.info = TableInfo(snippet)

    ###### ANALYSE ######
    def analyse_structure(self, content_lines, feature_lines, template="datatable"):
        """Analyse the structure of table with the help from the template information and extract some necessary parameter"""

        if template in ["datatable", "datatable_balance", "datatable_income"]:
            if template == "datatable_balance":
                self.info.type = "Aktiva"
            if template == "datatable_income":
                self.info.type = "Verlust"
            for content, features in zip(content_lines, feature_lines):
                # Append the default values to the structure list
                self._append_defaults(content,type=self.info.type)
                # Checks if any text was recognized
                if isinstance(features, bool):
                    continue
                # Checks if line is evaluable
                self._check_evaluability(content, features)
                # Checks the current template type (balance= Aktiva/Passiva,income=Gewinn/Verlust)
                self._check_type(content,template)
                # Iterate over all words and search for valid separator values (based on bbox)
                if features.counter_numbers > 3:
                    self._find_separator(features, content)
        # check if date is over more than one line
        self._check_multiline_date()
        # delete unnecassary lines
        self._del_empty_lines(content_lines, feature_lines)
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

    def _check_type(self, content,template):
        if template == "datatable_balance":
            if self.info.type == "Aktiva" and self.info.regex.assets_stop.search(content["text"]) is not None:
                self.info.type = "Passiva"
                self.structure["type"][-1] = self.info.type
        if template == "datatable_income":
            if self.info.regex.incometype.search(content["text"]) is not None:
                self.structure["type"][-1] = "Gewinn"
        return self.info.type

    def _check_evaluability(self, content, features):
        if features.counters_alphabetical_ratios[features.counter_words - 1] < 0.5 or \
                any([True for char in content["text"][:-2] if char.isdigit()]):
            self.structure["eval"][-1] = True
        return

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
                        if self.info.start is True and self.info.regex.lastidxnumber.search(content["text"][offset:]) \
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
                (features.counter_alphabetical < 3 or
                 self.info.regex.balancetype.search(content["text"]) is not None) and \
                self.info.regex.columnheader.search(content["text"]):
            self.structure["date"][-1] = True
            self.info.start = True
        return False

    def _check_multiline_date(self):
        old_date = None
        for date in list(np.nonzero(np.array(self.structure["date"])))[0]:
            if not old_date:
                old_date = date
                continue
            if date - old_date < 3:
                if not any(self.structure["next_section"][old_date:date + 1]):
                    for idx in range(old_date + 1, date + 1):
                        self.structure["lborder"][idx] = -1

    def _del_empty_lines(self, content_lines, feature_lines):
        delidxs = list(np.argwhere(np.array(self.structure["lborder"]) == -1))
        if delidxs:
            for delidx in reversed(delidxs):
                del content_lines[delidx[0]]
                del feature_lines[delidx[0]]
                for skey in self.structure.keys():
                    del self.structure[skey][delidx[0]]
        self.info.start = False

    ###### EXTRACT ######
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
                if not self.info.separator:
                    self.info.separator = int(
                        np.median([val for val in self.structure["separator"][startidx:next_date] if val > -1]))
            else:
                self.info.separator = int(np.median(self.structure["rborder"]))
        else:
            separatorlist = [val for val in self.structure["separator"][startidx:next_date] if val > -1]
            if separatorlist and  abs(self.info.separator-int(np.median(separatorlist))) > 250:
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
                    self.info.row = ''.join(
                        [i for i in entry['text'] if i not in list("()")]).strip() + " "
                    if self.info.dictionary and not self._valid_itemname(lidx=lidx):
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
                # Get the content in structured manner
                self._extract_content(entry, features, extractlevel)
                self.info.row = ""

        # Get all var names
        if self.info.config.STORE_OCCURENCES and template == self.info.config.OCCURENCES_TABLETYPE:
            self.var_occurence()
        return

    def _read_dictionary(self,tabletype):
        test = glob.glob(f"{self.info.config.INPUT_TABLE_DICTIONARY}*{tabletype}.json")
        if test:
            with open(test[0], "r") as file:
                self.info.dictionary = json.load(file)
        return

    def _columnheader(self, content_lines) -> int:
        """"Helper to find the column headers"""

        lines = np.nonzero(self.structure["date"])[0].tolist()
        if not lines:
            self.info.col = [0, 1]
            self._additional_columninfo(content_lines, [0, 2])
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
                amount = self.info.regex.amount.findall(content_lines[lidx]['text'])
                if amount:
                    infotext = ("(in 1 000 " + content_lines[lidx]['text'].replace(amount[0], "")).replace("  "," ")
                    offset += counter
                    break
            else:
                if not self.structure["next_section"][lidxs[1]]:
                    offset = 2
            if infotext == "" and len(lidxs) > 1:
                # Try to catch amount info with reocr
                reinfo = self._reocr(list(content_lines[lidxs[1]]["hocr_coordinates"]))
                amount = self.info.regex.amount.findall(reinfo)
                if amount:
                    infotext = ("(in 1 000 " + reinfo.replace(amount[0], "")).replace("  ", " ")
                amountmio = self.info.regex.amountmio.findall(reinfo)
                if amountmio:
                    infotext = ("(in 1 000 " + reinfo.replace(amountmio[0], "")).replace("  ", " ")
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

    def _reocr(self, bbox):
        if self.info.snippet.crop(bbox):
            if self.info.config.SAVE_SNIPPET:
                self.info.snippet.save(self.info.config.IMAGE_PATH)
            self.info.snippet.to_text()
            return self.info.snippet.text
        return ""

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
        if snd_section == fst_section:
            snd_section += 1
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
        for additive in self.info.dictionary["Zusatz"].keys():
            item = item.replace(additive+" ", "")
        item = item.lower().replace(" ","")
        if len(item) < 8:
            fuzzy_range = 1
        elif len(item) >= 12:
            fuzzy_range = 3
        else:
            fuzzy_range = 2
        itemregex = regex.compile(r"^"+item+"${e<=" + str(fuzzy_range) + "}")
        for itemlvl in ["Unterpunkte","Hauptpunkte"]:
            for itemname in list(self.info.dictionary[itemlvl].keys()):
                if itemregex.search(itemname.lower().replace(" ","")):
                    self.info.row = self.info.dictionary[itemlvl][itemname]
                    if itemlvl == "Unterpunkte" and self.info.lastmainitem and lidx and self.info.fst_order < self.structure["lborder"][lidx]:
                        self.info.order = 2
                        self.info.row = f"{self.info.lastmainitem} ({self.info.row})"
                    return True
        return False

    def var_occurence(self):
        with open('./var_occurences.json') as f:
            data = json.load(f)
            for type in self.content:
                if not isinstance(self.content[type][0], str):
                    for content_keys in self.content[type][0].keys():
                        if content_keys in data.keys():
                            data[content_keys] += 1
                        else:
                            data[content_keys] = 0
        with open('./var_occurences.json', 'w') as outfile:
            json.dump(data, outfile,indent=4,ensure_ascii=False)
        return

#legacy code just in case..
"""
if self.info.start is False and self.structure["eval"][lidx] is True and any(self.structure["date"][:3]) is False:
    self.info.separator = self.structure['separator'][lidx]
    for type in set(self.structure["type"]):
        for col in range(0,2):
            self.content[type][col] = {}
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
                for type in set(self.structure["type"]):
                    self.content[type][idx] = {'date': dates}
                self.info.currency = True
    elif self.info.currency:
        #todo: fix for loop
        for idx in range(0,len(self.info.col)):
            if "DM" in entry["text"].replace(" ", "") and "1000" in entry["text"].replace(" ", ""):
                entry["text"] = "in 1000 DM"
            else:
                entry["text"] = entry["text"].replace("(", "").replace(")", "")
                for type in set(self.structure["type"]):
                    self.content[type][idx]["currency"] = entry['text']
            self.info.start = True
    self.info.row = ""
"""