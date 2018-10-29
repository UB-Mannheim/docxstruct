import regex
from .data_helper import DataHelper as dh
from akf_corelib.regex_util import RegexUtil as regu


class AKFCommonParsingFunctions(object):
    """
    This is a holder object for commonly ocuring parsing
    steps in the akf-context used by akf-parsing-functions-(number)
    """

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

            abc_found = False
            if abc_sections:
                starts_with_abc = regex.search("^\w\s?\)", text)
                if starts_with_abc:
                    current_key = starts_with_abc[0]

                    # if there is a multikey give it an additional counter
                    key_count = list(final_items.keys()).count(current_key)

                    # remove current key from text
                    text = text.replace(current_key, "", 1).strip()
                    abc_found = True

                    if key_count >= 1:
                        current_key = current_key + "_" + str(key_count + 1)

            if ":" in text and abc_found is False:
                # find out if there is a new category
                current_key = text.split(":")[0]
                # if there is a multikey give it an additional counter
                key_count = list(final_items.keys()).count(current_key)

                # remove current key from text
                #text = text.replace(current_key, "").replace(":", "") # can lead to errors (double replacement in sth like  Lokomotive: Dampf-Lokomotive)
                text = regex.sub(regex.escape(current_key)+"\s?"+":", "", text)

                if key_count >= 1:
                    current_key = current_key+"_"+str(key_count+1)


            text = text.strip()

            # add key entry if it doesn't exist
            if current_key not in final_items.keys():
                final_items[current_key] = ""

            # join separated words if there are some
            if join_separated_lines:
                if len(text) >= 2 and "-" in text[-1]:
                    if next_text is not None and len(next_text) >=1:
                        # if the next starting letter is uppercase don't do the joining (assuming it's a '-'
                        # separated Name like "Jan-Philipp")
                        if not next_text[0].isupper():
                            text = text[0:len(text)-1]

                        # add the text without space separator cause next line will directly be directly joined
                        final_items[current_key] += text
                        continue

            add_space = " "
            # remove space added on last line
            if text_index >= len_content_texts-1:
                add_space = ""

            # add line to final items
            final_items[current_key] += text.strip()+add_space

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
            # todo cases
            # (17b) Rheinfelden (Baden);
            # (22c) Zementfabrik bei Ober- kassel (Siegkr.)
            # (14a) Bietigheim uWürtt (Württ.).

        # Sometimes the text contains an additional Sitz-preamble although segmented ok
        origpost_red = regex.sub("^Sitz", "", origpost_red.strip()).strip()
        # do first match
        match = regex.match(r"(?<NumID>\(.*?\))"                 # find starting number (non greedy to stop at first closing parenthesis)
                            r"(?<Location>.*?(,|\.\s)|.*?)"         # find location string
                            r"(?<Rest>.*+)",                     # just get the rest which is usually streetname and number, but has other possibilities
                            origpost_red)
        if match is None:
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
    def parse_persons(origpost_red):
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

            entry_split = entry_stripped.split(',')
            name = ""
            city = ""
            title = ""
            rest_info = ""
            for fragment_index, fragment in enumerate(entry_split):
                if fragment_index == 0:
                    name = fragment
                elif fragment_index == 1:
                    city = fragment
                elif fragment_index == 2:
                    title = fragment
                elif fragment_index >= 3:
                    rest_info += fragment

            final_entries.append((name, city, title, rest_info))
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

        # if not activated detailed parsing just return simple solution
        if not detailed_parsing:
            return text_reduced, None

        # continue with detailed parsing here
        match_currency = regex.search(r"^[a-zA-Z\.]+", text_reduced)
        match_numbers = regex.search(r"[\d\s\.\-]+", text_reduced)
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
        origpost, origpost_red = dh.create_stringified_linearray(joined_texts)   # final reduced array for further processing

        if topclass.config.ADD_INFO_ENTRY_TO_OUTPUT:
            # care!: origpost is added after joining seperated lines!
            topclass.ef.add_to_my_obj("origpost", origpost_red, object_number=element_counter)
            topclass.ef.add_to_my_obj("type", segmentation_class.segment_tag, object_number=element_counter)
            element_counter += 1

        return origpost, origpost_red, element_counter, joined_texts


    @staticmethod
    def match_common_block(content_texts, content_lines, complex_parsing, additional_categories):

        # check the additional categories field which additional categories can be found
        dict_used_categories = {}
        for entry in additional_categories:
            entry_low = entry.lower()
            dict_used_categories[entry_low] = True


        # create a writable results array
        results = []
        current_object = {}
        category_hit = False
        for text_index, text in enumerate(content_texts):
            text_stripped = text.strip()
            if text_stripped == "":
                continue
            if dict_used_categories['kapital'] is True:
                match_kapital, err_kapital = regu.fuzzy_search(r"^Kapital\s?:", text_stripped, err_number=1)
                if match_kapital:
                    my_result = match_kapital.group()
                    if 'kapital' in current_object.keys():
                        # refresh current object if already in keys
                        current_object = {}
                        # append old object
                        results.append(current_object)

                    simple, complex = AKFCommonParsingFunctions.parse_kapital_line(my_result, text_stripped,
                                                            detailed_parsing=complex_parsing)
                    current_object['kapital'] = complex if complex_parsing else simple  # conditionally set val
                    category_hit = True  # indicate that an additional subcategory was already found in current object

                    continue
            if dict_used_categories['dividenden'] is True:

                match_dividenden, err_divid = regu.fuzzy_search(r"^Dividenden\s?(:|ab)",
                                                                text_stripped, err_number=1)
                if match_dividenden:
                    my_result = match_dividenden.group()
                    if 'dividenden' in current_object.keys():
                        # refresh current object if already in keys
                        current_object = {}
                        # append old object
                        results.append(current_object)
                    simple, complex = AKFCommonParsingFunctions.parse_dividenden_line(my_result, text_stripped,
                                                                            detailed_parsing=complex_parsing)
                    current_object['dividenden'] =  complex if complex_parsing else simple  # conditionally set val
                    category_hit = True  # indicate that an additional subcategory was already found in current object

                    continue
            if dict_used_categories['parenthesis'] is True:

                match_parenth = regex.search(r"^\(\.*\)",text_stripped)

                if match_parenth:
                    my_result = match_parenth.group()
                    if 'parenthesis' in current_object.keys():

                        # refresh current object if already in keys
                        current_object = {}
                        # append old object
                        results.append(current_object)

                    current_object['add_info'] = my_result
                    category_hit = True  # indicate that an additional subcategory was already found in current object
                    continue

            word_info = content_lines[text_index]['words']

            # if shorter line (wordcount) (skip this if a text and a category was already found 'category hit')
            if not category_hit and len(word_info) <= 2:
                if 'text' not in current_object.keys():
                    current_object['text'] = text_stripped
                else:
                    current_object['text'] += " " + text_stripped
                    current_object['text'] = current_object['text'].strip()
                continue

            # if other cases don't match add text to new object
            current_object = {}
            current_object['text'] = text_stripped
            category_hit = False  # indicate that there has been no category assigned yet
            results.append(current_object)

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

        match_percentag = regex.search("[\d\,\.\-\/]*\s?%", input_text)
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
        return_object['percentage'] = percentage
        return_object['year'] = year
        return_object['amount'] = lead_num
        return_object['name'] = rest_3
        return_object['add_info'] = add_info_start

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

        if complex_parsing is False:
            # possible to add some simple parsing here
            return input_text, None

        current_text = input_text
        match_percentag = regex.search("(NGS\s?:\s?|:\s?)[\d\,\.\-\/]*\s?%?", current_text)
        match_year = regex.search("am.*\d\d\d\d", current_text)
        percentage = match_percentag.group() if match_percentag else ""
        year = match_year.group() if match_year else ""
        current_text = current_text.replace(percentage, "").replace(year, "").strip()

        return_object = {}
        return_object['percentage'] = percentage.strip(',. ')
        return_object['year'] = year.strip(',. ')
        return_object['city_and_rest'] = current_text.strip(',. ')

        # complex parsing here
        return input_text, return_object

