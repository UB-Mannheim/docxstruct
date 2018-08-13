# TODO's
# TODO-(jk): ocromore_data -> hocr_data -> data?
# Utils folder which is redundant to python-ocr as an extra repository

# custom imports
from akf_corelib.configuration_handler import ConfigurationHandler
from akf_corelib.database_handler import DatabaseHandler
from akf_corelib.conditional_print import ConditionalPrint
from lib.feature_extractor import FeatureExtractor
from lib.segment_classifier import SegmentClassifier
from lib.output_analysis import OutputAnalysis
from lib.additional_info_handler import AdditionalInfoHandler

# load configuration and printer
CODED_CONFIGURATION_PATH= './configuration/config_parse_hocr_js.conf'
config_handler = ConfigurationHandler(first_init=True, fill_unkown_args=True, \
                                      coded_configuration_paths=[CODED_CONFIGURATION_PATH])
config = config_handler.get_config()
cpr = ConditionalPrint(config.PRINT_MAIN, config.PRINT_EXCEPTION_LEVEL,
                            config.PRINT_WARNING_LEVEL, leading_tag="main_start")

# Basic steps:
feature_extractor = FeatureExtractor()
add_info_handler = AdditionalInfoHandler()
segment_classifier = SegmentClassifier()
output_analyzer = OutputAnalysis()


dh = DatabaseHandler(dbdir="")
dh.set_dirpos(tablename_pos=config.TABLENAME_POS,ocr_profile_pos=config.OCR_PROFILE_POS,\
              ocr_pos=config.OCR_POS,dbname_pos=config.DBPATH_POS)

dh.fetch_files(config.INPUT_FILEGLOB, config.INPUT_FILETYPES)
# get files-list
hocr_files = dh.get_files()


# main iteration loop
for key in hocr_files:
    if "Extra" in key:
        continue

    for file in hocr_files[key]:
        if "msa_best" not in file.ocr_profile:
            continue

        # fetch additional information for current file (if toggled in info)
        additional_info = add_info_handler.fetch_additional_information_simple(file)

        # fetch basic data for current file
        ocromore_data = dh.fetch_ocromore_data(file,additional_info=additional_info)
        cpr.print("Checking file:", ocromore_data['file_info'].path)


        # extract features from basic data
        ocromore_data = feature_extractor.extract_file_features(ocromore_data)
        # line segmentation
        ocromore_data = segment_classifier.classify_file_segments(ocromore_data)
        # segment parsing
        # todo
        # output file synthesis
        # todo

        # output analysis steps
        output_analyzer.log_segmentation_simple(ocromore_data)


