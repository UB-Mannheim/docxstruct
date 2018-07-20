# custom imports
from configuration.configuration_handler import ConfigurationHandler
from utils.hocr_converter import HocrConverter
from utils.database_handler import DatabaseHandler

# external imports
from pathlib import Path


# load configuration
CODED_CONFIGURATION_PATH= './configuration/config_parse_hocr_js.conf'
config_handler = ConfigurationHandler(first_init=True, fill_unkown_args=True, \
                                      coded_configuration_paths=[CODED_CONFIGURATION_PATH])
config = config_handler.get_config()


# Basic steps:
# 1. Read in the .hocr-files (then, for each file ...)
# = str(Path(config.DBDIR_READER).absolute())
dh = DatabaseHandler(dbdir="")
dh.set_dirpos(tablename_pos=config.TABLENAME_POS,ocr_profile_pos=config.OCR_PROFILE_POS,\
              ocr_pos=config.OCR_POS,dbname_pos=config.DBPATH_POS)

dh.fetch_files(config.INPUT_FILEGLOB, config.INPUT_FILETYPES)
test = dh.get_files()
dfs = dh.fetch_dataframe()
print(test)


# 2. line feature extraction

# 3. line segmentation

# 4. content classifictation

# 5. output synthesis (if not done in previous steps)