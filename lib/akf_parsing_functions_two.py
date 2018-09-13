from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from .data_helper import DataHelper as dh
from .akf_parsing_functions_common import AKFCommonParsingFunctions as cf

import regex


class AkfParsingFunctionsTwo(object):

    def __init__(self, endobject_factory, output_analyzer):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_PARSER_AKF_FN_TWO, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

        self.cpr.print("init akf parsing functions two")

        self.ef = endobject_factory
        self.output_analyzer = output_analyzer

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
                entry_final = regex.sub(r"beide\s?\.?", "", entry_stripped).strip()
                final_entries.append((ADDITIONAL_INFO_BOTH, entry_final, "", ""))
                continue
            if "sämtl" in entry_stripped:
                entry_final = regex.sub(r"sämtl\s?\.?", "", entry_stripped).strip()
                final_entries.append((ADDITIONAL_INFO_ALL_PREV, entry_final, "", ""))
                continue

            entry_split = entry_stripped.split(',')
            bank = ""
            city = ""
            title = ""
            rest_info = ""
            for fragment_index, fragment in enumerate(entry_split):
                if fragment_index == 0:
                    bank = fragment
                elif fragment_index == 1:
                    city = fragment
                elif fragment_index >= 2:
                    rest_info += fragment
            final_entries.append((DEFAULT_ENTRY, bank, city, title))

        # reverse list for better processing
        reverse_fe = final_entries.__reversed__()
        current_additional_info = ""
        current_info_index = None
        current_entry_type = None
        final_list = []
        for item_index, item in enumerate(reverse_fe):
            entry_type, entryorbank, city, title = item
            # change current additional info
            if entry_type == ADDITIONAL_INFO_BOTH or entry_type == ADDITIONAL_INFO_ALL_PREV:
                current_info_index = item_index
                current_additional_info = entryorbank
            elif entry_type == DEFAULT_ENTRY:
                templist = [(entryorbank, city, title, current_additional_info)]
                templist.extend(final_list)
                final_list = templist

            # end 'beide'-entry because it's over after 2 iterations
            if current_entry_type == ADDITIONAL_INFO_BOTH and item_index-current_info_index >= 1:
                current_info_index = None
                current_additional_info = ""

        # finally note the entries to output
        only_add_if_value = True
        for entry in final_list:
            bank, city, title, add_info = entry
            if add_info != "" and add_info != None:
                city += add_info
            self.ef.add_to_my_obj("bank", bank, object_number=element_counter, only_filled=only_add_if_value)
            self.ef.add_to_my_obj("city", city, object_number=element_counter, only_filled=only_add_if_value)
            self.ef.add_to_my_obj("title", title, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1

        return True

    def parse_grundkapital(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # todo validate other currencies than 'DM'
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)

        final_entries = []
        current_ref_index = -1
        for text_index, text in enumerate(content_texts):
            match_dm = regex.match(r"^DM.*", text)
            if match_dm is not None:
                final_entries.append(text)
                # get last entry as ref
                current_ref_index += 1
            else:
                if current_ref_index == -1:
                    # special case there was no leading dm entry
                    final_entries.append(text)
                    # get last entry as ref
                    current_ref_index += 1

                # update ref
                final_entries[current_ref_index] += " "+text

        only_add_if_value = True
        for entry in final_entries:
            match_entry = regex.match(r"(?<amount>.*?\.\-)"     # match until first '.-'
                                      r"(?<add_info>.*)",       # match the rest string
                                      entry)
            if match_entry is None:
                self.ef.add_to_my_obj("amount", entry, object_number=element_counter, only_filled=only_add_if_value)
                element_counter += 1
                continue

            amount = dh.strip_if_not_none(match_entry.group("amount"), "")
            add_info = dh.strip_if_not_none(match_entry.group("add_info"), "")

            self.ef.add_to_my_obj("amount", amount, object_number=element_counter, only_filled= only_add_if_value)
            self.ef.add_to_my_obj("additional_info", add_info, object_number=element_counter, only_filled= only_add_if_value)
            element_counter += 1

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
        for entry in content_texts:
            match_number = regex.match(r"\d*", entry)
            match_parenth = regex.search(r"\(.*\)", entry)

            if match_number is not None:
                number = match_number.group(0)
                self.ef.add_to_my_obj("ord_number", number, object_number=element_counter, only_filled=only_add_if_value)
            if match_parenth is not None:
                parenth = match_parenth.group(0)
                self.ef.add_to_my_obj("additional_info", parenth, object_number=element_counter, only_filled=only_add_if_value)
            if match_number is not None or match_parenth is not None:
                element_counter += 1

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

            match_parenth = regex.findall(r"(\(.*?\))", line)
            found_parenth = None
            organization = None
            location = None
            # find additional info in  each line and subtract it
            if match_parenth:
                found_parenth = match_parenth[-1].strip("., ") # find the last parenthesis grounp
                line = line.replace(found_parenth, "")

            split_line = line.split(',')
            len_split_line = len(split_line)
            if len_split_line == 1:
                organization = line.strip("., ")
            else:
                organization = line.replace(split_line[-1], "").strip("., ")
                location = split_line[-1].strip("., ")  # town

            self.ef.add_to_my_obj("organization", organization, object_number=element_counter,only_filled=only_add_if_value)
            self.ef.add_to_my_obj("location", location, object_number=element_counter,only_filled=only_add_if_value)
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

    def parse_stimmrechtaktien(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
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
                entry = entry.replace(sbe, "")

            self.ef.add_to_my_obj("entry", entry, object_number=element_counter ,only_filled=only_add_if_value)
            self.ef.add_to_my_obj("Stimmrechtsbeschränkung", sbe, object_number=element_counter ,only_filled=only_add_if_value)
            element_counter += 1

        return True

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

        for text_index, text in enumerate(content_texts):
            if text.strip() == "":
                continue
            match_akt = regex.search(r"\.\s?\-\s?Akt", text)
            match_saemtlsakt = regex.search(r"[Ss]ämtliche [Ss]tammaktien", text)
            if match_saemtlsakt is not None:
                self.ef.add_to_my_obj("additional_info", text, object_number=element_counter, only_filled=only_add_if_value)
                element_counter += 1
                continue
            if match_akt is not None:
                final_lines.append(text)
            else:
                if len(final_lines) == 0:
                    final_lines.append(text)
                    continue
                final_lines[-1] = final_lines[-1] + text

        for line in final_lines:
            self.ef.add_to_my_obj("entry", line, object_number=element_counter, only_filled=only_add_if_value)
            element_counter += 1

        return True



    def parse_aktienkurse(self, real_start_tag, content_texts, content_lines, feature_lines, segmentation_class):
        # get basic data
        element_counter = 0
        origpost, origpost_red, element_counter, content_texts = \
            cf.add_check_element(self, content_texts, real_start_tag, segmentation_class, element_counter)

        # logme
        self.output_analyzer.log_segment_information(segmentation_class.segment_tag, content_texts, real_start_tag)
