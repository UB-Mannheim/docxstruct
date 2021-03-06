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



    class SegmentFirmenname(Segment):
        # example recognition line:
        # Voigt & Haeffner Aktiengesellschaft
        # Nord-Deutsche Versicherungs-Gesellschaft

        def __init__(self):
            super().__init__("Firmenname")
            # self.disable()  # comment out to disable a segment
            # self.set_only()  # comment out to segment this segments and other segments with that tag exclusively


        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            # this function get's hopped and called later
            # Attention: This is a special case which get's called like:
            # lines, lines, self.index_field, feats, len(lines), file_info,None
            file_info = prev_line
            dbname = file_info.dbname
            current_year = int(dbname)
            selected_start_index = None

            if current_year >= 1960:
                # get the first lines which can resemble the title
                for index, value in enumerate(line_index):
                    if value is not False:
                        break
                    selected_line = line_text[index]
                    selected_text = selected_line['text'].strip(",.; ")
                    if selected_text != "":
                        selected_start_index = index
                        break
            else:
                # just take last line in early years
                selected_start_index = len(line_index)-1

            if selected_start_index is not None:
                placeholder_match, errors = regu.fuzzy_search(r"", "")
                self.do_match_work(True, placeholder_match, selected_start_index, 0)
                return True

            return False

    class SegmentSitz(Segment):
        # example recognition line:
        # Sitz: (20a) Peine, Gerhardstr. 10.

        def __init__(self):
            super().__init__("Sitz")
            # self.disable()  # comment out to disable a segment
            # self.set_only()  # comment out to segment this segments and other segments with that tag exclusively


        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Hauptsitz\s?:|^Sitz\s?:", line_text)
            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentVerwaltung(Segment):
        # example recognition:
        # Verwaltung: 8045 Ismaning bei Mün- \n chen ...
        # Verwaltungsrat:
        # Verw.: (20b) Hannover ...

        def __init__(self):
            super().__init__("Verwaltung")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Verwaltung:?|Verw\.\s?):", line_text, err_number=0)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentBeratendeMitglieder(Segment):
        # example recognition:
        # Beratende Mitglieder: \n H.S.A.Hartog, Hamburg;

        def __init__(self):
            super().__init__("BeratendeMitglieder")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Beratende Mitglieder\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentGesellschafter(Segment):
        # example recognition:
        # Gesellschafter

        def __init__(self):
            super().__init__("Gesellschafter")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Persönlich\shaftender\s)?(Gesellschafter|schafter)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentSekretaere(Segment):
        # example recognition:
        # Sekretäre: \n C. Zwagerman, London; ...

        def __init__(self):
            super().__init__("Sekretäre")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Sekretär des Verwaltungsrates|Sekretäre)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentGeschaeftsleitung(Segment):
        # example recognition:
        # Geschäftsleitung: \n Harry Heltzer, Vors. des A. -R.; \n

        def __init__(self):
            super().__init__("Geschäftsleitung")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Geschäftsführung|Geschäftsleitung)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentGeneraldirektion(Segment):
        # example recognition:
        # Generaldirektion: \n Niccolä Gioia; Francesco Rota

        def __init__(self):
            super().__init__("Generaldirektion")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Generaldirektorium|"
                                                    r"Generaldirektion|"
                                                    r"Direktion|"
                                                    r"Direktorium|"
                                                    r"Generalbevollmächtigter|"
                                                    r"Berzirksdirektionen)\s?:", line_text)

            if match_start is not None:
                if "Generaldirektion in" in line_text:
                    return False
                found_match = match_start.group(0)
                subgroup = found_match[-2:]
                if ":" not in subgroup:
                    return False
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentDirektionskomitee(Segment):
        # example recognition:
        # Direktionskomitee: \n Es besteht aus der Generaldirektion und

        def __init__(self):
            super().__init__("Direktionskomitee")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Direktionskomitee)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentVizegeneraldirektoren(Segment):
        # example recognition:
        # Vizegeneraldirektoren: \n Riccardo Chivino; Umberto Cuttica; Sanzio \n

        def __init__(self):
            super().__init__("Vizegeneraldirektoren")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Vizegeneraldirektoren\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True



    class SegmentTelefon(Segment):
        # example recognition:
        # Fernruf: Pei  ne 26 41, 26 09 und \n 2741, \n Grossilsede 5 41.
        # Telefon: (02 21)Sa.-Nr. 772 11
        def __init__(self):
            super().__init__("Telefon/Fernruf")


        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(?:Fernruf|Telefon)\s?:", line_text)

            # if "Kupferberg" in combined_texts:
            #    print("asd")

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentGeschaeftsinhaber(Segment):
        # example recognition:
        # Geschäftsinhaber: Emil Kupferberg, Mainz; Dr. Christian Adalbert Kupferberg, Mainz.

        def __init__(self):
            super().__init__("Geschäftsinhaber/leitung")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Geschäfts(inhaber|leitung)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True



    class SegmentFernschreiber(Segment):
        # example recognition:
        # Fernschreiber : ...
        # Telex: 8 885 706 (telex is same)

        def __init__(self):
            super().__init__("Fernschreiber")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(?:Fernschreiber|Telex)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentVorstand(Segment):
        # example recognition:
        # Vorstand: \n Diedrich Dännemark, Peine; \n Helmuth Heintzmann, Herne; \n ...


        def __init__(self):
            super().__init__("Vorstand")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Vorstand|Verwaltungsrat|Verwaltungsbeirat)\s?:", line_text)


            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentAufsichtsrat(Segment):
        # example recognition:
        # Aufsichtsrat: Julius Fromme, Peine, Vors.; \n Hermann Beermann, Hannover, 1.stellv. \n


        def __init__(self):
            super().__init__("Aufsichtsrat")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Aufsichtsrat|Kontrollstelle)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentArbeitnehmervertreter(Segment):
        # example recognition:
        # Arbeitnehmervertreter: \n Martin Birkel, Ehrang;

        def __init__(self):
            super().__init__("Arbeitnehmervertreter")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Arbeitnehmervertreter\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentGruendung(Segment):
        # example recognition:
        # Gründung: 1858.

        def __init__(self):
            super().__init__("Gründung")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Gründung\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentFilialen(Segment):
        # example recognition:
        # Filialen: \n Aachen / Ahlen (Westf.) / Altena (Westf.)/ ...

        def __init__(self):
            super().__init__("Filialen")
            #self.disable()  # this segment is disabled, because it's not really a common segmentation in 1956,
            # maybe activate later

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Filialen|Depositkassen)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentAuslandsvertretungen(Segment):
        # example recognition:
        # Auslandsvertretungen: \n Beirut (für Nah- und Mittel-Ost), Buenos \n ...

        def __init__(self):
            super().__init__("Auslandsvertretungen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Auslandsvertretungen\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentKommanditeUndBank(Segment):
        # example recognition:
        # Kommandite und verbundene  \n Bank: \n von der Heydt-Kersten & Söhne, Wupper- \n

        def __init__(self):
            super().__init__("KommanditeUndBank")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):

            match_start, errors = regu.fuzzy_search(r"^Kommandite.+und.+Bank.+:", combined_texts)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True



    class SegmentTaetigkeitsgebiet(Segment):
        # example recognition:
        # Tätigkeitsgebiet: \n Erzeugung von: Erze, Kohle, Strom,
        # todo check if 'Unternehmensgliederung is really part of this

        def __init__(self):
            super().__init__("Tätigkeitsgebiet")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Tätigkeitsgebiet\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentNiederlassungen(Segment):
        # example recognition:
        # Niederlassungen: \n Hannover, Berlin-Charlottenburg 1,

        def __init__(self):
            super().__init__("Niederlassungen")


        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"(^Niederlassungen\s?:)"
                                                    , line_text, err_number=1)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True



    class SegmentErzeugnisse(Segment):
        # example recognition:
        # Erzeugnisse: \n Ober- und untergäriges Bier; DAB-

        def __init__(self):
            super().__init__("Erzeugnisse")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Es werden erzeugt|Erzeugnisse|Gegenstand\sdes\sUnternehmens|Produktionsprogramm)\s?:", line_text, err_number=1)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentAnlagen(Segment):
        # example recognition:
        # Anlagen: \n Brauerei in Dortmund; Restaurants und ...

        def __init__(self):
            super().__init__("Anlagen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Anlagen\s?:", line_text, err_number=0)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentZweigniederlassungen(Segment):
        # example recognition:
        # Zweigniederlassungen: \n Berlin, Bielefeld, Bremen, Dortmund,

        def __init__(self):
            super().__init__("Zweigniederlassungen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"(^Zweigniederlassungen und Büros\s?:|"
                                                    r"^Zweigniederlassungen in\s?:?|"
                                                    r"^Zweigniederlassungen\s?:|"
                                                    r"^Vertreten\sin\s:|"
                                                    r"^Hauptverwaltung\s?:)",
                                                    line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentWerke(Segment):
        # example recognition:
        # Werke: \n Werksgruppe Geisweid
        # Betriebsstätten: \n Altona, Hamburg-St.Pauli, Hamburg-

        def __init__(self):
            super().__init__("Werke/Betriebsstätten")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Werke in|Werke\s?:|Betriebsstätten\s?:|Eigenwerke\s?:|Zechen\s?:)", line_text, err_number=1)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentBetriebsanlagen(Segment):
        # example recognition:
        # Betriebsanlagen:  \n Beize und Wäscherei, Glüherei, Draht-

        def __init__(self):
            super().__init__("Betriebsanlagen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Betriebsanlagen|Betriebsgesellschaften|Vertriebsgesellschaften|Besitzangaben)\s?:", line_text, err_number=1)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True



    class SegmentBeteiligungsGesellschaften(Segment):
        # example recognition:
        # Wichtigste inländische Beteili- \n gungsgesellschaften
        # Beteiligungsgesellschaften: \n Deutsche Bau- und Siedlungs-Gesellschaft

        def __init__(self):
            super().__init__("Beteiligungsgesellschaften")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            # this doesn't lead to wished results even stops beteiligungen from working
            #match_start, errors = regu.fuzzy_search(r"(?:^|inländische\s?)Beteiligung.+gesellschaft.+:",
            #                                        combi_text,
            #                                        err_number=1)


            match_start, errors = regu.fuzzy_search(r"Beteiligungsgesellschaften",
                                                    combined_texts,
                                                    err_number=1)
            return #todo really return?
            if match_start is not None:

                self.do_match_work(True, match_start, line_index-1, errors)

                return True

    class SegmentBeteiligungen(Segment):
        # example recognition:
        # Beteiligungen: \n Hamburger Verkehrsmittel-Werbung ...
        # Namhafte Beteiligungen: \n Stahlwerke Brüninghaus GmbH ...
        # Wesentliche Beteiligungen: \n Stahlwerke Brüninghaus GmbH ...
        # Maßgebliche Beteiligungen: \n Stahlwerke Brüninghaus GmbH ...
        # Sonstige Beteiligungen: \n ...

        def __init__(self):
            super().__init__("Beteiligungen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):

            # reduced error number to prevent confusion with "Beteiligung:"
            match_bet, errors = regu.fuzzy_search(r"(((?:Namhafte|Wesentliche|Maßgebliche|Wichtigste|Sonstige|Direkte)\s?Beteiligung(en)?)|\s?Beteiligung(en)?)\s?:", line_text, err_number=0)
            if match_bet is not None:
                self.do_match_work(True, match_bet, line_index, errors)
                return True

        def match_stop_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_stop, errors = regu.fuzzy_search(r"^Geschäftsjahr\s?:", line_text)

            if match_stop is not None:
                self.do_match_work(False, match_stop, line_index, errors)
                return True

    class SegmentHaupterzeugnisse(Segment):
        # example recognition:
        # Haupterzeugnisse: \n Form- und Stabstahl.

        def __init__(self):
            super().__init__("Haupterzeugnisse")


        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Haupterzeugnisse\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True



    class SegmentSpezialitaeten(Segment):
        # example recognition:
        # Spezialitäten: \n Breitflanschträger ("'Peiner Träger"),

        def __init__(self):
            super().__init__("Spezialitäten")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Spezialitäten\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentTochtergesellschaften(Segment):
        # example recognition:
        # Besitz- und Betriebsbeschreibung der Tochtergesellschaften: \n
        # todo this is very long content, check this and maybe do subclassification segments here, maybe subsegments

        def __init__(self):
            super().__init__("Tochtergesellschaften")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"(bung der Tochtergesellschaften|^Tochtergesellschaften\sund\ssonstige\sBeteiligungen|^Hauptlagerplatz)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentGeschaeftsjahr(Segment):
        # example recognition:
        # Geschäftsjahr:  Kalenderjahr....

        def __init__(self):
            super().__init__("Geschäftsjahr")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Geschäftsjahr\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentStimmrechtAktien(Segment):
        # example recognition:
        # Stimmrecht d. Aktien i.d.H. -V: \n Je nom. DM 100. - = 1 Stimme.

        def __init__(self):
            super().__init__("StimmrechtAktien")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Stimmrecht der Aktien|Stimmrecht d\.[.\s]*Aktien.+)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentZahlstellen(Segment):
        # example recognition:
        # Zahlstellen: \n Gesellschaftskasse; ...
        # Hinterlegungs- u.Zahlstellen:

        def __init__(self):
            super().__init__("Zahlstellen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"(^Zahlstellen|^Hinterlegungs\- u(nd|\.)\s?Zahlstellen|^Zahlstellen\sbzw.\sHinterlegungsstellen)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentGrundkapital(Segment):
        # example recognition:
        # Grundkapital: \n DM 1222....

        def __init__(self):
            super().__init__("Grundkapital")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Grundkapital\s?:", line_text, err_number=0)

            if match_start is not None:
                if "Bezugsrechte:" in combined_texts:
                    return False # this is a special case


                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentBoersennotiz(Segment):
        # example recognition:
        # Börsennotiz: \n Hannover und im Freiverkehr Berlin \n und Hamburg.

        def __init__(self):
            super().__init__("Börsennotiz")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Börsennotiz|Böresennotierung)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentWKN(Segment):
        # example recognition:
        # Wertpapier-Kenn-Nr.: \n 692100

        def __init__(self):
            super().__init__("Wertpapier-Kenn-Nr")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Wertpapier-Kenn-Nr\.\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True



    class SegmentOrdnungsnrDaktien(Segment):
        # example recognition:
        # Ordnungsnr.d.Aktien: 620200.

        def __init__(self):
            super().__init__("OrdnungsNrAktien")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Ordnungsn.+Aktien\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentStueckelung(Segment):
        # example recognition:
        # Stückelung: \n 99 856 St.-Akt. zu je DM 1 000.-

        def __init__(self):
            super().__init__("Stückelung")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Stückelung\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentRechteVorzugsaktien(Segment):
        # example recognition:
        # Besondere Rechte der Vorzugs- \n aktien: \n Vorzugsdividende bis 10 % des Nennbetra- ..

        def __init__(self):
            super().__init__("RechteVorzugsaktien")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):

            match_start, errors = regu.fuzzy_search(r"Rechte.+Vorzugs.*(?:a|A)ktien.*:", combined_texts, err_number=1)
            # mismatch: 'rechtslose Vorzugsaktien. Aktienkurse:' with e2
            # match: 'Besondere Rechte der an der Börse Hamburg gehandelten Vorzugs-Aktien:' with e0
            # match: 'Besondere Rechte der Vorzugsaktien:' with e0

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentAktionaere(Segment):
        # example recognition:
        # Aktionäre: \n Bankhaus August Lenz & Co., München

        def __init__(self):
            super().__init__("Aktionäre")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^(Aktionärvertreter)\s?:", line_text)

            # this is a possible false positive for above regex
            #match_wrong, errors = regu.fuzzy_search(r"^Aktionären", line_text, err_number=1)

            if match_start is not None:
                match_text = match_start.group()
                if "Aktionären" in match_text:
                    return

                self.do_match_work(True, match_start, line_index, errors)
                return True



    class SegmentGrossaktionaer(Segment):
        # example recognition:
        # Grossaktionär: \n Vereinigte Industrie-Unternehmungen

        def __init__(self):
            super().__init__("Großaktionär")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"^((Gro(?:ss|ß)aktionär(?:\s?|e\s?))|Aktionäre?)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentAnleihen(Segment):
        # example recognition:
        # Anleihe: \n 6 % Amerika-Anleihe von 1928/48
        # todo this has subentry 'Emissionsbeitrag:'
        # Anleihen: \n ... (todo is anleihen anleihe same?)

        def __init__(self):
            super().__init__("Anleihen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"(Anleihe(?:n?)\s?:|^Anleihe$|^Anleihen$|^Wandelanleihen)", line_text)

            if match_start is not None:
                text = match_start.group().strip()
                if "Anteile" in text:
                    return False
                if text[-1] != ":":
                    return False

                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentAktienkurse(Segment):
        # example recognition:
        # Aktienkurse: \n ultimo 1948 19,5 % \n <table> ...
        # Aktienkurse (Düsseldorf): \n ...f


        def __init__(self):
            super().__init__("Aktienkurse")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            # matches ss or ß (group is not capturing)
            #match_start, errors = regu.fuzzy_search(r"Aktienkurse\s?.*:", "Aktienkurse (Düsseldorf):")

            match_start, errors = regu.fuzzy_search(r"Aktienkurse\s?.*:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentKursZuteilungsrechte(Segment):
        # example recognition:
        # c:\n Düsseldorf am 10. Okt ...


        def __init__(self):
            super().__init__("KursVonZuteilungsrechten")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"Kurs von Zuteilungsrechten\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentDividenden(Segment):
        # example recognition:
        # Dividenden: \n 1949/50: 0% (this is for the table dividenden!)
        # not, because sub-item: Dividenden 1949/50-1953/54: \n
        # not, because sub-item: Dividenden ab 1948/50: \n
        #
        # todo think about combining with dividenden auf stammaktien

        def __init__(self):
            super().__init__("Dividenden")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search \
                (r"^(Gezahlte\s)?Dividenden\s?(\(netto\s?\))?:", line_text, err_number=0)
                #(r"^(Dividenden ab (\d{4}\/\d{2})?(\-\d{4}\/\d{2})?|Dividenden)s?:", line_text)
            if match_start is not None and "Kapital" not in combined_texts:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentEmissionsbetrag(Segment):
        # example recognition:
        # Emissionsbetrag: \n DM 15 000 000.-.

        def __init__(self):
            super().__init__("Emissionsbetrag")
            super().disable()  # this is disabled cause it's considered part of anleihen

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search \
                (r"^Emissionsbetrag\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentDividendenAxyAktien(Segment):
        # example recognition:
        # Dividenden auf Stammaktien: \n 1948/49: 0% \n 1950: 0% ...
        # Dividenden auf A-Aktien

        # todo think about combining with dividenden


        def __init__(self):
            super().__init__("DividendenAufXYaktien")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"^Dividenden(?:.+)aktien\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentKonsolBilanzen(Segment):
        # example recognition:
        # Aus den konsolidierten Bilanzen \n 31.12.1971 5 7 31.12.1972

        def __init__(self):
            super().__init__("AusDenKonsolidiertenBilanzen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"^Aus.+konsolidiert.+Bilanzen\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentKonsolGuVRechnungen(Segment):
        # example recognition:
        # Aus den konsolidierten Gewinn- \n und Verlustrechnungen

        def __init__(self):
            super().__init__("Konsolid.Gewinn-u.Verlustrechnungen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            match_start, errors = regu.fuzzy_search(r"Aus.+konsolidiert.+(?:G|g)ewinn.+(?:V|v)erlustrechnungen",
                                                    combined_texts)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True

    class SegmentBezugsrechte(Segment):
        # example recognition:
        # Bezugsrechte: \n 1955: i.V. 4:1 zu 130 %; Abschlag 20 %

        def __init__(self):
            super().__init__("Bezugsrechte")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            #if "Bezugsrechtabschläge insgesamt" in line_text:
            #   return False # false positive, abort
            # nd Berichtigungsaktien
            regex_string = r"(^Bezugsrechtabschläge insgesamt\s?:|^Umtauschrechte\s?:|^Berichtigunsaktien\s?:|^Bezugsrechte und Berichtigungsaktien\s?:|^Bezugsrechte\s?:)"
            match_start, errors = regu.fuzzy_search(regex_string, combined_texts)

            if match_start is not None:
                match_line, errors_2 = regu.fuzzy_search(
                    regex_string,
                    line_text)

                # if the current line contains match index current line
                if match_line:
                    pass_index = line_index
                else:
                    # if combination with previous text contains info match previous index
                    pass_index = line_index-1

                self.do_match_work(True, match_start, pass_index, errors)
                return True

    class SegmentZurGeschaeftslage(Segment):
        # example recognition:
        # Zur Geschäftslage: \n Guter Absatz aller im Bereich der Ilseder

        def __init__(self):
            super().__init__("ZurGeschäftslage")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"^Zur Geschäftslage\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True



    class SegmentAusDenBilanzen(Segment):
        # example recognition:
        # Aus den Bilanzen \n 31.12.1954 31.12.1955 \n (in 1 000 DM)

        def __init__(self):
            super().__init__("AusDenBilanzen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"^Aus (den|der) Bilanz(|en)\s?:", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True


    class SegmentAusGewinnVerlustrechnungen(Segment):
        # example recognition:
        # Aus den Gewinn- und Verlust- \n rechnungen \n Löhne und Gehälter 568 620

        def __init__(self):
            super().__init__("AusGewinnVerlustrechnungen")

        def match_start_condition(self, line, line_text, line_index, features, num_lines, prev_line, combined_texts):
            # matches ss or ß (group is not capturing)
            match_start, errors = regu.fuzzy_search(r"^Aus (der|den) Gewinn- und Verlust- ", line_text)

            if match_start is not None:
                self.do_match_work(True, match_start, line_index, errors)
                return True