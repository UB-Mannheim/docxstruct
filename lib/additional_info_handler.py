from akf_corelib.conditional_print import ConditionalPrint
from akf_corelib.configuration_handler import ConfigurationHandler


import json
import glob
import pandas as pd
from os import path



class AdditionalInfoHandler(object):

    def __init__(self):
        config_handler = ConfigurationHandler(first_init=False)

        self.config = config_handler.get_config()
        self.cpr = ConditionalPrint(self.config.PRINT_ADDITIONAL_INFO_HANDLER, self.config.PRINT_EXCEPTION_LEVEL,
                                    self.config.PRINT_WARNING_LEVEL, leading_tag=self.__class__.__name__)
        self.cpr.print("init additional info handler")


    def write_excel_to_json(self, fileinfo,filepath,filetype,idxcol=None,parse_cols=None,page=0):
        """"
        At the moment a little helper script for the Aktienführer-Project.
        Be free to modify as you wish.
        """
        #if isinstance(parse_cols, list): parse_cols = [parse_cols],
        additional_filepath = path.normpath(f"{filepath}/**/*{fileinfo.dbname}.{filetype}")
        file = glob.glob(additional_filepath,recursive=True)
        if len(file)!= 1: return None
        if filetype in ["xlsx","xls"]:
            df = pd.read_excel(file[0]).set_index("ProfileID")
            jsondata = {fileinfo.dbname:{"Year":fileinfo.dbname}}
            jsondf = df.to_dict(orient="index")
            jsondata.update(jsondf)
            with open(file[0].replace("xlsx","json"),"w") as output:
                json.dump(jsondata, output,indent=4)
        return None

    def fetch_additional_information_simple(self, file):
        """
        Same as fetch additional information, but config related info is already included in given
        parameters
        :return: additional info
        """
        if self.config.ADDITIONAL_INFORMATION:
            additional_info = self.fetch_additional_information(file, self.config.INPUT_ADDINFOPATH,
                                                           idxcol= self.config.IDXCOL,parse_cols=self.config.PARSE_COLS,
                                                           filetype =self.config.INPUT_ADDINFOFILETPYE)
            return additional_info

        return None

    def fetch_additional_information(self, fileinfo, filepath, filetype, idxcol=None, parse_cols=None, page=0):
        """
        Reads an additional file with information
        It searches the file where the index_name matches tablename or dbname
        :param file:
        :param index_name:
        :return: additional info
        """
        #if isinstance(parse_cols, list): parse_cols = [parse_cols]
        additional_filepath = path.normpath(f"{filepath}/**/*{fileinfo.dbname}.{filetype}")
        file = glob.glob(additional_filepath,recursive=True)

        len_files = len(file)
        if len_files > 1:
            self.cpr.printex("More than one additional information file was found!")
            return None
        if len_files == 0:
            self.cpr.printex("No additional information file was found!")
            return None

        file = file[0]
        current_db_and_table = {"db": fileinfo.dbname, "table": fileinfo.tablename}
        if filetype in ["xlsx","xls"]:
            infos = {}
            info_df = pd.read_excel(file)#.set_index("ProfileID")
            parse_cols.remove(idxcol)
            for db_and_table_id, current_db_and_tablename in current_db_and_table.items():
                infos[db_and_table_id] = {}
                for line, rubric_content in info_df.loc[info_df[idxcol]==current_db_and_tablename][parse_cols].to_dict(orient="index").items():
                    for rubric, content in rubric_content.items():
                        if rubric != idxcol:
                            if infos[db_and_table_id].get(rubric,None) is None:
                                infos[db_and_table_id][rubric] = content
                            elif infos[db_and_table_id].get(rubric,None) != content:
                                if not isinstance(infos[db_and_table_id][rubric], list): infos[db_and_table_id][rubric] = [infos[db_and_table_id][rubric]]
                                infos[db_and_table_id][rubric].append(content)
        elif filetype == "json":
            with open(file, "r") as add_info_file:
                infos = json.load(add_info_file)

            for possible_db_or_tablenames in reversed(list(infos.keys())):
                possible_db_or_tablenames_orig = possible_db_or_tablenames # unchanged name

                if self.config.ADD_INFO_SIMPLIFIED_NAME_COMPARISON:
                    psplit = possible_db_or_tablenames.split("-")
                    possible_db_or_tablenames = psplit[0]

                if possible_db_or_tablenames not in current_db_and_table['table']:
                    del infos[possible_db_or_tablenames_orig]
                else:
                    for db_and_table_id, current_db_and_tablename in current_db_and_table.items():
                        if possible_db_or_tablenames == current_db_and_tablename:
                            infos[db_and_table_id] = infos[possible_db_or_tablenames_orig]
                            del infos[possible_db_or_tablenames_orig]
        else:
            return None
        return infos