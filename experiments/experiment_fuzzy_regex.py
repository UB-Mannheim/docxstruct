import re
import regex # backwards compatible to 're', but additional functionality
# https://pypi.org/project/regex/ ---> 'fuzzy'-matches
from akf_corelib.regex_util import RegexUtil as regu

test_texts = [
    "Fernschreiber:",
    "Fernschreiber :",
    "F3rnschreiber:",
    "F3pnschreiber:",
    "ernschreiber:",
    "ernschr3iber:",
    "Fernschreiber!",
    "asdwevc!"
]


example = regex.fullmatch(r"(?:cats|cat){e<=1}", "cat").fuzzy_counts
print("Example is:", example)

def regexfuzzy_search(pattern, text ,err_number=2):
    compiled_wrapper = regex.compile(r"(?:"+pattern+"){e<="+str(err_number)+"}")
    result = compiled_wrapper.search(text)
    return result


# costs of insert, delete, substitute can be defined {2i+2d+1s<=4} each insertion costs 2 etc
def test_1():
    for text in test_texts:
        compiled = regex.compile(r"(?:^Fernschreiber\s?:){e<=1}")
        match_stop = compiled.search(text)
        if match_stop is not None:
            (substs, inserts, deletions) = match_stop.fuzzy_counts
            accumulated_errs = substs + inserts + deletions

            print("Text is:", text, "Match is True", "Errors:", (substs, inserts, deletions) )
        else:
            print("Text is:", text, "Match is False", "Errors: higher than limit")


# search with dynamic wrapper function (better looking regex)
for text in test_texts:
    match_stop = regexfuzzy_search("^Fernschreiber\s:", text)
    if match_stop is not None:
        (substs, inserts, deletions) = match_stop.fuzzy_counts
        accumulated_errs = substs + inserts + deletions

        print("Text is:", text, "Match is True", "Errors:", (substs, inserts, deletions))
    else:
        print("Text is:", text, "Match is False", "Errors: higher than limit")



match_shorter_text, errs  = regu.fuzzy_search("^Texte", "Text", err_number=2)
#if match_shorter_text:
    #result = match_shorter_text.text

# jk example
match_shorter_text2, errs2  = regu.fuzzy_search("^rückstellungen$", "rücksstellungen", err_number=2)
if match_shorter_text2:
    result = match_shorter_text2.text