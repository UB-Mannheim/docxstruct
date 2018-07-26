from lib.segment import Segment
from akf_corelib.regex_util import RegexUtil as regu
##
# notes to regex
# re.match("c", "abcdef")    # No match
# re.search("c", "abcdef")   # Match


class SegmentHolder(object):
    """
    This is a simple holder class for the adapted segments which
    contain start and stop recognition conditions, wrapper should
    be kept as simple as possible, this contains classes for
    aktienführer project. Other segmentation could be set here with
    a new class segment_holder_somethingelse and it's
    usage in segment_classifier.
    """

    class SegmentSitz(Segment):
        # example recognition line:
        # Sitz: (20a) Peine, Gerhardstr. 10.

        def __init__(self):
            super().__init__("Sitz")
            # self.disable()  # comment out to disable a segment
            # self.set_only() # comment out to segment this segments and other segments with that tag exclusively

        def match_start_condition(self, line, line_text, line_index, features):
            match_sitz = regu.fuzzy_search(r"^Sitz\s?:", line_text)
            if match_sitz is not None:
                self.set_keytag_indices(match_sitz)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):
            if self.start_was_segmented is True:
                self.stop_line_index = self.start_line_index
                self.stop_was_segmented = True
                return True

    class SegmentFernruf(Segment):
        # example recognition:
        # Fernruf: Peine 26 41, 26 09 und \n 2741, \n Grossilsede 5 41.

        def __init__(self):
            super().__init__("Fernruf")

        def match_start_condition(self, line, line_text, line_index, features):
            match_start = regu.fuzzy_search(r"^Fernruf\s?:", line_text)

            if match_start is not None:
                self.set_keytag_indices(match_start)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):
            match_stop = regu.fuzzy_search(r"^Fernschreiber\s?:", line_text)

            if match_stop is not None:
                self.stop_line_index = line_index -1
                self.stop_was_segmented = True
                return True

    class SegmentFernschreiber(Segment):
        # example recognition:
        # Fernruf: Peine 26 41, 26 09 und \n 2741, \n Grossilsede 5 41.

        def __init__(self):
            super().__init__("Fernschreiber")

        def match_start_condition(self, line, line_text, line_index, features):
            match_start = regu.fuzzy_search(r"^Fernschreiber\s?:", line_text)

            if match_start is not None:
                self.set_keytag_indices(match_start)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):
            match_stop = regu.fuzzy_search(r"^Vorstand\s?:", line_text)

            if match_stop is not None:
                self.stop_line_index = line_index -1
                self.stop_was_segmented = True
                return True


    class SegmentVorstand(Segment):
        # example recognition:
        # Vorstand: \n Diedrich Dännemark, Peine; \n Helmuth Heintzmann, Herne; \n ...


        def __init__(self):
            super().__init__("Vorstand")

        def match_start_condition(self, line, line_text, line_index, features):
            match_start = regu.fuzzy_search(r"^Vorstand\s?:", line_text)


            if match_start is not None:
                self.set_keytag_indices(match_start)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):
            match_stop = regu.fuzzy_search(r"^Aufsichtsrat\s?:", line_text)

            if match_stop is not None:
                self.stop_line_index = line_index -1
                self.stop_was_segmented = True
                return True

    class SegmentAufsichtsrat(Segment):
        # example recognition:
        # Aufsichtsrat: Julius Fromme, Peine, Vors.; \n Hermann Beermann, Hannover, 1.stellv. \n


        def __init__(self):
            super().__init__("Aufsichtsrat")


        def match_start_condition(self, line, line_text, line_index, features):
            match_start = regu.fuzzy_search(r"^Aufsichtsrat\s?:", line_text)


            if match_start is not None:
                self.set_keytag_indices(match_start)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):
            match_stop = regu.fuzzy_search(r"^Gründung\s?:", line_text)

            if match_stop is not None:
                self.stop_line_index = line_index -1
                self.stop_was_segmented = True
                return True

    class SegmentGruendung(Segment):
        # example recognition:
        # Gründung: 1858.


        def __init__(self):
            super().__init__("Gründung")

        def match_start_condition(self, line, line_text, line_index, features):
            match_start = regu.fuzzy_search(r"^Gründung\s?:", line_text)


            if match_start is not None:
                self.set_keytag_indices(match_start)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):

            if self.start_was_segmented and not self.stop_was_segmented:
                self.stop_line_index = self.start_line_index
                self.stop_was_segmented = True
                return True

    class SegmentTaetigkeitsgebiet(Segment):
        # example recognition:
        # Tätigkeitsgebiet: \n Erzeugung von: Erze, Kohle, Strom,

        def __init__(self):
            super().__init__("Tätigkeitsgebiet")

        def match_start_condition(self, line, line_text, line_index, features):
            match_start = regu.fuzzy_search(r"^Tätigkeitsgebiet\s?:", line_text)

            if match_start is not None:
                self.set_keytag_indices(match_start)
                self.start_line_index = line_index
                self.start_was_segmented = True
                return True

        def match_stop_condition(self, line, line_text, line_index, features):

            match_stop = regu.fuzzy_search(r"^Haupterzeugnisse\s?:", line_text)

            if match_stop is not None:
                self.stop_line_index = line_index -1
                self.stop_was_segmented = True
                return True

