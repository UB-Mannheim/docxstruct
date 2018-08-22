import re

class KnownUncategories(object):
    """
    List of known entries in test_data which are no categories,
    but are recognized as such
    """

    def __init__(self):

        # un-category regex strings (care for commas)
        self.uc = [
            "Beteiligung",                   # 1956: is part of Beteiligungen
            "Ferngespräche",                 # 1956: is part of Fernruf/Telefon
            "Kapital",                       # 1956: is part of multiple top-level items
            "Umstellung \d\d?",              # 1956: is part of Grundkapital or other
            "Dividenden ab \d{4}.*",         # 1956: is part of Dividenden or other (with year or yearspan)s
            "^Kurs.*",                       # 1956: second level tag
            "ab \d{4}(\/\d{2})?"             # 1956: i.e "ab 1949/50"-part of other categories
        ]

        # create corresponding regexes
        self.uc_regex = []
        for item in self.uc:
            regex_compiled = re.compile(item)
            self.uc_regex.append(regex_compiled)

    @property
    def uncategories(self):
        return self.uc

    def check_uncategories(self, text_to_check):
        """
        Allows to compare a tag against the existing uncategories
        :param text_to_check: tag text
        :return: True if un-category, False if not
        """
        for regex_to_check in self.uc_regex:
            match_result = regex_to_check.search(text_to_check)
            if match_result is not None:
                return True

        return False