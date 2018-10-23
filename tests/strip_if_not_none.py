from lib.data_helper import DataHelper as dh


# single trail sc
test_text_1 = "this is my text)"
test_result_1 = dh.strip_if_not_none(test_text_1, ")., ")


# multi trail sc
test_text_2 = "this is my text)..."
test_result_2 = dh.strip_if_not_none(test_text_2, ")., ")


# single start sc multi trail sc
test_text_3 = ")this is my text)..."
test_result_3 = dh.strip_if_not_none(test_text_3, ")., ")

# multi start sc multi trail sc
test_text_4 = ")....this is my text)..."
test_result_4 = dh.strip_if_not_none(test_text_4, ")., ")


# with spaces
test_text_5 = ").. ..this is my text). .."
test_result_5 = dh.strip_if_not_none(test_text_5, ")., ")


# non-pattern break
test_text_6 = ").(...this is my text).(.."
test_result_6 = dh.strip_if_not_none(test_text_6, ")., ")

print("done")
