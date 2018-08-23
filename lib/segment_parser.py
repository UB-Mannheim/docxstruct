from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler


class SegmentParser(object):
    """
    Parse the classified segments segment by segment,
    each segment defined code the parser points to.
    """

    def __init__(self):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_SEGMENT_PARSER, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)



    def parse_segments(self, ocromore_data):
        segmentation = ocromore_data['segmentation']
        segmentation_classes = segmentation.my_classes
        for segmentation_class in segmentation_classes:

           # if the class segment was recognized ...
           if segmentation_class.is_start_segmented():

               # get the unique identifier for this class
               segment_tag = segmentation_class.get_segment_tag()
               self.trigger_mapped_function(segment_tag)
        pass

    def trigger_mapped_function(self, segment_tag):

        key_val = {
            "Sitz": self.sitz_funct
        }

        if segment_tag not in key_val.keys():
            return

        key_val[segment_tag].__call__('text a text')

    def sitz_funct(self, text1):
        print(text1)