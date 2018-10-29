import json
import pprint
from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler

class EndobjectFactory(object):
    """
    Creates an object with the following structure and provides exporting methods:

    segment_tag_1: [                ---> this level is created by set_current_main_list
        {
            type: "Sitz"            ---> add this level entries with add_to_my_object object_number=0
            city: "Neustadt"
        },
        {
            type: "Sitz"            ---> add this level entries with add_to_my_object object_number=0
            city: "Neustadt"
        }

    ],
    segment_tag_2: [
        {
            ...
        }
        ...
    ]
    """
    def __init__(self):
        self.my_object = {}
        self.current_main_list = None
        self.pp = pprint.PrettyPrinter(indent=5)

        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_OUTPUT_ANALYSIS, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)

    def set_current_main_list(self, segment_tag):
        if segment_tag not in self.my_object.keys():
            self.my_object[segment_tag] = []              # create the main list (all subsequent entries are stored here)

        self.current_main_list = self.my_object[segment_tag]  # create a short link on the main list

    def add_to_my_obj(self, key, value, object_number=0, only_filled=False):

        if only_filled is True and (value == None or value == "" or value == [] or value == {}):
            return False

        # fill main list if object index not in
        len_list = len(self.current_main_list)
        if len_list < object_number+1:
            for index in range(len_list,object_number+1):
                self.current_main_list.append({})

        self.cpr.print("Adding value to List,- ObjectNr.:", object_number,"Key:", key, "Value:", value)
        # add or insert to the main_list
        self.current_main_list[object_number][key] = value
        return True

    def print_me_and_return(self):
        print("my_object is:")
        self.pp.pprint(self.my_object)
        return self.my_object

    def print_current_main(self):
        print("current_main:")
        self.pp.pprint(self.current_main_list)

    def export_as_json(self):
        my_obj_json = json.dumps(self.my_object, indent=5, ensure_ascii=False)
        return my_obj_json

    def export_as_json_at_key(self, key, remove_first_object=False):

        if key not in self.my_object.keys():
            return None

        my_obj = self.my_object[key]
        if remove_first_object:
            if len(my_obj) >= 1:
                my_obj = my_obj[1:]  # remove the first object which usally contains generic info

        my_obj_json = json.dumps(my_obj, indent=5, ensure_ascii=False)
        return my_obj_json

    def diff_seg_to_orig_at_key(self, key):

        def fetch_subentries_recursive(entry):
            final_texts = []

            for item in entry:
                if isinstance(entry, list):
                    value = item
                else:
                    # item is a key
                    value = entry[item]
                if isinstance(value, str):
                    final_texts.append(value)
                elif isinstance(value, int):
                    final_texts.append(str(value))
                elif isinstance(value, object):
                    obj_size = len(value)
                    if obj_size > 0:
                        recursive_texts = fetch_subentries_recursive(value)
                        final_texts.extend(recursive_texts)

            return final_texts

        if key not in self.my_object.keys():
            return None

        my_data = self.my_object[key]

        # check if the orig-post property can exist warn if not
        if not self.config.ADD_INFO_ENTRY_TO_OUTPUT:
            self.cpr.printw("trying to fetch original data, original data is not added to results")
            self.cpr.printw("toggle ADD_INFO_ENTRY_TO_OUTPUT in config to True")
        if len(my_data) <= 0:
            self.cpr.printw("no data to do returning")
            return

        return # todo this seems to be wrong
        # copy orig string
        original_text = my_data[0]['origpost']
        rest_text = original_text

        # fetch parsed entries for diff
        all_final_entries = []  # array of final entries
        for index in range(1, len(my_data)):
            entry = my_data[index]
            final_entries = fetch_subentries_recursive(entry)
            all_final_entries.extend(final_entries)

        # order diff data after length
        all_final_entries.sort(key=lambda x: len(x))
        all_final_entries.reverse()

        # subtract
        for text in all_final_entries:
            rest_text = rest_text.replace(text, "")

            rest_text = rest_text.strip()

        return rest_text, original_text

    def diff_parsed_to_orig_at_key(self, key):

        def fetch_subentries_recursive(entry):
            final_texts = []

            for item in entry:
                if isinstance(entry, list):
                    value = item
                else:
                    # item is a key
                    value = entry[item]
                if isinstance(value, str):
                    final_texts.append(value)
                elif isinstance(value, int):
                    final_texts.append(str(value))
                elif isinstance(value, object):
                    obj_size = len(value)
                    if obj_size > 0:
                        recursive_texts = fetch_subentries_recursive(value)
                        final_texts.extend(recursive_texts)

            return final_texts

        if key not in self.my_object.keys():
            return None
        if key == "Erzeugnisse":
            print("todo remove debug")


        my_data = self.my_object[key]

        # check if the orig-post property can exist warn if not
        if not self.config.ADD_INFO_ENTRY_TO_OUTPUT:
            self.cpr.printw("trying to fetch original data, original data is not added to results")
            self.cpr.printw("toggle ADD_INFO_ENTRY_TO_OUTPUT in config to True")
        if len(my_data) <= 0:
            self.cpr.printw("no data to do returning")
            return
        # copy orig string
        original_text = my_data[0]['origpost']
        rest_text = original_text

        # fetch parsed entries for diff
        all_final_entries = []  # array of final entries
        for index in range(1, len(my_data)):
            entry = my_data[index]
            final_entries = fetch_subentries_recursive(entry)
            all_final_entries.extend(final_entries)

        # order diff data after length
        all_final_entries.sort(key=lambda x: len(x))
        all_final_entries.reverse()

        #if key == "Sitz" and "Zement" in rest_text:
        #    print("debugging check")

        # subtract
        for text in all_final_entries:
            text_stripped = text.strip() # remove spaces so texts better fit in
            rest_text = rest_text.replace(text_stripped, "")
            rest_text = rest_text.strip()

        return rest_text, original_text