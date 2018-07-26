# TODO's
# Utils folder which is redundant to python-ocr as an extra repository

# custom imports
from akf_corelib.configuration_handler import ConfigurationHandler
from akf_corelib.database_handler import DatabaseHandler
from lib.feature_extractor import FeatureExtractor
from lib.segment_classifier import SegmentClassifier

# load configuration
CODED_CONFIGURATION_PATH= './configuration/config_parse_hocr_js.conf'
config_handler = ConfigurationHandler(first_init=True, fill_unkown_args=True, \
                                      coded_configuration_paths=[CODED_CONFIGURATION_PATH])
config = config_handler.get_config()


# Basic steps:
feature_extractor = FeatureExtractor()
segment_classifier = SegmentClassifier()

dh = DatabaseHandler(dbdir="")
dh.set_dirpos(tablename_pos=config.TABLENAME_POS,ocr_profile_pos=config.OCR_PROFILE_POS,\
              ocr_pos=config.OCR_POS,dbname_pos=config.DBPATH_POS)

dh.fetch_files(config.INPUT_FILEGLOB, config.INPUT_FILETYPES)
# get files-list
hocr_files = dh.get_files()


# main iteration loop
for key in hocr_files:
    for file in hocr_files[key]:
        # fetch basic data for current file
        ocromore_data = dh.fetch_ocromore_data(file)
        # extract features from basic data
        ocromore_data = feature_extractor.extract_file_features(ocromore_data)
        # line segmentation
        ocromore_data = segment_classifier.classify_file_segments(ocromore_data)
        # segment parsing
        # todo
        # output file synthesis
        # todo
        break
    break

# 4. content classifictation

# 5. output synthesis (if not done in previous steps)