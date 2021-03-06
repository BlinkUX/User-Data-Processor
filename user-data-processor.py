#!/usr/bin/env python

# Copyright 2015, Institute for Systems Biology.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os

import user_gen.molecular_processing
import user_gen.user_gen_processing
import argparse


def generate_bq_schema(columns):
    obj = []
    columns.sort(key=lambda x: x['INDEX'])
    for column in columns:
        obj.append({'name': column['NAME'], 'type': column['TYPE']})
    return obj



def main(user_data_config, etl_config_file):
    schemas_dir = os.path.join(os.getcwd(), 'schemas/')

    configs = open(user_data_config).read()
    data = json.loads(configs)

    project_id = data['GOOGLE_PROJECT']
    user_project = data['USER_PROJECT']
    user_study = data['STUDY']
    bucketname = data['BUCKET']
    bq_dataset = data['BIGQUERY_DATASET']
    cloudsql_tables = {
        'METADATA_DATA': data['USER_METADATA_TABLES']['METADATA_DATA'],
        'METADATA_SAMPLES': data['USER_METADATA_TABLES']['METADATA_SAMPLES'],
        'FEATURE_DEFS': data['USER_METADATA_TABLES']['FEATURE_DEFS']
    }

    # Check for user_gen files and process them first
    user_gen_list = []
    mol_file_list = []
    low_level_list = []
    for file in data['FILES']:
        if file['DATATYPE'] == 'user_gen':
            user_gen_list.append(file)
        elif file['DATATYPE'] == 'low_level':
            low_level_list.append(file)
        else:
            mol_file_list.append(file)

    # TODO: Add processor for low level file listings

    print 'Number of user_gen files: ', len(user_gen_list)
    print 'Number of molecular files: ', len(mol_file_list)
    print 'Number of low level files: ', len(low_level_list)

    # Process all user_gen files together
    if len(user_gen_list):
        user_gen.user_gen_processing.process_user_gen_files(project_id,
                                                            user_project,
                                                            user_study,
                                                            bucketname,
                                                            bq_dataset,
                                                            cloudsql_tables,
                                                            user_gen_list)

    # Process all other datatype files
    if len(mol_file_list):
        for file in mol_file_list:
            table_name = file['BIGQUERY_TABLE_NAME']

            inputfilename = file['FILENAME']
            blob_name = inputfilename.split('/')[1:] # Path without bucket. Assuming bucket name appended to front of file path.
            outputfilename = '{0}.out'.format(inputfilename.split('/')[-1]) # Get the actual file name
            bucket_name = inputfilename.split('/')[0] # Get the bucketname

            metadata = {
                'sample_barcode': file.get('SAMPLEBARCODE', ''),
                'participant_barcode': file.get('PARTICIPANTBARCODE', ''),
                'project_id': user_project,
                'study_id': user_study,
                'platform': file.get('PLATFORM', ''),
                'pipeline': file.get('PIPELINE', ''),
            }

            # Update metadata_data table in cloudSQL
            metadata['file_path'] = inputfilename
            metadata['file_name'] = inputfilename.split('/')[-1]
            metadata['data_type'] = file['DATATYPE']

            # Transform and load metadata
            user_gen.molecular_processing.parse_file(project_id,
                                                     bq_dataset,
                                                     bucket_name,
                                                     file,
                                                     blob_name,
                                                     outputfilename,
                                                     metadata,
                                                     cloudsql_tables
                                                     )

    if len(low_level_list):
        for file in low_level_list:
            pass
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'config_file',
        help='Path to the config file for the job'
    )

    args = parser.parse_args()

    # log_filename = 'etl_{0}.log'.format(args.datatype)
    # log_name = 'etl_{0}'.format(args.datatype)
    # log = configure_logging(log_name, log_filename)

    # print args.config_file

    main(
        args.config_file,
        './config/data_etl_template.json',
    )
