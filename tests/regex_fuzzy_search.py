#todo add testing and check for regex fuzzy search implementation (with error_number correctness)

from akf_corelib.regex_util import RegexUtil as regu


text = "my test text"
match, errs = regu.fuzzy_search(r"", text, err_number=0)