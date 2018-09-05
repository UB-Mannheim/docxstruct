class AKFCommonParsingFunctions(object):
    """
    This is a holder object for commonly ocuring parsing
    steps in the akf-context used by akf-parsing-functions-(number)
    """

    @staticmethod
    def parse_general_and_keys(content_texts, join_separated_lines=False, current_key_initial_value=None):
        """
        Separates an array of texts into categories.
        Categories are found by leading tag followed by ':'

        :param content_texts: texts to check
        :param join_separated_lines: lines which have trailing - get concatinated
        :param current_key_initial_value: used key initial value (for "General info" key)
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

            if ":" in text:
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
