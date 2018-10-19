import numpy as np
import regex
from akf_corelib.configuration_handler import ConfigurationHandler
from skimage import filters, color, measure, io
from PIL import ImageDraw

class TableRegex(object):
    """Compiled regex pattern for TP"""
    def __init__(self):
        self.assets_stop = regex.compile(r"(?:" + "kaptial|Passiva" + "){e<=" + str(2) + "}")
        self.columnheader = regex.compile(r"\d\d[- /.]\d\d[- /.]\d\d\d\d|\d\d\d\d\/\d\d|\d\d\d\d")
        self.balancetype = regex.compile(r"(?:" + "Aktiva|Passiva" + "){e<=" + str(2) + "}")
        self.lastidxnumber = regex.compile(r"[\d|\d.]$")
        self.amount = regex.compile(r"\S?in{e<="+str(1)+"}.{0,3}\d.?[0|Ö|O]{2,3}")
        self.additional_info = regex.compile(r"(^[+][\)]|Bilanzposten|Erinnerungswert|Verlustausweis){e<="+str(1)+"}")

class TableInfo(object):
    """Helper dataclass - Information storage for TP"""
    def __init__(self, snippet=None, regexdict=None):
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
        self.snippet = snippet
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
                if features.counter_numbers > 3:
                    self._find_separator(features, content)
        #check if date is over more than one line
        old_date = None
        for date in list(np.nonzero(np.array(self.structure["date"])))[0]:
            if not old_date:
                old_date = date
                continue
            if date-old_date < 3:
                if not any(self.structure["next_section"][old_date:date+1]):
                    for idx in range(old_date+1,date+1):
                        self.structure["lborder"][idx]=-1

        # delete unnecasary lines
        delidxs = list(np.argwhere(np.array(self.structure["lborder"])==-1))
        if delidxs:
            for delidx in reversed(delidxs):
                del content_lines[delidx[0]]
                del feature_lines[delidx[0]]
                for structurkey in self.structure.keys():
                    del self.structure[structurkey][delidx[0]]
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
        if content["text"] == "":
            self.structure["rborder"].append(-1)
            self.structure["lborder"].append(-1)
        else:
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
                    if widx != features.counter_words:
                        if content["words"][features.counter_words - widx-1]["text"][-1].isdigit():
                            widx -= 1
                    xgaps = np.append(np.zeros(features.counter_words - widx)[0],
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
                    #Todo: maybe searcj for amount to fuzzy?
                    if not self._vali_date(features, content):
                        if self.info.start is True and self.info.regex.lastidxnumber.search(content["text"][offset:])\
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

    def _vali_date(self, features, content:dict):
        """Checks if the string contains a valid date"""
        if features.counter_numbers > 5 and \
                (features.counter_alphabetical < 3 or self.info.regex.balancetype.search(content["text"]) is not None) and \
                self.info.regex.columnheader.search(content["text"]):
            self.structure["date"][-1] = True
            self.info.start = True
        return False


    ###### EXTRACT ######
    def extract_content(self, content_lines:list, feature_lines:list, template="datatable"):
        """Extracts the table information in a structured manner in a the 'content'-dict with the analyse information"""
        self.info.nrow = len(feature_lines)
        # Get the columnheader information based on date lines
        startidx = self._columnheader(content_lines)
        self.info.start = True
        next_date = list(np.nonzero(self.structure["date"][startidx:])[0])
        if not next_date:
            next_date = self.info.nrow
        else:
            next_date = next_date[0]+startidx
        # Calculate first separator
        if len(self.info.col) > 1:
            if self.info.config.USE_TOOLBBOX:
                self.info.separator = self._imgseparator(content_lines,startidx,next_date)
            if not self.info.separator:
                self.info.separator = int(np.median([val for val in self.structure["separator"][startidx:next_date] if val>-1]))
        else:
            self.info.separator = int(np.median(self.structure["rborder"]))
        # Extract content of each line
        for lidx, [entry, features] in enumerate(zip(content_lines, feature_lines)):
            self.info.lidx = lidx
            if entry["text"] == "" or lidx < startidx:
                continue
            if self.info.regex.additional_info.findall(entry["text"]):
                self.content["additional_info"] = ""
                for info_entry in content_lines[lidx:]:
                    self.content["additional_info"] += info_entry["text"]
                break
            # read the number of columns the currency of the attributes
            if self.info.lborder is None: # or (self.structure["date"][lidx] and self.info.fst_order is not None):
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
            if self.info.start is True:
                if features.counter_numbers < 2 and not self.info.regex.lastidxnumber.findall(entry['text']):
                    self.info.row = ''.join(
                        [i for i in entry['text'] if i not in list("()")]).strip() + " "
                    continue
                self.info.row += ''.join([i for i in entry['text'] if i not in list("0123456789()")]).strip()
                self.info.row = self.info.row.replace("- ", "")
                if self.structure["date"][lidx] is True or self.info.row == "":
                    next_sections = list(np.nonzero(self.structure["next_section"][lidx:])[0])
                    if next_sections:
                        next_section = next_sections[0]+lidx
                        offset = (self.info.lborder-min(self.structure["lborder"][next_section:]))
                        self.info.separator -= offset
                        self.info.lborder -= offset
                        self.info.fst_order -= offset
                        self.info.rborder -= offset
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
            self._additional_columninfo(content_lines,[0,2])
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
        infotext, offset = self._additional_columninfo(content_lines,(lines[0]-1,lines[0]+1,lines[0]+2))
        return lines[0] + offset

    def _additional_columninfo(self, content_lines, lidxs):
        infotext = ""
        offset = 1
        for counter, lidx in enumerate(lidxs):
            if content_lines[lidx]['text'] == "":
                counter += 1
                lidx += 1
            amount = self.info.regex.amount.findall(content_lines[lidx]['text'])
            if amount:
                infotext = "(in 1 000" +content_lines[lidx]['text'].replace(amount[0],"")
                offset += counter
                break
        else:
            if not self.structure["next_section"][lidxs[1]]:
                offset = 2
        for btype in set(self.structure["btype"]):
            self.content[btype] = {}
            for col in range(0,len(self.info.col)):
                self.content[btype][col] = {}
                if self.info.col != [1, 0]:
                    self.content[btype][col]["date"] = self.info.col[col]
                self.content[btype][col]["amount"] = infotext
        return infotext, offset

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
        numbers = ''.join([i for i in entry['text'] if i.isdigit() or i == " "]).strip()

        # If one column just parse
        if len(self.info.col) == 1:
            self.content[self.structure["btype"][self.info.lidx]][0][self.info.row] = " ".join(numbers)
            return True

        # First try to solve the problem with reocr the bbox
        if self.info.snippet:
            if self._extract_reocrlevel(entry,numbers):
                return True

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
                self.content[self.structure["btype"][self.info.lidx]][count_years][self.info.row] = (numbergrp + " " + number).strip()
                number = ""
                count_years -= 1
                if count_years == 0:
                    self.content[self.structure["btype"][self.info.lidx]][count_years][self.info.row] = " ".join(numbers[:len(numbers) - grpidx - 1])
                    return True
        return True


    def _extract_reocrlevel(self,entry,numbers):
        if self.info.separator < entry["hocr_coordinates"][2]:
            try:
                bbox = list(entry["hocr_coordinates"])
                bbox[0] = self.info.separator+13
                bbox = [val-5 if pos<2 else val+5 for pos, val in enumerate(bbox)]
                result = self._reocr(bbox).replace("\n","").replace("+)","")
                if result == "": return False
                if any(True for char in result if str(char).isalpha() and str(char) not in ["U","E"]): return False
                resultex = regex.compile(r"(?:" + result + "){e<=" + str(1) + "}")
                if resultex.findall(numbers):
                    self.content[self.structure["btype"][self.info.lidx]][0][self.info.row] = numbers[:-len(result)].strip()
                    self.content[self.structure["btype"][self.info.lidx]][1][self.info.row] = numbers[-len(result):].strip()
                    return True
            except:
                print("Reocr did not work!")
        return False

    def _reocr(self,bbox):
        if self.info.snippet.crop(bbox):
            self.info.snippet.save("/media/sf_ShareVB/")
            self.info.snippet.to_text()
            return self.info.snippet.text
        return ""

    def _imgseparator(self,content_lines,startidx,next_date):
        fst_section = list(np.nonzero(self.structure["next_section"])[0])
        if fst_section:
            first_section = fst_section[0]
        else:
            first_section = startidx+1
        if next_date-first_section > 3:
            snd_section = first_section+3
        else:
            snd_section = next_date-1
        if snd_section == first_section:
            snd_section += 1
        lborder = min(self.structure["lborder"][first_section:snd_section+1])
        rborder = max(self.structure["rborder"][first_section:snd_section + 1])
        tablebbox = [lborder,content_lines[first_section]["words"][0]["hocr_coordinates"][1],rborder,content_lines[snd_section-1]["words"][-1]["hocr_coordinates"][3]]
        if self.info.snippet.crop(tablebbox):
            tableimg = color.rgb2gray(np.array(self.info.snippet.snippet))
            thresh = filters.threshold_otsu(tableimg)
            threshed = tableimg > thresh
            threshed_red = np.sum(threshed,axis=0) > threshed.shape[0]*0.95
            label = measure.label(threshed_red)
            size = np.bincount(label.ravel())
            biggest = sorted(size[1:],reverse=True)[:2]
            if biggest[0]*0.3 > biggest[1]:
                selected = biggest[0]
            else:
                selected = biggest[1]
            gapidx = np.argwhere(size >= selected)[-1][0]
            gap = np.nonzero(label == gapidx)[0]
            separator = int(gap[0]+len(gap)*0.35)
            #draw = ImageDraw.Draw(self.info.snippet.snippet)
            #draw.line((separator,0,separator,threshed.shape[0]),fill=128)
            #self.info.snippet.save("/media/sf_ShareVB/")
            return separator+tablebbox[0]
        return None

#legacy code just in case..
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