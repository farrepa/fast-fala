import fileinput
import gzip
import hashlib
import json
import os
import re
from pathlib import Path
from string import Template

import requests
import xlrd

dist_dir = Path.cwd() / os.environ.get('DIST_DIR', 'dist')


def fetch_spreadsheet(listing_url, spreadsheet_filename):
    listing_response = requests.get(listing_url)
    regex_results = re.search(
        r'href="(?P<spreadsheet_url>https://assets.publishing.service.gov.uk/[a-zA-Z0-9_/]+.xlsx)"',
        listing_response.text)
    spreadsheet_url = regex_results.groupdict().get('spreadsheet_url')
    spreadsheet_response = requests.get(spreadsheet_url)
    md5 = hashlib.md5()
    with open(spreadsheet_filename, 'wb') as fd:
        for chunk in spreadsheet_response.iter_content(chunk_size=128):
            fd.write(chunk)
            md5.update(chunk)
    return md5


def get_categories(spreadsheet_filename):
    wb = xlrd.open_workbook(spreadsheet_filename, on_demand=True)
    ws = wb.sheet_by_index(0)
    categories_start_col = 8
    categories_end_col = 21
    header_row_index = 4
    return ws.row_values(header_row_index, categories_start_col, categories_end_col)


def extract_providers(spreadsheet_filename):
    # N.B. Use only with trusted sources while defusedxml not implemented
    # https://xlrd.readthedocs.io/en/latest/vulnerabilities.html#xml-vulnerabilities-and-excel-files

    wb = xlrd.open_workbook(spreadsheet_filename, on_demand=True)
    ws = wb.sheet_by_index(0)

    data_start_col = 1
    data_end_col = 21
    header_row_index = 4
    header = ['id']
    header.extend(ws.row_values(header_row_index, data_start_col, data_end_col))

    providers = []
    for provider_id, provider_row in enumerate(range(header_row_index + 1, ws.nrows)):
        values = [provider_id]
        values.extend(ws.row_values(provider_row, data_start_col, data_end_col))
        providers.append(dict(zip(header, values)))
        # yield(dict(zip(header, values)))
    # TODO delete spreadsheet_filename
    return providers


def flatten_bulk_lookup_results(raw_results):
    flattened_results = {}
    for result in raw_results:
        postcode = result.get('query')
        details = result.get('result', {})
        if details:
            lng_lat = {'longitude': details.get('longitude'), 'latitude': details.get('latitude')}
            flattened_results[postcode] = lng_lat
    return flattened_results


def geocode_provider_postcodes(providers, batch_size=100):
    bulk_lookup_url = "https://api.postcodes.io/postcodes"
    lookup_results = []
    for i in range(0, len(providers), batch_size):
        lookup_batch = providers[i:i + batch_size]
        lookup_batch = [provider.get('Postcode') for provider in lookup_batch]
        bulk_lookup_response = requests.post(bulk_lookup_url, data={"postcodes": lookup_batch})
        lookup_results.extend(bulk_lookup_response.json().get('result'))
    return flatten_bulk_lookup_results(lookup_results)


def process_providers(unprocessed_providers, geolocated_postcodes, categories):
    processed_providers = []
    for provider in unprocessed_providers:
        address_fields = ['Address Line 1', 'Address Line 2', 'Address Line 3', 'City', 'Postcode']
        postcode = provider.get('Postcode')
        lat_lng = geolocated_postcodes.get(postcode, {})
        clean_provider = {
            'name': provider.get('Firm Name'),
            'address': '\n'.join([provider.get(part) for part in address_fields if provider.get(part)]),
            'tel': provider.get('Telephone Number'),
            'categories': [category for category in categories if provider.get(category)],
            'lngLat': [lat_lng.get('longitude'), lat_lng.get('latitude')]
        }
        processed_providers.append(clean_provider)
    return processed_providers


def remove_file(path):
    try:
        os.remove(path)
    except OSError:
        pass


def generate_providers_json():
    default_listing_url = "https://www.gov.uk/government/publications/directory-of-legal-aid-providers"
    listing_url = os.environ.get('LISTING_URL', default_listing_url)
    spreadsheet_temp_filename = 'temp.xlsx'
    md5 = fetch_spreadsheet(listing_url, spreadsheet_temp_filename)
    processed_filename = f"providers.{md5.hexdigest()}.json"
    output_filename = dist_dir / processed_filename

    if Path(output_filename).exists():
        print("Source spreadsheet unchanged")
    else:
        categories = get_categories(spreadsheet_temp_filename)
        providers = extract_providers(spreadsheet_temp_filename)
        geolocated_postcodes = geocode_provider_postcodes(providers)
        processed_providers = process_providers(providers, geolocated_postcodes, categories)
        with open(output_filename, 'w') as fd:
            json.dump(processed_providers, fd)
        print(f"Generated {processed_filename}")
    remove_file(spreadsheet_temp_filename)
    return processed_filename


def compile_static():
    bundles = [
        {"in": ['lib/axios.min.js', 'lib/turf.min.js', 'lib/underscore.min.js', 'lib/vue.min.js', 'lib/mapbox-gl.js'],
         "out": 'fastfala.min.js'},
        {"in": ['main.css'],
         "out": 'main.css'},
        {"in": ['lib/mapbox-gl.css'],
         "out": 'mapbox-gl.css'},
        {"in": ['lib/mapstack-bright.json'],
         "out": 'mapstack-bright.json'},
    ]
    for bundle in bundles:
        in_files = fileinput.input(bundle['in'])
        with open(dist_dir / bundle['out'], 'w') as output_file:
            output_file.writelines(in_files)
        with gzip.open((dist_dir / bundle['out']).with_suffix('.gz'), 'wb') as output_gz:
            output_gz.writelines(in_files)


def generate_website(providers_json):
    with open('index.html', 'r') as template_file:
        s = Template(template_file.read())
        rendered_template = s.substitute(providers_json=providers_json)
        with open(dist_dir / 'index.html', 'w') as rendered_file:
            rendered_file.write(rendered_template)
    compile_static()
    print("Built website")


providers_json = generate_providers_json()
generate_website(providers_json)
