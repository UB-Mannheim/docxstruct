# custom imports
from akf_corelib.configuration_handler import ConfigurationHandler
from akf_corelib.database_handler import DatabaseHandler
from akf_corelib.conditional_print import ConditionalPrint
from lib.feature_extractor import FeatureExtractor
from lib.segment_classifier import SegmentClassifier
from lib.segment_parser import SegmentParser
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
segment_parser = SegmentParser(output_analyzer)


dh = DatabaseHandler(dbdir="")
dh.set_dirpos(tablename_pos=config.TABLENAME_POS,ocr_profile_pos=config.OCR_PROFILE_POS,\
              ocr_pos=config.OCR_POS,dbname_pos=config.DBPATH_POS)

dh.fetch_files(config.INPUT_FILEGLOB, config.INPUT_FILETYPES)
# get files-list
hocr_files = dh.get_files()


# main iteration loop
for key in hocr_files:
    #if "1976" not in key:
    #    continue

    accumulated_diff_info = output_analyzer.AccumulatedInfo()
    ocromore_data = None
    ctr_test = 0

    my_list = hocr_files[key]
    for file in my_list:
        if "msa_best" not in file.ocr_profile:
            continue


        #if not "0064_1" in file.name and not "0142_1" in file.name:
        #    continue
        # fetch additional information for current file (if toggled in info)
        additional_info = add_info_handler.fetch_additional_information_simple(file)

        # fetch basic data for current file
        ocromore_data = dh.fetch_ocromore_data(file, additional_info=additional_info)
        cpr.print("Checking file:", ocromore_data['file_info'].path)

        # extract features from basic data
        ocromore_data = feature_extractor.extract_file_features(ocromore_data)
        # line segmentation
        ocromore_data = segment_classifier.classify_file_segments(ocromore_data)
        # segment parsing
        ocromore_data = segment_parser.parse_segments(ocromore_data)
        # output file synthesis
        segment_parser.write_result_to_output(True, ocromore_data)
        # todo

        # output analysis steps
        output_analyzer.log_segmentation_simple(ocromore_data)  # log the recognized segmentation
        output_analyzer.log_parsed_output(ocromore_data)        # log the parsed segments into tag-based files
        diff_info = output_analyzer.log_unsegmentated(ocromore_data)
        accumulated_diff_info = output_analyzer.accumulate_diff_info(ocromore_data, diff_info, accumulated_diff_info)
        ctr_test += 1
        if ctr_test >= 500:
            break

        # clear the current result in segment_parser cache to parse the next one
        segment_parser.clear_result(output_analyzer)

    # output analysis: print diff info for this year (accumulated over all tables/year)
    output_analyzer.log_accumulated_unsegmentated(accumulated_diff_info, ocromore_data)


