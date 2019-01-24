from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from .data_helper import DataHelper as dh
from .akf_parsing_functions_common import AKFCommonParsingFunctions as cf
from akf_corelib.regex_util import RegexUtil as regu

import regex


class AkfParsingFunctionsTwo(object):

    def __init__(self, endobject_factory, output_analyzer, dictionary_handler):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_PARSER_AKF_FN_TWO, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

        self.cpr.print("init akf parsing functions two")

        self.ef = endobject_factory
        self.output_analyzer = output_analyzer
        self.dictionary_handler = dictionary_handler

    def parse_zahlstellen(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        split_post = origpost_red.split(';')
        DEFAULT_ENTRY = 1
        ADDITIONAL_INFO_BOTH = 2      # beide - two previous
        ADDITIONAL_INFO_ALL_PREV = 3  # sämtl. - all previous

        final_entries = []
        for index, entry in enumerate(split_post):
            entry_stripped = entry.strip()

            if "beide" in entry_stripped:
                entry_final = regex.sub(r"beide\s?\.?", "##", entry_stripped).strip()
                entry_final_split = entry_final.split('##')
                for index_fs, entry_fs in enumerate(entry_final_split):
                    if entry_fs.strip() == "" : continue
                    if index_fs < len(entry_final_split)-1:
                        final_entries.append((DEFAULT_ENTRY, entry_fs, "", "", ""))
                    else:
                        final_entries.append((ADDITIONAL_INFO_BOTH, entry_fs, "", "", ""))
                continue
            if regex.search("sämtl\s?\.?", entry_stripped):
                entry_final = regex.sub(r"sämtl\s?\.?", "##", entry_stripped).strip()
                entry_final_split = entry_final.split('##')
                for index_fs, entry_fs in enumerate(entry_final_split):
                    if entry_fs.strip() == "": continue
                    if index_fs < len(entry_final_split)-1:
                        final_entries.append((DEFAULT_ENTRY, entry_fs, "", "", ""))
                    else:
                        final_entries.append((ADDITIONAL_INFO_ALL_PREV, entry_fs, "", "", ""))
                continue

            entry_split = entry_stripped.split(',')
            bank = ""
            city = ""
            title = ""
            rest_info = []
            for fragment_index, fragment in enumerate(entry_split):
                if fragment_index == 0:
                    bank = fragment
                elif fragment_index == 1:
                    city = fragment
                elif fragment_index >= 2:
                    rest_info.append(fragment)
            if bank != "" or city != "" or title != "":
                final_entries.append((DEFAULT_ENTRY, bank, city, title, rest_info))

        # reverse list for better processing
        reverse_fe = final_entries.__reversed__()
        current_additional_info = ""
        current_info_index = None
        current_entry_type = None
        final_list = []
        for item_index, item in enumerate(reverse_fe):
            entry_type, entryorbank, city, title, rest_info = item
            # change current additional info
            if entry_type == ADDITIONAL_INFO_BOTH or entry_type == ADDITIONAL_INFO_ALL_PREV:
                current_info_index = item_index
                current_additional_info = entryorbank
            elif entry_type == DEFAULT_ENTRY:
                templist = [(entryorbank, city, title, current_additional_info, rest_info)]
                templist.extend(final_list)
                final_list = templist

            # end 'beide'-entry because it's over after 2 iterations
            if current_entry_type == ADDITIONAL_INFO_BOTH and item_index-current_info_index >= 1:
                current_info_index = None
                current_additional_info = ""

        # finally note the entries to output
        only_add_if_value = True
        for entry in final_list:
            bank, city, title, add_info, rest_info = entry
            if add_info.strip() != "":
                rest_info_new = [add_info]
                rest_info_new.extend(rest_info)
            else:
                rest_info_new = rest_info

            #if add_info != "" and add_info != None and city =="":
            #    city += add_info
            self.ef.add_to_my_obj("bank", bank, object_number=element_counter, only_filled=only_add_if_value)
            self.ef.add_to_my_obj("city", city, object_number=element_counter, only_filled=only_add_if_value)
            self.ef.add_to_my_obj("title", title, object_number=element_counter, only_filled=only_add_if_value)
            #self.ef.add_to_my_obj("additional_info", add_info, object_number=element_counter, only_filled=only_add_if_value)
            #self.ef.add_to_my_obj("rest_info", rest_info, object_number=element_counter, only_filled=only_add_if_value)
            self.ef.add_to_my_obj("rest_info", rest_info_new, object_number=element_counter, only_filled=only_add_if_value)

            element_counter += 1

        return True

    def parse_grundkapital(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # todo validate other currencies than 'DM'
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        only_add_if_value = True

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)





        gk = cf.parse_general_and_keys(content_texts,
                                  join_separated_lines=True,
                                  current_key_initial_value='start_value',
                                  abc_sections=True)
        print(gk)
        # check start value for 'normal' grundkapital content
        # if found parse
        start_value = gk['start_value']
        if len(start_value) >= 1:
            print("could be grundkapital")
            my_return_object, found_main_amount, element_counter, only_add_if_value, additional_info = \
                cf.parse_grundkapital_line(start_value[0], False, element_counter, only_add_if_value, [])
            currency = my_return_object['currency'].strip()
            amount = my_return_object['amount'].strip()
            if amount != "" and currency != "":
                self.ef.add_to_my_obj('Grundkapital', my_return_object, object_number=element_counter, only_filled=only_add_if_value)
            else:
                gk['additional_info'] = []
                gk['additional_info'].append(start_value[0])


        if len(start_value) >= 2: # get the additional values which are in start_value, but have nothing to do with that
            if 'additional_info' not in gk.keys():
                gk['additional_info'] = []

            gk['additional_info'] = []
            for index in range(1, len(start_value)):
                val = start_value[index]
                gk['additional_info'].append(val)

        """
        if 'additional_info' in gk.keys():
            gk_ai = cf.parse_general_and_keys(gk['additional_info'],
                                           join_separated_lines=True,
                                           current_key_initial_value='start_value_addinfo',
                                           abc_sections=True)

            print("lemme check")
        """


        for key in gk:
            if key is "start_value":
                continue
            entry = gk[key]
            # individual parsing here
            match_year = regex.search("\d\d\d\d", key) # key is year
            year = None
            key_rest = ""
            if match_year:
                year = match_year.group()
                key_rest = key.replace(year, "").strip()

            accumulated_text = []
            if key_rest != "":
                accumulated_text.append(key_rest)

            for inner_entry in entry:
                accumulated_text.append(inner_entry)

            final_entry = None
            if year is None:
                final_entry = accumulated_text
            else:
                final_entry = {
                    "year": year,
                    "text": accumulated_text
                }

            if final_entry != None and final_entry != "":
                self.ef.add_to_my_obj(key, final_entry, object_number=element_counter,
                                      only_filled=only_add_if_value)
                element_counter += 1

        # check all year lines and parse the
        return



        # old parsing style
        final_entries = []
        current_ref_index = -1
        found_main_amount = False
        additional_info = []
        only_add_if_value = True
        for text_index, text in enumerate(content_texts):
            text_stripped = text.strip()
            if text_stripped == "":
                continue

            # todo increment element ctr ?
            my_return_object, found_main_amount, element_counter, only_add_if_value, additional_info = \
                cf.parse_grundkapital_line(text_stripped, found_main_amount, element_counter, only_add_if_value, additional_info)

            for key in my_return_object:
                value = my_return_object[key]
                self.ef.add_to_my_obj(key, value, object_number=element_counter, only_filled=only_add_if_value)


        if len(additional_info) >= 1:
            add_lines_parsed = cf.parse_grundkapital_additional_lines(additional_info,element_counter,True, 0)
            self.ef.add_to_my_obj("additional_info", add_lines_parsed, object_number=element_counter,
                                     only_filled=only_add_if_value)

        return True

    def parse_ordnungsnrdaktien(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        only_add_if_value = True
        # example values - each line of content_texts list
        # '589300 (St.-Akt.)'
        # '589300.'
        first_number_match = True
        for entry in content_texts:
            entry_stripped = entry.strip()
            rest = entry_stripped
            if entry_stripped == "":
                continue

            match_number = regex.search(r"^([\d\s]*)", entry_stripped)
            match_parenth = regex.search(r"\(.*\)", entry_stripped) # take content in parenthesis

            if match_number is not None and match_number.group(0).strip() != "":

                if not first_number_match:
                    element_counter += 1        # switch to next element if number not true
                number = match_number.group(0).strip()

                self.ef.add_to_my_obj("ord_number", number, object_number=element_counter, only_filled=only_add_if_value)
                rest = rest.replace(number, "", 1)
                first_number_match = False
            if match_parenth is not None:
                parenth = match_parenth.group(0)
                self.ef.add_to_my_obj("category", parenth, object_number=element_counter, only_filled=only_add_if_value)
                rest = rest.replace(parenth, "", 1)

            rest_stripped = rest.strip()
            if rest_stripped != "":
                self.ef.add_to_my_obj("additional_info", rest_stripped, object_number=element_counter, only_filled=only_add_if_value)

    def parse_grossaktionaer(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        lines_split = origpost_red.split(';')
        only_add_if_value = True
        for line in lines_split:
            # testline
            # line = "Société Sidérurgique de Participations et d’ Approvisionnement en Charbons, par abréviation (Sidechar), Paris (ca.60,2 %)."

            # find parenthesis with 2 or more characters inside
            match_parenth = regex.findall(r"(\(.{2,}\))", line)
            found_parenth = None
            parenth_is_used = False
            organization = None
            location = None
            # find additional info in  each line and subtract it
            if match_parenth:
                found_parenth = match_parenth[-1].strip("., ") # find the last parenthesis grounp
                # if the parenthesis are at the end of line
                if line.strip()[-1] == ")" and not(len(found_parenth.replace(" ", "")) <= 5 and "%" in found_parenth): # exclude percentages from parenthesis matches
                    line = line.replace(found_parenth, "", 1)
                    parenth_is_used = True

            split_line = line.split(',')
            len_split_line = len(split_line)
            if len_split_line == 1:
                organization = line.strip("., ")
            else:
                organization = line.replace(split_line[-1], "", 1).strip("., ")
                location = split_line[-1].strip("., ")  # town

            self.ef.add_to_my_obj("organization", organization, object_number=element_counter,only_filled=only_add_if_value)
            self.ef.add_to_my_obj("location", location, object_number=element_counter,only_filled=only_add_if_value)
            if parenth_is_used:
                self.ef.add_to_my_obj("additional_info", found_parenth, object_number=element_counter,only_filled=only_add_if_value)
            element_counter += 1

        return True


    def parse_geschaeftsjahr(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        only_add_if_value = True
        final_jahr = []

        for text in content_texts:
            text_stripped = text.strip("., ")
            if text_stripped != "":
                if "bis" in text_stripped:
                    split_text = text_stripped.split('bis ')#
                    # regex.split('\.bis|\sbis\s', text_stripped)
                    if len(split_text) == 1:
                        final_jahr.append(split_text[0].strip())
                        continue
                    gesch_jahr_start = split_text[0].strip("( ")
                    gesch_jahr_stop = split_text[1].strip(" )")
                    self.ef.add_to_my_obj('gesch_jahr_start', gesch_jahr_start, object_number=element_counter,
                                          only_filled=only_add_if_value)
                    self.ef.add_to_my_obj('gesch_jahr_stop', gesch_jahr_stop, object_number=element_counter,
                                          only_filled=only_add_if_value)

                    if len(split_text) >= 3:
                        for rest in split_text[3:]:
                            if rest.strip() != "":
                                final_jahr.append(rest)
                else:
                    final_jahr.append(text_stripped)

        self.ef.add_to_my_obj('year', final_jahr, object_number=element_counter,only_filled=only_add_if_value)
        return True

    def parse_stimmrechtaktien(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # find last parenthesis and filter
        match_parenth = regex.findall(r"(\(.*?\))", origpost_red)
        found_parenth = None
        origpost_used = origpost_red
        # find additional info in  each line and subtract it
        if match_parenth:
            found_parenth = match_parenth[-1].strip("., ")  # find the last parenthesis grounp
            origpost_used = origpost_red.replace(found_parenth, "")  # update the orignpost used

        final_lines = []
        only_add_if_value = True
        skip = False
        final_text = ""
        for text_index, text in enumerate(content_texts):
            if text == "":
                continue
            text = text.replace("DM =", "DM 1 =").replace("DM=", "DM 1 =").replace("eine DM", "DM 1.-")
            if element_counter == 0 and "je nom" not in text.lower():
                self.ef.add_to_my_obj("additional_info", "".join(content_texts[text_index:]),
                                      object_number=element_counter,
                                      only_filled=only_add_if_value)
                break
            if skip:
                skip = False
                continue
            parse_aktie = regex.compile(r"(?P<nominal>[Jj]e[de]*?\s?(?P<nomvalue>[\d\s]*?)\s?[Aa]ktie[n]?)[^\d]*(?P<vote>[\d\s]*?)\s*?(?P<voteend>Stimme[n]*)")
            finding = parse_aktie.findall(text.replace("Stamm",""))
            if finding != []:
                finding = list(finding[0])
                if finding[1] == "":
                    finding[1] = "1"
                stck = {"kind": "Aktie",
                        "amount": finding[1],
                        "vote": finding[2].replace(" ", "").strip(),
                        "value": "",
                        "currency": "",
                        "rank": element_counter}
                self.ef.add_to_my_obj("entry", stck, object_number=element_counter,
                                      only_filled=only_add_if_value)
                element_counter += 1
                continue
            #text = 'Je nom. DM 50.- =1 Stimme.'
            parse_stimmrecht = regex.compile(r"(?P<nominal>[Jj]e[de]*?\s?(?P<nomvalue>[\d\s]*?)\s?nom\.)\s*?(?P<currency>[^\d]*)\s?(?P<value>[\d\s]*)\s*?(?P<waste>[^\dA-Za-z]*)\s{0,}(?P<kind>[A-Za-z.,\-\s]*)?[^\d\s]*\s{0,}(?P<vote>[\d]*)?\s{0,}(?P<voteend>Stimme[n]*)?")
            finding = parse_stimmrecht.findall(text.replace("DM", " DM").replace("RM"," RM"))
            # Special case "bzw."
            if finding and "bzw." in text:
                if "Stimm" not in text:
                    skip = True
                    text += content_texts[text_index+1]
                parse_bzw = regex.compile(r"(?P<nominal>[Jj]e[de]*?\s?(?P<nomvalue>[\d\s]*?)\s?nom\.)\s*?(?P<currency>[^\d]*)\s?(?P<value>[\d\s]*)\s*?[^\d]*\s*?(?P<value2>[\d\s]*)[^\dA-Za-z]*(?P<kind>[A-Za-z][A-Za-z.,\-\s]*)?[^\d\s]*\s{0,}(?P<vote>[\d]*)?\s{0,}[^\d]*\s{0,}(?P<vote2>[\d]*)\s{0,}(?P<voteend>Stimme[n]*)?")
                finding = parse_bzw.findall(text)
                finding = finding[0]
                if finding:
                    stck = {"kind": finding[5].strip(),
                            "amount": "1",
                            "vote": finding[6].replace(" ", "").strip(),
                            "value": finding[3].strip(),
                            "currency": finding[2].strip(),
                            "rank": element_counter}
                    self.ef.add_to_my_obj("entry", stck, object_number=element_counter,
                                          only_filled=only_add_if_value)
                    element_counter += 1
                    stck = {"kind": finding[5].strip(),
                            "amount": "1",
                            "vote": finding[7].replace(" ", "").strip(),
                            "value": finding[4].strip(),
                            "currency": finding[2].strip(),
                            "rank": element_counter}
                    self.ef.add_to_my_obj("entry", stck, object_number=element_counter,
                                          only_filled=only_add_if_value)
                    continue
            if not finding or finding[0][0] + finding[0][1] == "":
                final_text += text
                continue
            if final_text != "":
                self.ef.add_to_my_obj("additional_info", final_text, object_number=element_counter-1,
                                      only_filled=only_add_if_value)
                final_text = ""
            finding_next = None
            if finding[0][6] + finding[0][7] == "":
                if text_index == len(content_texts) - 1:
                    self.ef.add_to_my_obj("additional_info", text, object_number=element_counter,
                                          only_filled=only_add_if_value)
                    continue
                else:
                    finding_next = parse_stimmrecht.findall(text + " " + content_texts[text_index + 1])
            if finding_next:
                skip = True
                finding = finding_next
            finding = list(finding[0])
            if finding[5] == "":
                finding[5] = "nom."
            if finding[1] == "":
                finding[1] = "1"
            stck = {"kind": finding[5].strip(),
                    "amount": finding[1].strip(),
                    "vote": finding[6].replace(" ", "").strip(),
                    "value": finding[3].strip(),
                    "currency": finding[2].strip(),
                    "rank": element_counter}
            self.ef.add_to_my_obj("entry", stck, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1
        # match_akt = regex.search(r"\.\s?\-\s?Akt", text)
        # if match_saemtlsakt is not None:
        #    self.ef.add_to_my_obj("additional_info", text, object_number=element_counter, only_filled=only_add_if_value)
        #    element_counter += 1
        #    continue
        if final_text != "":
            self.ef.add_to_my_obj("additional_info", final_text, object_number=element_counter,
                                  only_filled=only_add_if_value)
        return True
        """
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # add extra splitting elements to each 'je' or 'Je'
        origpost_red_se = regex.sub(r"(Je |je )", r"~~~\1", origpost_red)

        split_text = origpost_red_se.split('~~~')
        # origpost_red = regex.sub(r"(\d\.)", r"\1~~~~", origpost_red)
        only_add_if_value = True

        for entry in split_text:
            if entry == "":
                continue
            match_sb = regex.search(r"Stimmrechtsbeschränkung:.*", entry)
            sbe = None
            if match_sb is not None:
                sbe = match_sb.group()
                sbe = sbe.replace("Stimmrechtsbeschränkung:", "", 1)
                entry = entry.replace(sbe, "").replace("Stimmrechtsbeschränkung:", "", 1)

            self.ef.add_to_my_obj("entry", entry, object_number=element_counter ,only_filled=only_add_if_value)
            self.ef.add_to_my_obj("Stimmrechtsbeschränkung", sbe, object_number=element_counter ,only_filled=only_add_if_value)
            element_counter += 1
        """

    def parse_boersennotiz(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)
        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # find last parenthesis and filter
        match_parenth = regex.findall(r"(\(.*?\))", origpost_red)
        found_parenth = None
        origpost_used = origpost_red
        # find additional info in  each line and subtract it
        if match_parenth:
            found_parenth = match_parenth[-1].strip("., ")  # find the last parenthesis grounp
            origpost_used = origpost_red.replace(found_parenth, "") # update the orignpost used

        # log all location elements
        only_add_if_value = True
        split_post = regex.split('u\.|und|,', origpost_used)
        for entry in split_post:
            entry_stripped = entry.strip("., ")
            if entry_stripped == None or entry_stripped == "":
                continue
            self.ef.add_to_my_obj("location", entry_stripped, object_number=element_counter, only_filled= only_add_if_value)
            element_counter += 1
        # log additional info in last parenthesis
        self.ef.add_to_my_obj("additional_info", found_parenth, object_number=element_counter, only_filled=only_add_if_value)

        return True

    def parse_stueckelung(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        # find last parenthesis and filter
        match_parenth = regex.findall(r"(\(.*?\))", origpost_red)
        found_parenth = None
        origpost_used = origpost_red
        # find additional info in  each line and subtract it
        if match_parenth:
            found_parenth = match_parenth[-1].strip("., ")  # find the last parenthesis grounp
            origpost_used = origpost_red.replace(found_parenth, "") # update the orignpost used

        final_lines = []
        only_add_if_value = True
        skip = False
        final_text = ""
        for text_index, text in enumerate(content_texts):
            if text.strip() == "":
                continue
            if skip:
                skip = False
                continue
            parse_stck = regex.compile(r"(?P<amount>[\d\s\.]*)\s*(?P<kind>[^\d]*?)[\s]?(?P<nominal>zu je|zuje|zu|je)\s{0,}(?P<currency>[^\d\s]*)\s{0,}(?P<value>[\d\s]*)")
            finding = parse_stck.findall(text.replace(" Stücke "," Aktien ").replace(" Stück "," Aktie ").replace("DM"," DM").replace("RM"," RM").replace("hfl"," hfl"))
            if not finding or finding[0][0]+finding[0][1] == "" or finding[0][0]+finding[0][4] == "":
                match_akt = regex.search(r"\.\s?\-\s?Akt", text)
                match_saemtlsakt, err_saemtlsakt = regu.fuzzy_search(
                    r"([Ss]ämtliche [Ss]tammaktien.*|[Ss]ämtliche [Aa]ktien.*)", text, err_number=1)
                if match_saemtlsakt is not None and match_akt is not None:
                    saemtl_res = match_saemtlsakt.group()
                    self.ef.add_to_my_obj("additional_info", saemtl_res, object_number=element_counter,
                                          only_filled=only_add_if_value)
                    reduced_text = text.replace(saemtl_res, "")
                    final_lines.append(reduced_text)
                if match_saemtlsakt or "Börse" in text or "Besondere" in text:
                    self.ef.add_to_my_obj("additional_info", "".join(content_texts[text_index:]), object_number=element_counter,
                                          only_filled=only_add_if_value)
                    element_counter += 1
                    break
                if "(" in text:
                    self.ef.add_to_my_obj("additional_info", text, object_number=element_counter-1,
                                          only_filled=only_add_if_value)
                else:
                    final_text += text
                continue
            finding_next = None
            if finding[0][2] == "" or (finding[0][2] == "zu" and finding[0][3] == ""):
                #test =  '2 638 514 Inh. - bzw. Namensaktien zuje FF 75.-'
                if text_index == len(content_texts) - 1:
                    self.ef.add_to_my_obj("additional_info", text, object_number=element_counter,
                                          only_filled=only_add_if_value)
                    continue
                else:
                    finding_next = parse_stck.findall(text +" "+ content_texts[text_index + 1])
            if finding[0][3]+finding[0][4] == "":
                if text_index == len(content_texts) - 1:
                    self.ef.add_to_my_obj("additional_info", text, object_number=element_counter,
                                          only_filled=only_add_if_value)
                    continue
                else:
                    finding_next = parse_stck.findall(text +" "+ content_texts[text_index + 1])
            if finding_next:
                skip = True
                finding = finding_next
            stck = {"amount": finding[0][0].replace("."," ").strip(),
                     "kind": finding[0][1].replace(" ","").strip(),
                     "nominal": "zu je",
                     "currency": finding[0][3],
                     "value": finding[0][4],
                     "rank":element_counter}
            self.ef.add_to_my_obj("entry", stck, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1
           # match_akt = regex.search(r"\.\s?\-\s?Akt", text)
            #if match_saemtlsakt is not None:
            #    self.ef.add_to_my_obj("additional_info", text, object_number=element_counter, only_filled=only_add_if_value)
            #    element_counter += 1
            #    continue
        if final_text != "":
            self.ef.add_to_my_obj("additional_info", final_text, object_number=element_counter,
                                  only_filled=only_add_if_value)
        return True



