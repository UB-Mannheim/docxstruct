class KnownUncategories(object):
    """
    List of known entries in test_data which are no categories,
    but are recognized as such
    """

    def __init__(self):
        self.uc = [
            "Beteiligung",   # 1956: is part of Beteiligungen
            "Ferngespräche", # 1956: is part of Fernruf/Telefon
            ""

        ]

    @property
    def uncategories(self):
        return self.uc

