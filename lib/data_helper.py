from akf_corelib.filehandler import FileHandler as fh
import io

class DataHelper(object):
    """
    Class with helper functions for handling the data block
    """

    @staticmethod
    def get_real_tag_from_segment(segment, start_line, remove_trailing_colon=True):
        """
        Extracts the recognized tag string from the line object from the corresponding segment
        :param segment: segment class instance
        :param line: line-object from data
        :param remove_trailing_colon: indicator if results trailing colons ':' are removed
        :return: string of tag
        """
        start = segment.key_tag_cindex_start
        stop = segment.key_tag_cindex_stop

        text = start_line['text'][start:stop]
        len_text = len(text)

        # remove trailing ':'
        if remove_trailing_colon:

            if len_text >= 1 and text[len_text-1] == ":":
                text = text[0:len_text-1]

        return text


    @staticmethod
    def get_rest_content_start_line(segmentation_class, start_line, trim=True):
        text = start_line['text']
        stop = segmentation_class.key_tag_cindex_stop
        rest_start = text[stop:]
        if trim:
            rest_start = rest_start.strip()
        return rest_start

    @staticmethod
    def get_content(segment_lines, feature_lines, segmentation_class):
        start_index = segmentation_class.get_start_line_index()
        stop_index = segmentation_class.get_stop_line_index()
        selected_start_line = segment_lines[start_index]
        feature_start_line = feature_lines[start_index]
        real_tag = DataHelper.get_real_tag_from_segment(segmentation_class, selected_start_line)
        rest_content_start_line = DataHelper.get_rest_content_start_line(segmentation_class, selected_start_line)

        # if there are no further line, return obtained content
        if start_index == stop_index:
            return real_tag, [rest_content_start_line], [selected_start_line], [feature_start_line]

        # otherwise fetch the rest of the content
        other_rest_content_texts = []
        other_rest_content_lines = []
        other_rest_feature_lines = []

        other_rest_content_texts.append(rest_content_start_line)
        other_rest_content_lines.append(selected_start_line)
        other_rest_feature_lines.append(feature_start_line)

        for current_index in range(start_index+1, stop_index+1):
            current_line = segment_lines[current_index]
            current_feature_lines = feature_lines[current_index]
            other_rest_content_texts.append(current_line['text'])
            other_rest_content_lines.append(current_line)
            other_rest_feature_lines.append(current_feature_lines)

        return real_tag, other_rest_content_texts, other_rest_content_lines, other_rest_feature_lines


    @staticmethod
    def write_array_to_root_simple(base_path, tag, text_lines, analysis_root, append_mode=False):
        full_dir = analysis_root + base_path + "/"
        full_path = full_dir + tag + ".txt"

        fh.create_directory_tree(full_dir)
        # write append or normal
        if append_mode is True:
            my_file = io.open(full_path, 'a', encoding='utf8')
        else:
            my_file = io.open(full_path, 'w', encoding='utf8')

        for text_line in text_lines:
            my_file.write(text_line+"\n")

        my_file.close()

    @staticmethod
    def write_array_to_root(base_path, text_lines, ocromore_data, analysis_root, accumulated=False):
        """
        Writes a line-array to the base path in root path with ocromore data file and db name
        :param base_path:
        :param text_lines:
        :param ocromore_data:
        :param analysis_root: root path in base directory
        :param accumulated: file is accumulated file naming different
        :return:
        """

        dbpath = ocromore_data['file_info'].dbpath
        tablename = ocromore_data['file_info'].tablename

        full_dir = analysis_root + base_path + dbpath+"/"
        if accumulated is False:
            full_path = full_dir + tablename + ".txt"
        else:
            full_path = full_dir +"accumulated_report"+".txt"

        fh.create_directory_tree(full_dir)

        my_file = io.open(full_path, 'w', encoding='utf8')

        for text_line in text_lines:
            my_file.write(text_line+"\n")

        my_file.close()

    @staticmethod
    def create_stringified_linearray(array_of_texts):
        final_string = ""
        for line_text in array_of_texts:
            final_string += line_text+"\n"

        final_string = final_string.strip()
        return final_string, final_string.replace("\n", " ")

    @staticmethod
    def strip_if_not_none(text,strip_pattern):
        if text is None:
            return text
        else:
            if strip_pattern != "":
                return text.strip(strip_pattern)
            else:
                return text.strip()


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