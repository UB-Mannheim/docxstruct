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
            # self.set_only()  # comment out to segment this segments and other segments with that tag exclusively


        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Sitz\s?:", line_text)
            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            if self.start_was_segmented is True:
                self.do_match_work(False, None, self.start_line_index, 0)
                return True

    class SegmentVerwaltung(Segment):
        # example recognition:
        # Verwaltung: 8045 Ismaning bei Mün- \n chen ...

        def __init__(self):
            super().__init__("Verwaltung")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Verwaltung\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentBeratendeMitglieder(Segment):
        # example recognition:
        # Beratende Mitglieder: \n H.S.A.Hartog, Hamburg;

        def __init__(self):
            super().__init__("BeratendeMitglieder")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Beratende Mitglieder\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentSekretaere(Segment):
        # example recognition:
        # Sekretäre: \n C. Zwagerman, London; ...

        def __init__(self):
            super().__init__("Sekretäre")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Sekretäre\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentFernruf(Segment):
        # example recognition:
        # Fernruf: Peine 26 41, 26 09 und \n 2741, \n Grossilsede 5 41.

        def __init__(self):
            super().__init__("Fernruf")


        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Fernruf\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_stop, errors = regu.fuzzy_search(r"^Fernschreiber\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)

                return True

    class SegmentFernschreiber(Segment):
        # example recognition:
        # Fernruf: Peine 26 41, 26 09 und \n 2741, \n Grossilsede 5 41.

        def __init__(self):
            super().__init__("Fernschreiber")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Fernschreiber\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_stop, errors = regu.fuzzy_search(r"^Vorstand\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True


    class SegmentVorstand(Segment):
        # example recognition:
        # Vorstand: \n Diedrich Dännemark, Peine; \n Helmuth Heintzmann, Herne; \n ...


        def __init__(self):
            super().__init__("Vorstand")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Vorstand\s?:", line_text)


            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_stop, errors = regu.fuzzy_search(r"^Aufsichtsrat\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True

    class SegmentAufsichtsrat(Segment):
        # example recognition:
        # Aufsichtsrat: Julius Fromme, Peine, Vors.; \n Hermann Beermann, Hannover, 1.stellv. \n


        def __init__(self):
            super().__init__("Aufsichtsrat")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Aufsichtsrat\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_stop, errors = regu.fuzzy_search(r"^Gründung\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True

    class SegmentArbeitnehmervertreter(Segment):
        # example recognition:
        # Arbeitnehmervertreter: \n Martin Birkel, Ehrang;


        def __init__(self):
            super().__init__("Arbeitnehmervertreter")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Arbeitnehmervertreter\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentGruendung(Segment):
        # example recognition:
        # Gründung: 1858.


        def __init__(self):
            super().__init__("Gründung")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Gründung\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            if self.start_was_segmented and not self.stop_was_segmented:
                self.do_match_work(False, None, self.start_line_index, 0)
                return True

    class SegmentTaetigkeitsgebiet(Segment):
        # example recognition:
        # Tätigkeitsgebiet: \n Erzeugung von: Erze, Kohle, Strom,

        def __init__(self):
            super().__init__("Tätigkeitsgebiet")


        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Tätigkeitsgebiet\s?:", line_text)


            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Haupterzeugnisse\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True



    class SegmentWerke(Segment):
        # example recognition:
        # Werke: \n Werksgruppe Geisweid

        def __init__(self):
            super().__init__("Werke")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Werke\s?:", line_text, err_number=1)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop = None # regu.fuzzy_search(r"^Haupterzeugnisse\s?:", line_text)

            if match_stop is not None:
                self.stop_line_index = line_index -1
                self.stop_was_segmented = True
                return True


    class SegmentInlaendischeBeteiligungsGesellsch(Segment):
        # example recognition:
        # Wichtigste inländische Beteili- \n gungsgesellschaften

        def __init__(self):
            super().__init__("Inl.Beteiligungsgesellschaften")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            prev_text = ""
            if prev_line is not None:
                prev_text = prev_line['text']
            combi_text = prev_text + line_text

            match_start, errors = regu.fuzzy_search(r"inländische Beteiligung.+gesellschaft.+:", combi_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index-1, errors)

                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop = None # regu.fuzzy_search(r"^Haupterzeugnisse\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, 0)
                return True

    class SegmentNamhafteBeteiligungen(Segment):
        # example recognition:
        # Namhafte Beteiligungen: \n Stahlwerke Brüninghaus GmbH ...

        def __init__(self):
            super().__init__("NamhafteBeteiligungen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Namhafte Beteiligungen\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop = None # regu.fuzzy_search(r"^Haupterzeugnisse\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, 0)
                return True

    class SegmentBeteiligungen(Segment):
        # example recognition:
        # Beteiligungen: \n Hamburger Verkehrsmittel-Werbung ...

        def __init__(self):
            super().__init__("Beteiligungen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            # reduced error number to prevent confusion with "Beteiligung:"
            match_sitz, errors = regu.fuzzy_search(r"^Beteiligungen\s?:", line_text, err_number=1)
            if match_sitz is not None:
                self.do_match_work(True, match_sitz, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            if self.start_was_segmented is True:
                self.do_match_work(False, None, line_index -1, 0)
                return True

    class SegmentHaupterzeugnisse(Segment):
        # example recognition:
        # Haupterzeugnisse: \n Form- und Stabstahl.

        def __init__(self):
            super().__init__("Haupterzeugnisse")


        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Haupterzeugnisse\s?:", line_text)


            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Spezialitäten\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True

    class SegmentSpezialitaeten(Segment):
        # example recognition:
        # Spezialitäten: \n Breitflanschträger ("'Peiner Träger"),

        def __init__(self):
            super().__init__("Spezialitäten")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Spezialitäten\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"bung der Tochtergesellschaften\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-2, errors)
                return True

    class SegmentTochtergesellschaften(Segment):
        # example recognition:
        # Besitz- und Betriebsbeschreibung der Tochtergesellschaften: \n
        # todo this is very long content, check this and maybe do subclassification segments here, maybe subsegments

        def __init__(self):
            super().__init__("Tochtergesellschaften")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"bung der Tochtergesellschaften\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Geschäftsjahr\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True

    class SegmentGeschaeftsjahr(Segment):
        # example recognition:
        # Geschäftsjahr:  Kalenderjahr....

        def __init__(self):
            super().__init__("Geschäftsjahr")


        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Geschäftsjahr\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Stimmrecht d.+ Aktien.+\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True


    class SegmentStimmrechtAktien(Segment):
        # example recognition:
        # Stimmrecht d. Aktien i.d.H. -V: \n Je nom. DM 100. - = 1 Stimme.

        def __init__(self):
            super().__init__("StimmrechtAktien")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Stimmrecht d.+ Aktien.+\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Zahlstellen\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True

    class SegmentZahlstellen(Segment):
        # example recognition:
        # Zahlstellen: \n Gesellschaftskasse; ...

        def __init__(self):
            super().__init__("Zahlstellen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Zahlstellen\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Grundkapital\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True


    class SegmentGrundkapital(Segment):
        # example recognition:
        # Grundkapital: \n DM 1222....

        def __init__(self):
            super().__init__("Grundkapital")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Grundkapital\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Börsennotiz\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True


    class SegmentBoersennotiz(Segment):
        # example recognition:
        # Börsennotiz: \n Hannover und im Freiverkehr Berlin \n und Hamburg.

        def __init__(self):
            super().__init__("Börsennotiz")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Börsennotiz\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Ordnungsn.+Aktien\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True


    class SegmentWKN(Segment):
        # example recognition:
        # Wertpapier-Kenn-Nr.: \n 692100

        def __init__(self):
            super().__init__("Wertpapier-Kenn-Nr")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Wertpapier-Kenn-Nr\.\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True



    class SegmentOrdnungsnrDaktien(Segment):
        # example recognition:
        # Ordnungsnr.d.Aktien: 620200.

        def __init__(self):
            super().__init__("OrdnungsNrAktien")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Ordnungsn.+Aktien\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Stückelung\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True

    class SegmentStueckelung(Segment):
        # example recognition:
        # Stückelung: \n 99 856 St.-Akt. zu je DM 1 000.-

        def __init__(self):
            super().__init__("Stückelung")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Stückelung\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Grossaktionär\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True

    class SegmentAktionaere(Segment):
        # example recognition:
        # Aktionäre: \n Bankhaus August Lenz & Co., München

        def __init__(self):
            super().__init__("Aktionäre")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Aktionäre\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True



    class SegmentGrossaktionaer(Segment):
        # example recognition:
        # Grossaktionär: \n Vereinigte Industrie-Unternehmungen

        def __init__(self):
            super().__init__("Großaktionär")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"Gro(?:ss|ß)aktionär(?:\s?|e\s?):", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Anleihe\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True

    class SegmentAnleihen(Segment):
        # example recognition:
        # Anleihe: \n 6 % Amerika-Anleihe von 1928/48
        # todo this has subentry 'Emissionsbeitrag:'
        # Anleihen: \n ... (todo is anleihen anleihe same?)

        def __init__(self):
            super().__init__("Anleihen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"Anleihe(?:n?)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Aktienkurse\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True

    class SegmentAktienkurse(Segment):
        # example recognition:
        # Aktienkurse: \n ultimo 1948 19,5 % \n <table> ...


        def __init__(self):
            super().__init__("Aktienkurse")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"Aktienkurse\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Dividenden(?:.+)Stammaktien\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True

    class SegmentDividenden(Segment):
        # example recognition:
        # Dividenden: \n 1949/50: 0% (this is for the table dividenden!)
        # todo think about combining with dividenden auf stammaktien

        def __init__(self):
            super().__init__("Dividenden")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Dividenden\s?:$", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Zur Geschäftslage?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True


    class SegmentDividendenAStammaktien(Segment):
        # example recognition:
        # Dividenden auf Stammaktien: \n 1948/49: 0% \n 1950: 0% ...
        # todo think about combining with dividenden


        def __init__(self):
            super().__init__("DividendenAufStammaktien")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"^Dividenden(?:.+)Stammaktien\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Zur Geschäftslage?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True

    class SegmentBezugsrechte(Segment):
        # example recognition:
        # Bezugsrechte: \n 1955: i.V. 4:1 zu 130 %; Abschlag 20 %


        def __init__(self):
            super().__init__("Bezugsrechte")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            match_start, errors = regu.fuzzy_search(r"^Bezugsrechte\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentZurGeschaeftslage(Segment):
        # example recognition:
        # Zur Geschäftslage: \n Guter Absatz aller im Bereich der Ilseder


        def __init__(self):
            super().__init__("ZurGeschäftslage")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"^Zur Geschäftslage\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Aus den Bilanzen\s?:?", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True



    class SegmentAusDenBilanzen(Segment):
        # example recognition:
        # Aus den Bilanzen \n 31.12.1954 31.12.1955 \n (in 1 000 DM)


        def __init__(self):
            super().__init__("AusDenBilanzen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"^Aus d(?:en)? Bilanzen\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            match_stop, errors = regu.fuzzy_search(r"^Aus d(?:en)? Gewinn- und Verlust- \s?:?", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index-1, errors)
                return True


    class SegmentAusGewinnVerlustrechnungen(Segment):
        # example recognition:
        # Aus den Gewinn- und Verlust- \n rechnungen \n Löhne und Gehälter 568 620

        def __init__(self):
            super().__init__("AusGewinnVerlustrechnungen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"^Aus d(?:en)? Gewinn- und Verlust- ", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line):

            #match_stop = regu.fuzzy_search(r"^Aus d(?:en)? Gewinn- und Verlust- \s?:?", line_text)
            match_stop = line_index == num_lines-2

            if match_stop is True:
                self.do_match_work(False, match_stop, line_index-1, 0)

                return True