import regex
from .data_helper import DataHelper as dh
from akf_corelib.regex_util import RegexUtil as regu


class AKFCommonParsingFunctions(object):
    """
    This is a holder object for commonly ocuring parsing
    steps in the akf-context used by akf-parsing-functions-(number)
    """


    @staticmethod
    def parse_grundkapital_line(text, found_main_amount, element_counter, only_add_if_value, additional_info):
        my_return_object = {}
        text_stripped = text.strip()
        match_dm = regex.search(r"^(?P<currency>\D{1,4})(?P<amount>[\d\.\-\s]*)", text)
        if found_main_amount is False and match_dm is not None and \
            "Autorisiertes Kapital:" not in text and "Ausgegebenes Kapital:" not in text:

            currency = match_dm.group("currency").strip(",. ")
            amount = match_dm.group("amount")
            if (currency is not None and currency != "") or only_add_if_value is False:
                my_return_object["currency"] = currency
            if (amount is not None and amount != "") or only_add_if_value is False:
                my_return_object["amount"] = amount
            found_main_amount = True
        else:

            # DM34000000. - Inh. - St. - Akt.
            # DM266000. - Nam. - St. - Akt.
            # DM1718400. - St. - Akt.
            # DM21600. - Vorz. - Akt.
            # DM 2 000 000.- St.-Akt.,
            # DM 60 000.- Vorz.-Akt. Lit.A,
            # DM 9 000.- Vorz.-Akt. Lit.B.

            if "Akt." in text:
                match_entry = regex.search(r"^(?P<currency>\D{1,4})(?P<amount>[\d\.\-\s]*)(?P<rest_info>.*)", text)
                addt_currency = ""
                addt_amount = ""
                addt_rest_info = ""
                final_object = {}

                if match_entry:
                    addt_currency = match_entry.group("currency")
                    addt_amount = match_entry.group("amount")
                    addt_rest_info = match_entry.group("rest_info")
                    final_object = {
                        "currency": addt_currency,
                        "amount": addt_amount,
                        "rest_info": addt_rest_info
                    }
                if "Inh." in text and "St." in text:
                    # Inhaber Stammaktien
                    my_return_object["Inhaber-Stammaktien"] = final_object


                elif "Nam." in text and "St." in text:
                    # Nanhafte Stammaktien
                    my_return_object["Namhafte-Stammaktien"] = final_object

                elif "St." in text:
                    # Stammaktien
                    my_return_object["Stammaktien"] = final_object

                elif "Vorz." in text:
                    my_return_object["Vorzeigeaktien"] = final_object

                else:
                    # not recognized just add as additional info
                    additional_info.append(text_stripped)
                # element_counter += 1
            else:
                additional_info.append(text_stripped)

        return my_return_object, found_main_amount, element_counter, only_add_if_value, additional_info

    @staticmethod
    def parse_general_and_keys(content_texts, join_separated_lines=False, current_key_initial_value=None, abc_sections=False):
        """
        Separates an array of texts into categories.
        Categories are found by leading tag followed by ':'

        :param content_texts: texts to check
        :param join_separated_lines: lines which have trailing '-'
                are joined (usually not needed use 'join_separated_lines' instead)
        :param current_key_initial_value: used key initial value (for "General info" key)
        :param abc_sections: 'a) section1' 'b) section2' use this as additional splitting
        :return: a dictionary with general_content as well as the seperated keytag content
        """
        final_items = {}

        if current_key_initial_value is not None:
            current_key = current_key_initial_value
        else:
            current_key = "general"

        len_content_texts = len(content_texts)

        for text_index, text in enumerate(content_texts):
            next_text = None
            if text_index < len_content_texts-1:
                next_text = content_texts[text_index+1].strip()
            #if "Altona" in text:
            #    print("asd")

            abc_found = False
            if abc_sections:
                starts_with_abc = regex.search("^\w\s?\)", text)
                if starts_with_abc:
                    current_key = starts_with_abc[0]
                    if current_key.strip() != "":
                        # if there is a multikey give it an additional counter
                        key_count = list(final_items.keys()).count(current_key)

                        # remove current key from text
                        text = text.replace(current_key, "", 1).strip()
                        abc_found = True

                        if key_count >= 1:
                            current_key = current_key + "_" + str(key_count + 1)

            if ":" in text and abc_found is False:
                # find out if there is a new category
                #current_key = text.split(":")[0]
                text_with_tag = regex.sub(":", "┇┇:", text)
                current_key_sp = regex.split(r",|;|:", text_with_tag)
                new_key_found = None
                for key_to_check in current_key_sp:
                    if "┇┇" in key_to_check:
                        new_key_found = key_to_check.replace("┇┇", "")
                        # if there is a multikey give it an additional counter
                        keys_list = list(final_items.keys())
                        key_count = 0
                        for listkey in keys_list:
                            if new_key_found in listkey:
                                key_count += 1

                        # key_count = list(final_items.keys()).count(new_key_found)

                        # remove current key from text
                        # text = text.replace(current_key, "").replace(":", "") # can lead to errors (double replacement in sth like  Lokomotive: Dampf-Lokomotive)
                        new_key_found = regex.sub(regex.escape(new_key_found) + "\s?" + ":", "", new_key_found)
                        if new_key_found.strip() == "":
                            continue
                        starts_with_und = regex.search("^und\s", new_key_found.strip())
                        trails_with_und = regex.search("\sund$", new_key_found.strip())
                        if starts_with_und:
                            new_key_found = new_key_found.replace(starts_with_und.group(), "", 1).strip()
                        if trails_with_und:
                            new_key_found = new_key_found.replace(trails_with_und.group(), "", 1).strip()

                        if key_count >= 1:
                            current_key = (new_key_found + "_" + str(key_count + 1)).strip()
                        else:
                            current_key = new_key_found.strip()

                    else:
                        key_to_check_stripped = key_to_check.strip()
                        if key_to_check == "":
                            continue
                        if current_key not in final_items.keys():
                            final_items[current_key] = []
                            final_items[current_key].append(key_to_check_stripped)
                        else:
                            final_items[current_key].append(key_to_check_stripped)

                continue

            text = text.strip()

            # add key entry if it doesn't exist
            if current_key not in final_items.keys():
                final_items[current_key] = []

            # join separated words if there are some
            if join_separated_lines:
                if len(text) >= 2 and "-" in text[-1]:
                    if next_text is not None and len(next_text) >=1:
                        # if the next starting letter is uppercase don't do the joining (assuming it's a '-'
                        # separated Name like "Jan-Philipp")
                        if not next_text[0].isupper():
                            text = text[0:len(text)-1]
                        if text != "":
                            # add the text without space separator cause next line will directly be directly joined
                            final_items[current_key].append(text)
                            continue

            #add_space = " "
            # remove space added on last line
            #if text_index >= len_content_texts-1:
            #    add_space = ""

            # add line to final items
            if text != "":
                final_items[current_key].append(text)

        return final_items



    @staticmethod
    def parse_id_location(origpost_red):
        """
        Parses a text for common text block like
        (24a) Hamburg 13, Mittelweg 180
        :param origpost_red:
        :return: tuple with numID, city, street, street_number, additional_info
        """
        #if "Zementfabrik" in origpost_red or "Rheinfelden" in origpost_red or "Bietigheim" in origpost_red:
            #print("asd")

            # (17b) Rheinfelden (Baden);
            # (22c) Zementfabrik bei Ober- kassel (Siegkr.)
            # (14a) Bietigheim uWürtt (Württ.).
            # 648 Wächtersbach (Hessen), Postfach 20   ## resembles case from 1963 on
            # 648 Wächtersbach (Hessen) 22, Postfach 20   ## resembles case from 1963 on

        # Sometimes the text contains an additional Sitz-preamble although segmented ok
        origpost_red = regex.sub("^Sitz", "", origpost_red.strip()).strip()
        # do first match
        match = regex.match(r"(?<NumID>\(.*?\))"                 # find starting number (non greedy to stop at first closing parenthesis)
                            r"(?<Location>.*?(,|\.\s)|.*?)"         # find location string
                            r"(?<Rest>.*+)",                     # just get the rest which is usually streetname and number, but has other possibilities
                            origpost_red)
        if match is None:
            if len(origpost_red) >= 3:
                # special case from years 1963 on regex isn't triggered
                op_r_split = origpost_red.split(',')
                found_ctr = 0
                found_nums = ""
                num_found = False
                found_city = ""
                found_street = []
                found_rest = []
                for element in op_r_split:
                    element_strip = element.strip()
                    if element_strip == "":
                        continue
                    if found_ctr == 0:
                        # it's ordnumber city and some other number optionally '51 Aachen 2' or smth
                        element_split = element.split(' ')
                        for els in element_split:
                            els_strip = els.strip()
                            if els_strip.isnumeric() and num_found is False:
                                found_nums = els_strip
                                num_found = True
                            else:
                                found_city += " " + els_strip

                    elif found_ctr == 1:
                        # it's smth
                        found_street = element_strip
                    else:
                        # rest
                        found_rest.append(element_strip)
                    found_ctr += 1
                city = dh.strip_if_not_none(found_city, ", ")

                return found_nums, city, found_street, None, found_rest

            return None, None, None, None, None

        numID = dh.strip_if_not_none(match.group("NumID"), ", ")
        city = dh.strip_if_not_none(match.group("Location"), ", ")
        rest = dh.strip_if_not_none(match.group("Rest"), ". ")

        if rest.strip() == ")":
            rest = ""
            city += ")"

        # parse the rest if there is some
        if rest != "" and rest is not None:
            match_rest = regex.match(r"(?<Street>.*?)" # match all characters non-greedy 
                                     r"(?<Number>[0-9]+[-\/]*[0-9]*[abcdefgh]*)"
                                     r"(?<Rest>.*+)",
                                     rest)
            if match_rest is not None:
                street = dh.strip_if_not_none(match_rest.group("Street"), "")
                street_number = dh.strip_if_not_none(match_rest.group("Number"), ",\.")
                additional_info = dh.strip_if_not_none(match_rest.group("Rest"), ")., ")
                return numID, city, street, street_number, additional_info
            else:
                additional_info = None
                if city.strip() == "":
                    city = rest
                else:
                    additional_info = dh.strip_if_not_none(rest, ")., ")

                return numID, city, None, None, additional_info

        return numID, city, None, None, None


    @staticmethod
    def parse_persons(origpost_red, dictionary_handler, use_dictionary):
        """
        Parses a ';' separated list of persons i.e.
        - Karl Markmann, Kiel-Holtenau, Vorstand, (ehem. direktor);
        - Dr. Paul Leverkuehn, Hamburg.

        :param origpost_red:
        :return: a list of name, city, title, rest_info tuples
        """
        split_post = origpost_red.split(';')
        final_entries = []
        for index, entry in enumerate(split_post):
            entry_stripped = entry.strip()
            if entry_stripped == "":
                continue

            print("Person:", entry_stripped)
            entry_split = entry_stripped.split(',')
            name = ""
            first_name = ""
            last_name = ""
            city = ""
            title = ""
            funct = ""
            rest_info = []
            for fragment_index, fragment in enumerate(entry_split):
                if fragment_index == 0:
                    name, title = dictionary_handler.diff_name_title(fragment.strip())

                    name_split = name.split(" ")
                    if " von " in name:
                        first_name = name_split[0]
                        last_name = name.replace(first_name,"")

                    else:
                        # just take the last word as nachname
                        first_name = name.replace(name_split[-1], "").strip()
                        last_name = name_split[-1]



                    #print("vorname", vorname, "name", name)
                    #name = fragment.strip()
                    #print("asd")
                elif fragment_index == 1:
                    city = fragment.strip()
                elif fragment_index == 2:
                    funct = fragment.strip() # that's probably position
                elif fragment_index >= 3:
                    rest_info.append(fragment.strip())
            #print("Parsed:", (name, city, title, funct, rest_info))

            final_entries.append((name, first_name,last_name, city, title, funct, rest_info))
        return final_entries

    @staticmethod
    def parse_kapital_line(rec_tag, text, detailed_parsing=True):
        """
        Parses a common 'Kapital' line - like in 'Beteiligungen'
        examples for 'text' are whereas 'rec_tag' is usually 'Kapital:':
        "Kapital: DM 240 000.- (25 %)."
        "Kapital: DM 500 000.- (71,8 %)"
        "Kapital: sfrs. 30 000 000.- (25 %)."

        :param rec_tag: the tag associated with topic in the referred text
        :param text: text which contains the content and
        :param detailed_parsing: create a more detailed parsed object
        :return: simple_text_result, complex_result_object (comes with detailed parsing)
        """

        text_reduced = text.replace(rec_tag, "").strip()
        #text_reduced = 'DM 2 500 000, - (100 %).' # erronous case 2 500
        #text_reduced = '40 532 400.-'
        # if not activated detailed parsing just return simple solution
        if not detailed_parsing:
            return text_reduced, None

        # continue with detailed parsing here
        match_currency = regex.search(r"^[a-zA-Z\p{Sc}\.]+", text_reduced)
        #match_numbers = regex.search(r"[\d\s]+(\.\s\-|\.\-|,\s-)", text_reduced) # old numbers match

        match_numbers = regex.search(r"[\d\s]+", text_reduced)
        #match_numbers_addendum = regex.search(r"[\d\s]+", text_reduced)   # could be tested if addendum needed


        #match_numbers = regex.search(r"[\b\s*\d+]*", text_reduced)
        match_parenthesis = regex.search(r"\(.+\)", text_reduced)

        return_object = {}
        if match_currency:
            res_currency = match_currency.group().strip()
            return_object['currency'] = res_currency
        if match_numbers:
            res_numbers = match_numbers.group().strip()
            return_object['amount'] = res_numbers

        if match_parenthesis:
            res_parenthesis = match_parenthesis.group().strip()
            return_object['add_info'] = res_parenthesis

        #print("orig:", text_reduced)
        #print("prsd:", return_object)

        # return a simple and more sophisticated parsing
        return text_reduced, return_object

    @staticmethod
    def parse_dividenden_line(rec_tag, text, detailed_parsing=True):
        """
        Parses a common 'Dividenden' line - like in 'Beteiligungen'
        examples for 'text' are whereas 'rec_tag' is usually 'Dividenden ab':
        "Dividenden ab 1949/50: 0, 0, 0, 0,0%"
        "Dividenden ab 1950: 4, 4, 4, 4, 4%."
        "Dividenden ab 1950: 0, 0, 3, 3, 4%"

        :param rec_tag: the tag associated with topic in the referred text
        :param text: text which contains the content and
        :param detailed_parsing: create a more detailed parsed object
        :return: simple_text_result, complex_result_object (comes with detailed parsing)
        """

        text_reduced = text.replace(rec_tag, "").strip()

        # if not activated detailed parsing just return simple solution
        if not detailed_parsing:
            return text_reduced, None

        return_object = {}
        text_red_split = regex.split(r':|,', text_reduced)

        for text_index, text_entry in enumerate(text_red_split):
            if text_index == 0:
                return_object['year'] = text_entry.strip(",. ")
            else:
                if 'percentages' not in return_object.keys():
                    return_object['percentages'] = []

                stripped_text = text_entry.strip(",.% ")
                if stripped_text == "":
                    continue
                return_object['percentages'].append(stripped_text)


        return text_reduced, return_object


    @staticmethod
    def add_check_element(topclass, content_texts, real_start_tag, segmentation_class, element_counter):

        joined_texts = dh.join_separated_lines(content_texts)  # join dash separated texts
        joined_texts = dh.join_separated_lines_parenthesis(joined_texts) # join divided parenthesis blocks
        origpost, origpost_red = dh.create_stringified_linearray(joined_texts)   # final reduced array for further processing

        if topclass.config.ADD_INFO_ENTRY_TO_OUTPUT:
            # care!: origpost is added after joining seperated lines!
            topclass.ef.add_to_my_obj("origpost", origpost_red, object_number=element_counter)
            topclass.ef.add_to_my_obj("type", segmentation_class.segment_tag, object_number=element_counter)
            element_counter += 1

        return origpost, origpost_red, element_counter, joined_texts


    @staticmethod
    def match_common_block(content_texts, content_lines, complex_parsing, additional_categories):
        """
        This is an algorithm to fetch content groups and create blocks which are parsed, parsing of these
        blocks can be activated by naming the category of the block in 'additional categories'

        Example input for content lines (Roman Numbers in parenthesis are added for description here):
        (I.) Flachglasbearbeitungs -Gesellschaft mbH. (Flabeg), Fürth-Kunzendorf
        Kapital: DM 300 000. - (100 %)
        (II.) Vereinigte Vopelius’sche und Wentzel’sche Glashütten GmbH.,St.Ingbert Saar)
        Kapital: ffrs. 118 000 000.- (32,2 %) Thermolux Glas GmbH., Bergisch Gladbach Kapital:DM20000.-(50%)

        This creates 2 blocks by knowing there was already a category (like Kapital) and a text without category is following
        Roman numbers indicate the recognized block starts here.



        :param content_texts: input list which contains the text lines
        :param content_lines: line info list which contains additional infos
        :param complex_parsing: within the additional categories, a more complex parsing approach is used
        :param additional_categories: list of the additional categories which should be recognized as such (e.g.
               'kapital' or 'dividenden'
        :return: dictionary with combined blocks and parsed sub-entries
        """

        # check the additional categories field which additional categories can be found
        dict_used_categories = {}
        for entry in additional_categories:
            entry_low = entry.lower()
            dict_used_categories[entry_low] = True

        # create a writable results array
        results = []
        current_object = {}
        category_hit = False
        ended_with_only_text = False

        for text_index, text in enumerate(content_texts):
            text_stripped = text.strip()
            if text_stripped == "":
                continue
            ended_with_only_text = False # refresh ended with text property
            #if text_index == len(content_texts)-1:
            #    print("debug last element")

            if 'kapital' in dict_used_categories:
                match_kapital, err_kapital = regu.fuzzy_search(r"^Kapital\s?:", text_stripped, err_number=1)
                if match_kapital:
                    my_result = match_kapital.group()
                    if 'kapital' in current_object.keys():
                        # append old object
                        results.append(current_object)
                        # refresh current object if already in keys
                        current_object = {}

                    simple, complex = AKFCommonParsingFunctions.parse_kapital_line(my_result, text_stripped,
                                                            detailed_parsing=complex_parsing)
                    current_object['kapital'] = complex if complex_parsing else simple  # conditionally set val
                    category_hit = True  # indicate that an additional subcategory was already found in current object

                    continue
            if 'dividenden' in dict_used_categories:

                match_dividenden, err_divid = regu.fuzzy_search(r"^Dividenden\s?(:|ab)",
                                                                text_stripped, err_number=1)
                if match_dividenden:
                    my_result = match_dividenden.group()
                    if 'dividenden' in current_object.keys():
                        # append old object
                        results.append(current_object)
                        # refresh current object if already in keys
                        current_object = {}

                    simple, complex = AKFCommonParsingFunctions.parse_dividenden_line(my_result, text_stripped,
                                                                            detailed_parsing=complex_parsing)
                    current_object['dividenden'] =  complex if complex_parsing else simple  # conditionally set val
                    category_hit = True  # indicate that an additional subcategory was already found in current object

                    continue

            if 'beteiligungen' in dict_used_categories:

                match_bet, err_bet = regu.fuzzy_search(r"^(Beteiligungen|Beteiligung|Beteil\.)\s?(:|ab)",
                                                                text_stripped, err_number=0)
                if match_bet:
                    my_result = match_bet.group().strip()
                    if 'beteiligungen' in current_object.keys():
                        # append old object
                        results.append(current_object)
                        # refresh current object if already in keys
                        current_object = {}

                    #simple, complex = AKFCommonParsingFunctions.parse_dividenden_line(my_result, text_stripped,
                     #                                                       detailed_parsing=complex_parsing)
                    current_object['beteiligungen'] = text_stripped.replace(my_result, "", 1).strip()  # conditionally set val
                    category_hit = True  # indicate that an additional subcategory was already found in current object

                    continue

            if 'parenthesis' in dict_used_categories:

                match_parenth = regex.search(r"^\(\.*\)", text_stripped)

                if match_parenth:
                    my_result = match_parenth.group()
                    if 'parenthesis' in current_object.keys():
                        # append old object
                        results.append(current_object)
                        # refresh current object if already in keys
                        current_object = {}

                    current_object['add_info'] = my_result
                    category_hit = True  # indicate that an additional subcategory was already found in current object
                    continue


            word_info = content_lines[text_index]['words']

            # if shorter line (wordcount) (skip this if a text and a category was already found 'category hit')
            if not category_hit and len(word_info) <= 2:
                if 'text' not in current_object.keys():
                    current_object['text'] = text_stripped
                else:
                    if len(current_object['text']) >= 1 and current_object['text'][-1] == "-":
                        current_object['text'] += " " + text_stripped # todo needed w/o space ? remove case  if ok
                    else:
                        current_object['text'] += " " + text_stripped

                    current_object['text'] = current_object['text'].strip()
                ended_with_only_text = True # indicate last line ended with text
                continue

            # if other cases don't match add text to new object
            if current_object is None or category_hit is True:
                results.append(current_object) # append existing content
                current_object = {} # create new holder
                current_object['text'] = ""
            if "text" in current_object.keys():
                if len(current_object['text']) >= 1 and current_object['text'][-1] == "-":
                    current_object['text'] += " " + text_stripped # todo needed w/o space ? remove case  if ok
                else:
                    current_object['text'] += " " + text_stripped
                ended_with_only_text = True # indicate last line ended with text
            else:
                current_object['text'] = text_stripped
                ended_with_only_text = True # indicate last line ended with text

            current_object['text'] = current_object['text'].strip()

            category_hit = False  # indicate that there has been no category assigned yet

        if category_hit is True:
            # last element was a category hit and therefore still has to be added
            results.append(current_object)  # append existing content
        if ended_with_only_text is True:
            results.append(current_object)  # last object was not applied because it ended with text

        # check if object was not appended sh
        #if results is None:
        #    print("asd")
        #    return 5

        return results

    @staticmethod
    def parse_anleihe(input_text, complex_parsing=True):
        """
        Parse line for anleihe in complex or simple mode
        simple mode just returns the line at the moment
        :param input_text: input_text
        :param complex_parsing: if true complex solution is created
        :return: simple parsed, complex parsed object
        """
        # Example
        # Restverpflichtung 1 5 % Franken-Anleihe von 1927

        if complex_parsing is False:
            # possible to add some simple parsing here
            return input_text, None

        match_percentag = regex.search("[\d\,\.\-\/\s]*\s?%", input_text)
        match_vonyer = regex.search("von\s\d*", input_text)
        percentage = match_percentag.group() if match_percentag else ""
        year = match_vonyer.group() if match_vonyer else ""

        rest = input_text.replace(percentage, "").replace(year, "").strip()
        match_lead_words = regex.search("^[a-zA-ZäÄüÜöÖß\-]*", rest)
        add_info_start = match_lead_words.group() if match_lead_words else ""
        rest_2 = rest.replace(add_info_start, "").strip()
        match_lead_num = regex.search("^[\d\,\.\-\/]*", rest_2)
        lead_num = match_lead_num.group() if match_lead_num else ""
        rest_3 = rest_2.replace(lead_num, "").strip()

        return_object = {}
        return_object['percentage'] = percentage.strip()
        return_object['year'] = year.strip()
        return_object['amount'] = lead_num.strip()
        return_object['name'] = rest_3.strip()
        return_object['add_info'] = add_info_start.strip()

        return input_text, return_object

    @staticmethod
    def parse_emissionsbetrag(input_text, complex_parsing=True):
        """
        Parse line for emissionsbetrag in complex or simple mode
        simple mode just returns the line at the moment
        :param input_text: input_text
        :param complex_parsing: if true complex solution is created
        :return: simple parsed, complex parsed object
        """
        # Example
        # "DM 15 000 000.-."
        # "RM 15 000 000.-."
        if complex_parsing is False:
            # possible to add some simple parsing here
            return input_text, None

        current_text = input_text
        match_currency = regex.search("^(.*?)\s", current_text)  # match until first space
        currency = match_currency.group() if match_currency else ""
        current_text = current_text.replace(currency, "")
        match_amount = regex.search("[\d\s\-\.\,]+", current_text)  # does this get first occurence

        amount = match_amount.group() if match_amount else ""
        current_text = current_text.replace(amount, "")
        if "Umtauschrecht:" in current_text:
            current_text.replace("Umtauschrecht:","")

        # current_text = current_text.replace(percentage,"").replace(year,"").strip()
        return_object = {}
        return_object['currency'] = currency.strip(',. ')
        return_object['amount'] = amount.strip(',. ')
        return_object['rest_info'] = current_text.strip(',. ')

        # complex parsing here
        return input_text, return_object

    @staticmethod
    def parse_umsatz(input_text, complex_parsing=True):
        """
        Parse line for umsatz in complex or simple mode
        simple mode just returns the line at the moment
        :param input_text: input_text
        :param complex_parsing: if true complex solution is created
        :return: simple parsed, complex parsed object
        """
        # Example
        # " DM 4,4 Mill."
        # " DM 1,301 Mill."

        if complex_parsing is False:
            # possible to add some simple parsing here
            return input_text, None

        current_text = input_text.strip()
        match_currency = regex.search("^(.*?)\s", current_text)  # match until first space
        currency = match_currency.group() if match_currency else ""
        current_text = current_text.replace(currency, "")
        match_amount = regex.search("[\d\s\-\.\,]+", current_text)  # does this get first occurence

        amount = match_amount.group() if match_amount else ""
        current_text = current_text.replace(amount, "")

        # current_text = current_text.replace(percentage,"").replace(year,"").strip()
        return_object = {}
        return_object['currency'] = currency.strip(',. ')
        return_object['amount'] = amount.strip(',. ')
        return_object['rest_info'] = current_text.strip(',. ')

        # complex parsing here
        return input_text, return_object


    @staticmethod
    def parse_kurs_von_zuteilungsrechten(input_text, complex_parsing=True):
        """
        Parse line for kurs von zahlungsrechten in complex or simple mode
        simple mode just returns the line at the moment
        :param input_text: input_text
        :param complex_parsing: if true complex solution is created
        :return: simple parsed, complex parsed object
        """
        # Example
        #  Inh.-Akt. 6.10.1955 NGS: 249 DM /n Nam.-Akt. 10.10.1955 NGS: 239 DM.
        #  68,18 % Einz.: NGS am 10.10.1955: \n 20 DM (Berlin)
        #  Berlin am 10.10.1955 NGS: \n Nam.-St.-Akt.Lit.A : 12 DM \n Berlin am 10.10.1955 NGS: \n Nam.-St.-Akt.Lit.B: 7 DM
        # 'St.-Akt.: Berlin, 10.10.1955 NGS: 32 %'

        if complex_parsing is False:
            # possible to add some simple parsing here
            return input_text, None

        current_text = input_text
        text_generic = AKFCommonParsingFunctions.parse_general_and_keys([current_text],
                                            join_separated_lines=True, current_key_initial_value="general_info",
                                            abc_sections=True)
        final_info = {}

        for entry_key in text_generic:
            values_at_key = text_generic[entry_key]
            final_info[entry_key] = {
                     'perc': [],
                     'year': [],
                     'rest': []
                    }
            for value in values_at_key:
                match_percentag = regex.search("[\d\,\.\-\/]*\s?%?", value)
                perc = None
                if match_percentag:
                    perc = match_percentag.group()
                    value = value.replace(perc, "¦", 1).strip()

                match_year = regex.search("am.*\d\d\d\d", value)
                year = None
                if match_year:
                    year = match_year.group()
                    value = value.replace(year, "¦", 1).strip()

                value_split = value.split('¦')
                values_final = []
                for val in value_split:
                    val_strip = val.strip()
                    if val_strip == "":
                        continue
                    values_final.append(val_strip)

                rest = values_final

                final_info[entry_key]['perc'].append(perc)
                final_info[entry_key]['year'].append(year)
                final_info[entry_key]['rest'].append(rest)

        endobject = {}
        for key_parsed in final_info:
            value_of_key = final_info[key_parsed]
            length_of_key = len(value_of_key['perc'])
            final_object = []
            current_sub_object = {}

            last_is_append = False
            there_is_new_values = False
            for index in range(0, length_of_key):
                perc = value_of_key['perc'][index]
                year = value_of_key['year'][index]
                rest = value_of_key['rest'][index]
                last_is_append = False

                for key_inner in value_of_key:
                    last_is_append = False
                    value_inner = value_of_key[key_inner][index]
                    if key_inner not in current_sub_object.keys():
                        if value_inner is not None and value_inner != '':
                            current_sub_object[key_inner] = value_inner
                            there_is_new_values = True

                    else:
                        last_is_append = True
                        there_is_new_values = False
                        final_object.append(current_sub_object)
                        current_sub_object = {}
                if not last_is_append and there_is_new_values:
                    final_object.append(current_sub_object)
            endobject[key_parsed] = final_object
        """
        match_tags = regex.findall("(?P<tag>[^\s]:)(?P<pattern>.*)", current_text)
        if match_tags:
            for entry in match_tags:
                tag = entry.group('tag')
                pattern = entry.group('pattern')
                print("asd")


        match_percentag = regex.search("(?P<lead>(NGS\s?:\s?|:\s?))(?P<perc>[\d\,\.\-\/]*\s?%?)", current_text)
        match_percentag2 = regex.search("(NGS)[\d\,\.\-\/]*\s?%?", current_text)

        match_year = regex.search("am.*\d\d\d\d", current_text)
        if match_percentag:
            perc = match_percentag.group('perc')
            lead = match_percentag.group('lead')
            print("asd")
        percentage = match_percentag.group() if match_percentag else ""
        year = match_year.group() if match_year else ""
        current_text = current_text.replace(percentage, "").replace(year, "").strip()

        return_object = {}
        return_object['percentage'] = percentage.strip(',. ')
        return_object['year'] = year.strip(',. ')
        return_object['city_and_rest'] = current_text.strip(',. ')
        """
        # complex parsing here
        return input_text, endobject

