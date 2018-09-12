import json
import pprint

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

    def set_current_main_list(self, segment_tag):
        if segment_tag not in self.my_object.keys():
            self.my_object[segment_tag] = []              # create the main list (all subsequent entries are stored here)

        self.current_main_list = self.my_object[segment_tag]  # create a short link on the main list

    def add_to_my_obj(self, key, value, object_number=0, only_filled=False):

        if only_filled is True and (value == None or value == "" or value == [] or value == {}):
            return

        # fill main list if object index not in
        len_list = len(self.current_main_list)
        if len_list < object_number+1:
            for index in range(len_list,object_number+1):
                self.current_main_list.append({})
        # add or insert to the main_list
        self.current_main_list[object_number][key] = value

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

    def export_as_json_at_key(self, key):

        if key not in self.my_object.keys():
            return None

        my_obj_json = json.dumps(self.my_object[key], indent=5, ensure_ascii=False)
        return my_obj_json

