

import io
import os

import pandas as pd
import pandavro as pdx
from azure.storage.filedatalake import DataLakeServiceClient
from detect_delimiter import detect


def initialize_storage_account(storage_account_name, storage_account_key):
    try:
        global service_client
        service_client = DataLakeServiceClient(
            account_url="{}://{}.dfs.core.windows.net".format(
                "https", storage_account_name
            ),
            credential=storage_account_key,
        )
    except Exception as e:
        print(e)


def get_field_value_from_adls(
    storage_name, storage_key, container_name, parent_folder_name, field_list
):
    initialize_storage_account(storage_name, storage_key)
    file_system_client = service_client.get_file_system_client(container_name)
    file_paths = file_system_client.get_paths(path=parent_folder_name)
    main_df = pd.DataFrame()
    for path in file_paths:
        if not path.is_directory:
            file_client = file_system_client.get_file_client(path.name)
            file_ext = os.path.basename(path.name).split(".", 1)[1]
            if file_ext in ["csv", "tsv"]:
                with open("adls_file/csv_file.txt", "wb") as my_file:
                    download = file_client.download_file()
                    download.readinto(my_file)
                with open("adls_file/csv_file.txt", "r") as file:
                    data = file.read()
                row_delimiter = detect(
                    text=data, default=None, whitelist=[",", ";", ":", "|", "\t"]
                )
                processed_df = pd.read_csv("adls_file/csv_file.txt", sep=row_delimiter)
            if file_ext == "parquet":
                download = file_client.download_file()
                stream = io.BytesIO()
                download.readinto(stream)
                processed_df = pd.read_parquet(stream, engine="pyarrow")
            if file_ext == "avro":
                with open("adls_file/avro_file.avro", "wb") as my_file:
                    download = file_client.download_file()
                    download.readinto(my_file)
                processed_df = pdx.read_avro("adls_file/avro_file.avro")
            if not main_df.empty:
                main_df = main_df.append(
                    pd.DataFrame(processed_df[field_list]), ignore_index=True
                )
            else:
                main_df = pd.DataFrame(processed_df[field_list])
    return main_df
