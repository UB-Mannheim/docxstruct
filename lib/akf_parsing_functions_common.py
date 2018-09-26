import regex
from .data_helper import DataHelper as dh

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

                    if key_count >= 1:
                        current_key = current_key + "_" + str(key_count + 1)
                    # remove current key from text
                    text = text.replace(current_key, "").strip()
                    abc_found = True

            if ":" in text and abc_found is False:
                # find out if there is a new category
                current_key = text.split(":")[0]
                # if there is a multikey give it an additional counter
                key_count = list(final_items.keys()).count(current_key)

                if key_count >= 1:
                    current_key = current_key+"_"+str(key_count+1)

                # remove current key from text
                text = text.replace(current_key, "").replace(":", "")



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
    def join_separated_lines(content_texts):
        """
        Joins dash separated lines in the text list (reduces the number of entries, if
        there are such lines)
        :param content_texts: text list to join
        :return: text array where all dash separated lines are joined
        """

        # final array with joined texts
        joined_texts = []
        # intermediate array for storing tagged lines (normal line:0 or separator_line:1)
        NORMAL_LINE = 0
        SEPARATOR_LINE = 1
        LAST_LINE = 2

        tagged_texts = []

        len_content_texts = len(content_texts)

        # iterate the given texts
        for text_index, text in enumerate(content_texts):
            if text is None:
                continue
            # if there is one, get the follow up text
            next_text = None
            if text_index < len_content_texts - 1:
                next_text = content_texts[text_index + 1].strip()

            # detect line with separator
            if len(text) >= 2 and "-" in text[-1]:
                if next_text is not None and len(next_text) >= 1:
                    # if the next starting letter is uppercase don't do the joining (assuming it's a '-'
                    # separated Name like "Jan-Phillipp")
                    if not next_text[0].isupper():
                        # fetch the next text in current and remove separator
                        text = text[0:len(text) - 1]
                    # store in tagged texts
                    tagged_texts.append((text, SEPARATOR_LINE))
                    continue

            if text_index >= len_content_texts:
                tagged_texts.append((text, LAST_LINE))
                break

            # append to tagged texts
            tagged_texts.append((text, NORMAL_LINE))

        # join the tagged texts

        for current_index, ttext_info in enumerate(tagged_texts):
            if ttext_info == None:
                continue # line was already joined

            current_ttext, current_id = ttext_info
            if current_id == NORMAL_LINE:
                joined_texts.append(current_ttext)
            elif current_id == SEPARATOR_LINE:
                # check all follow up lines
                for follow_up_index in range(current_index+1, len(tagged_texts)):
                    follow_ttext, follow_id = tagged_texts[follow_up_index]
                    current_ttext = current_ttext + follow_ttext
                    tagged_texts[follow_up_index] = None
                    if follow_id == NORMAL_LINE or follow_id == LAST_LINE:
                        #update my new array
                        joined_texts.append(current_ttext)
                        break # done escape the inner loop
                    elif follow_id == SEPARATOR_LINE:
                        continue # continue  inner loop

        # return the modified list
        return joined_texts

    @staticmethod
    def parse_id_location(origpost_red):
        """
        Parses a text for common text block like
        (24a) Hamburg 13, Mittelweg 180
        :param origpost_red:
        :return: tuple with numID, city, street, street_number, additional_info
        """

        # do first match
        match = regex.match(r"(?<NumID>\(.*?\))"                 # find starting number (non greedy to stop at first closing parenthesis)
                            r"(?<Location>.*?[,\.]|.*?)"         # find location string
                            r"(?<Rest>.*+)",                     # just get the rest which is usually streetname and number, but has other possibilities
                            origpost_red)
        if match is None:
            return None, None, None, None, None

        numID = dh.strip_if_not_none(match.group("NumID"), "")
        city = dh.strip_if_not_none(match.group("Location"), "")
        rest = dh.strip_if_not_none(match.group("Rest").strip(), "")

        # parse the rest if there is some
        if rest != "" and rest is not None:
            match_rest = regex.match(r"(?<Street>.*?)" # match all characters non-greedy 
                                     r"(?<Number>[0-9]+[-\/]*[0-9]*)"
                                     r"(?<Rest>.*+)",
                                     rest)
            if match_rest is not None:
                street = dh.strip_if_not_none(match_rest.group("Street"), "")
                street_number = dh.strip_if_not_none(match_rest.group("Number"), ",\.")
                additional_info = dh.strip_if_not_none(match_rest.group("Rest"), "")
                return numID, city, street, street_number, additional_info

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
    def add_check_element(topclass, content_texts, real_start_tag, segmentation_class, element_counter):

        if topclass.config.ADD_INFO_ENTRY_TO_OUTPUT:
            origpost, origpost_red = dh.create_stringified_linearray(
                content_texts)  # complete text, complete text without \n
            topclass.ef.add_to_my_obj("origpost", origpost_red, object_number=element_counter)
            topclass.ef.add_to_my_obj("type", segmentation_class.segment_tag, object_number=element_counter)
            element_counter += 1

        joined_texts = AKFCommonParsingFunctions.join_separated_lines(content_texts)  # join dash separated texts
        origpost, origpost_red = dh.create_stringified_linearray(joined_texts)   # final reduced array for further processing

        return origpost, origpost_red, element_counter, joined_texts
