from lib.data_helper import DataHelper as dh


# single trail sc
test_text_1 = "this is my text)"
test_result_1 = dh.strip_if_not_none(test_text_1, ")., ")
test_result_1s = test_text_1.strip(")., ")
test_result_1r = dh.remove_multiple_outbound_chars(test_text_1)

# multi trail sc
test_text_2 = "this is my text)..."
test_result_2 = dh.strip_if_not_none(test_text_2, ")., ")
test_result_2s = test_text_2.strip(")., ")
test_result_2r = dh.remove_multiple_outbound_chars(test_text_2)


# single start sc multi trail sc
test_text_3 = ")this is my text)..."
test_result_3 = dh.strip_if_not_none(test_text_3, ")., ")
test_result_3s = test_text_3.strip(")., ")
test_result_3r = dh.remove_multiple_outbound_chars(test_text_3)

# multi start sc multi trail sc
test_text_4 = ")....this is my text)..."
test_result_4 = dh.strip_if_not_none(test_text_4, ")., ")
test_result_4s = test_text_4.strip(")., ")
test_result_4r = dh.remove_multiple_outbound_chars(test_text_4)


# with spaces
test_text_5 = ").. ..this is my text). .."
test_result_5 = dh.strip_if_not_none(test_text_5, ")., ")
test_result_5s = test_text_5.strip(")., ")
test_result_5r = dh.remove_multiple_outbound_chars(test_text_5)


# non-pattern break
test_text_6 = ").(...this is my text).(.."
test_result_6 = dh.strip_if_not_none(test_text_6, ")., ")
test_result_6s = test_text_6.strip(")., ")
test_result_6r = dh.remove_multiple_outbound_chars(test_text_6)

print("done")



# strip for comparison

test_strip = " u."
test_strip_1 = test_strip.strip(". ")


print("done2")

