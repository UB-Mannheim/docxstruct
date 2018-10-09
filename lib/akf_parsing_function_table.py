import numpy as np
import regex

class Tableinfo(object):

    def __init__(self):
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
        self.assets = True
        self.currency= False

class Table(object):

    def __init__(self):
        self.content = {}
        self.structure ={"eval":[],
                         "date":[],
                         "btype":[],
                         "lborder":[],
                         "separator":[],
                         "gapsize":[],
                         "gapidx":[],
                         "rborder":[]}
        self.info = Tableinfo()

    def analyse_structure(self, content_lines, feature_lines, template="datatable"):
        reg_assets = regex.compile(r"(?:" + "kaptial|Passiva" + "){e<=" + str(2) + "}")
        if template in ["datatable", "datatable_money"]:
            for content, features in zip(content_lines, feature_lines):
                self.structure["separator"].append(-1)
                self.structure["gapsize"].append(-1)
                self.structure["gapidx"].append(-1)
                self.structure["date"].append(False)
                self.structure["rborder"].append(content["words"][len(content["words"]) - 1]['hocr_coordinates'][2])
                self.structure["lborder"].append(content["words"][0]['hocr_coordinates'][0])
                if isinstance(features, bool):
                    self.structure["eval"].append(False)
                    self.structure["btype"].append("Aktiva")
                    continue
                if features.counter_words > 1 and features.counters_alphabetical_ratios[features.counter_words - 1] < 0.5:
                    self.structure["eval"].append(True)
                else:
                    self.structure["eval"].append(False)
                if self.info.assets:
                    if reg_assets.search(content["text"]) is not None:
                        self.info.assets = False
                        self.structure["btype"].append("Passiva")
                    else:
                        self.structure["btype"].append("Aktiva")
                else:
                    self.structure["btype"].append("Passiva")

                for widx, wordratio in enumerate(reversed(features.counters_alphabetical_ratios)):
                    if wordratio > 0.5:
                        if widx >= 1:
                            xgaps = np.append(np.zeros(features.counter_words - widx)[0],
                                              features.x_gaps[features.counter_words - widx:])
                            maxgap = int(np.argmax(xgaps))
                            self.structure["separator"][-1] = int((content["words"][maxgap + 1]['hocr_coordinates'][0] +
                                               content["words"][maxgap]['hocr_coordinates'][2]) / 2)
                            self.structure["gapsize"][-1] = int(xgaps[maxgap])
                            self.structure["gapidx"][-1] = maxgap
                            if features.counter_special_chars > 3 and features.counter_alphabetical < 4:
                                self.structure["date"][-1] = True
                        break
                    if widx == len(features.counters_alphabetical_ratios)-1 and widx >= 1 and wordratio < 0.5:
                        if widx > 1 and widx+1 < features.counter_words:
                            xgaps = np.append(np.zeros(features.counter_words - widx-1)[0],
                                          features.x_gaps[features.counter_words - widx-1:])
                        else:
                            xgaps = [features.x_gaps[0]]
                        maxgap = int(np.argmax(xgaps))
                        self.structure["separator"][-1] = int((content["words"][maxgap+1]['hocr_coordinates'][0] +
                                                               content["words"][maxgap]['hocr_coordinates'][2]) / 2)
                        self.structure["gapsize"][-1] = int(xgaps[maxgap])
                        self.structure["gapidx"][-1] = maxgap
                        if features.counter_special_chars > 3 and features.counter_alphabetical < 4:
                            self.structure["date"][-1] = True
        return

    def extract_content(self, content_lines, feature_lines, template="datatable"):
        for btype in set(self.structure["btype"]):
            self.content[btype] = {}
        for lidx, [entry, features] in enumerate(zip(content_lines, feature_lines)):
            self.info.lidx = lidx
            btype = self.structure["btype"][lidx]
            # read the number of columns the currency of the attributes
            if self.info.start is True and self.info.lborder is None:
                offset = 2
                if self.structure["date"][lidx+1] is False:
                    offset = 1
                self.info.lborder = min(self.structure["lborder"][lidx:lidx+offset])
                self.info.rborder = max(self.structure["rborder"][lidx:lidx+offset])
            if entry["text"] == "":
                continue
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
                    if len(entry['words']) == 2:
                        self.info.separator = self.structure['separator'][lidx]
                    else:
                        for next in range(lidx+2,len(self.structure["eval"])-1):
                            if self.structure['separator'][next] != -1:
                                self.info.separator = self.structure['separator'][lidx]
                                break
                    for idx, year in enumerate(self.info.col):
                        # Count the coloumns 0,1,2,...
                        if template in ["datatable","datatable_money"]:
                            for btype in set(self.structure["btype"]):
                                self.content[btype][idx] = {'year': year}
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
                    #self.info.gapidx
                    self._extract_wwboxlevel(entry, features)
                else:
                    self._extract_wordlevel(entry, features)
                self.info.row = ""
        return

    def _extract_wwboxlevel(self, entry, features):
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
