from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler
from akf_corelib.random import Random

import numpy as np


class LineFeatures():
    counter_special_chars = -1
    counter_alphanumerical_chars = -1
    counter_numbers = -1
    counter_chars = -1
    counter_alphabetical = -1
    counter_words = -1
    counter_spaces = -1
    counters_alphabetical_ratios = []
    counters_wordlengths = []
    counters_numbers = []
    special_chars_ratio = -1
    alphanumerical_chars_ratio = -1
    alphabetical_ratio = -1
    spaces_ratio = -1
    numbers_ratio = -1

    x_box_sizes = []
    x_gaps = []

    maximum_x_gap = None
    mean_x_gap = None
    median_x_gap = None

    many_numbers_in_first_word = False
    many_alphabetical_in_middle_words = False
    many_alphabetical_in_last_word = False

    def __init__(self, cpr):
        self.cpr = cpr

    def print_me(self):
        self.cpr.print("alle cntr:", self.counter_chars)
        self.cpr.print("spec cntr:", self.counter_special_chars, "ratio", self.special_chars_ratio)
        self.cpr.print("alnr cntr:", self.counter_alphanumerical_chars, "ratio", self.alphanumerical_chars_ratio)
        self.cpr.print("albt cntr:", self.counter_alphabetical, "ratio", self.alphabetical_ratio)
        self.cpr.print("spce cntr:", self.counter_spaces, "ratio", self.spaces_ratio)
        self.cpr.print("nmbr cntr:", self.counter_numbers, "ratio", self.numbers_ratio)
        self.cpr.print("x_box_sizes", self.x_box_sizes)
        self.cpr.print("x_gaps", self.x_gaps)
        self.cpr.print("x_gap_max_size", self.maximum_x_gap)
        self.cpr.print("x_gaps_mean", self.mean_x_gap)
        self.cpr.print("x_gaps_median", self.median_x_gap)

class FeatureExtractor():

    def __init__(self):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_FEATURE_EXTRACTOR, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL)

        self.filter_start_words = ["Fernruf:", "Vorstand:", "Fernschreiber:",
                                   "von","Gründung:", "Ordnungsnr.", "Ordnungsnr",
                                   "Grundkapital:","Umstellung"]


    def extract_file_features(self, ocromore_data):
        all_line_features = []
        for line in ocromore_data['lines']:
            current_line_features = self.extract_line_features(line)
            all_line_features.append(current_line_features)

        ocromore_data['line_features'] = all_line_features

        return ocromore_data


    def extract_line_features(self, line):

        final_line_features = {}

        whole_text = line['text']

        self.cpr.print("recognizing text:", whole_text)

        # counters
        counter_special_chars = 0
        counter_alphanumerical_chars = 0
        counter_numbers = 0
        counter_chars = len(whole_text)
        counter_alphabetical = 0
        counter_words = 0
        counters_alphabetical_ratios = []
        counters_wordlengths = []
        counters_numbers = []

        character_index = 0
        # special conditions
        ultimo_is_first_word = False
        first_word_no_table_indicator = False
        starts_with_parenthesis = False
        ends_with_parenthesis = False

        last_xstop = 0
        x_box_sizes = []
        x_gaps = []
        for word_obj in line['words']:
            word_index = word_obj['word_index']
            word_text = word_obj['text']
            hocr_coordinates = word_obj['hocr_coordinates']

            word_xstart = hocr_coordinates[0]
            word_xstop = hocr_coordinates[2]
            word_box_size = word_xstop - word_xstart
            x_box_sizes.append(word_box_size)

            if word_index >= 1:
                x_gap = word_xstop - last_xstop
                x_gaps.append(x_gap)

            #line.data['word_x0']
            if word_text is None or word_text == "":
                continue

            if word_index == 0:
                if word_text in self.filter_start_words:
                    first_word_no_table_indicator = True
                if word_text.lower() == "ultimo":
                    ultimo_is_first_word = True
                if word_text[0] == "(":
                    starts_with_parenthesis = True


            if word_index == len(whole_text)-1:
                if word_text[-1] == ")":
                    ends_with_parenthesis = True



            counter_alphabetical_chars_word = 0
            counter_alphanumerical_chars_word = 0
            counter_numbers_word = 0


            counter_words += 1

            word_list = list(word_text)
            for char in word_list:
                if Random.is_special_character(char):
                    counter_special_chars += 1
                elif Random.is_alphanumerical_character(char):
                    counter_alphanumerical_chars += 1
                    counter_alphanumerical_chars_word += 1
                if char.isdigit():
                    counter_numbers += 1
                    counter_numbers_word += 1

            counter_alphabetical_word = counter_alphanumerical_chars_word - counter_numbers_word
            ratio_alphabetical_word = np.round(counter_alphabetical_word/len(word_text), 2)
            counters_alphabetical_ratios.append(ratio_alphabetical_word)
            counters_wordlengths.append(len(word_text))
            counters_numbers.append(counter_numbers_word)
            character_index += len(word_text)
            last_xstop = word_xstop


        # get number of spaces
        len_whole_unspace = len(whole_text.replace(" ", ""))
        counter_spaces = counter_chars - len_whole_unspace
        # set alphabetical counter
        counter_alphabetical = counter_alphanumerical_chars - counter_numbers


        if counter_chars == 0:
            self.cpr.printw("no chars shouldn't happen, no recognition")
            return False

        special_chars_ratio = counter_special_chars/ counter_chars
        alphanumerical_chars_ratio = counter_alphanumerical_chars / counter_chars
        alphabetical_ratio = counter_alphabetical / counter_chars
        spaces_ratio = counter_spaces/ counter_chars
        numbers_ratio = counter_numbers / counter_chars


        maximum_x_gap = None
        mean_x_gap = None
        median_x_gap = None

        if len(x_gaps) >= 1:
            maximum_x_gap = max(x_gaps)
            mean_x_gap = np.mean(x_gaps)
            median_x_gap = np.median(x_gaps)

        many_numbers_in_first_word = False
        many_alphabetical_in_middle_words = False
        many_alphabetical_in_last_word = False

        # check some middle and last word conditions
        for counter_index, counter in enumerate(counters_wordlengths):
            if counter_index == 0:
                ctr_numbers = counters_numbers[counter_index]
                numbers_ratio_word = np.round(ctr_numbers/counter,2)
                if numbers_ratio_word > 0.8:
                    many_numbers_in_first_word = True
            elif counter_index == len(counters_wordlengths)-1:
                if counter >= 4:
                    alphabetical_ratio_word = counters_alphabetical_ratios[counter_index]
                    if alphabetical_ratio_word >= 0.75:
                        many_alphabetical_in_last_word = True

            else:
                if counter >= 4:
                    alphabetical_ratio_word = counters_alphabetical_ratios[counter_index]
                    if alphabetical_ratio_word >= 0.75:
                        many_alphabetical_in_middle_words = True





        final_line_features = LineFeatures(cpr=self.cpr)
        final_line_features.many_alphabetical_in_last_word = many_alphabetical_in_last_word

        final_line_features.counter_special_chars = counter_special_chars
        final_line_features.counter_chars = counter_chars
        final_line_features.counter_spaces = counter_spaces
        final_line_features.counter_numbers = counter_numbers
        final_line_features.counter_alphabetical = counter_alphabetical
        final_line_features.counter_alphanumerical_chars = counter_alphanumerical_chars
        final_line_features.counter_words = counter_words

        final_line_features.counters_numbers = counters_numbers
        final_line_features.counters_wordlengths = counters_wordlengths
        final_line_features.counters_alphabetical_ratios = counters_alphabetical_ratios

        final_line_features.numbers_ratio = numbers_ratio
        final_line_features.alphabetical_ratio = alphabetical_ratio
        final_line_features.alphanumerical_chars_ratio = alphanumerical_chars_ratio
        final_line_features.special_chars_ratio = special_chars_ratio
        final_line_features.spaces_ratio = spaces_ratio

        final_line_features.many_alphabetical_in_last_word = many_alphabetical_in_last_word
        final_line_features.many_alphabetical_in_middle_words = many_alphabetical_in_middle_words
        final_line_features.many_numbers_in_first_word = many_numbers_in_first_word
        final_line_features.x_box_sizes = x_box_sizes
        final_line_features.x_gaps = x_gaps

        final_line_features.maximum_x_gap = maximum_x_gap
        final_line_features.mean_x_gap = mean_x_gap
        final_line_features.median_x_gap = median_x_gap



        return final_line_features