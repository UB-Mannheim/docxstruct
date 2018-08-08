import json
import glob
import pandas as pd
from os import path

def write_excel_to_json(fileinfo,filepath,filetype,idxcol=None,parse_cols=None,page=0):
    """"
    At the moment a little helper script for the Aktienführer-Project.
    Be free to modify as you wish.
    """
    #if isinstance(parse_cols, list): parse_cols = [parse_cols]
    file = glob.glob(path.normpath(f"{filepath}/**/*{fileinfo.dbname}.{filetype}"),recursive=True)
    if len(file)!= 1: return None
    if filetype in ["xlsx","xls"]:
        df = pd.read_excel(file[0]).set_index("ProfileID")
        jsondata = {fileinfo.dbname:{"Year":fileinfo.dbname}}
        jsondf = df.to_dict(orient="index")
        jsondata.update(jsondf)
        with open(file[0].replace("xlsx","json"),"w") as output:
            json.dump(jsondata, output,indent=4)
    return None

def fetch_additional_information(fileinfo,filepath,filetype,idxcol=None,parse_cols=None,page=0):
    """
    Reads an additional file with information
    It searches the file where the index_name matches tablename or dbname
    :param file:
    :param index_name:
    :return:
    """
    #if isinstance(parse_cols, list): parse_cols = [parse_cols]
    file = glob.glob(path.normpath(f"{filepath}/**/*{fileinfo.dbname}.{filetype}"),recursive=True)
    if len(file)!= 1:
        try:
            raise Exception
        except Exception:
            print("More than one additional information file was found!")
            print(f"Choosen file:{file[0]}!")
            pass
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
            if possible_db_or_tablenames not in current_db_and_table.values():
                del infos[possible_db_or_tablenames]
            else:
                for db_and_table_id, current_db_and_tablename in current_db_and_table.items():
                    if possible_db_or_tablenames == current_db_and_tablename:
                        infos[db_and_table_id] = infos[possible_db_or_tablenames]
                        del infos[possible_db_or_tablenames]
    else:
        return None
    return infos