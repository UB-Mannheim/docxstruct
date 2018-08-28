import json

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

    def set_current_main_list(self, segment_tag):
        if segment_tag not in self.my_object.keys():
            self.my_object[segment_tag] = []              # create the main list (all subsequent entries are stored here)
        self.current_main_list = self.my_object[segment_tag]  # create a short link on the main list

    def add_to_my_obj(self, key, value, object_number=0):
        # fill main list if object index not in
        len_list = len(self.current_main_list)
        if len_list < object_number+1:
            for index in range(len_list,object_number+1):
                self.current_main_list.append({})
        # add or insert to the main_list
        self.current_main_list[object_number][key] = value

    def print_me_and_return(self):
        print("my_object is:", self.my_object)
        return self.my_object

    def export_as_json(self):
        my_obj_json = json.dumps(self.my_object, indent=5)
        return my_obj_json