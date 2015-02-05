#!/usr/bin/env python3

from generator import Generator
from scraper import Scraper
import os, json

DOCS_URL = "http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/"
CONTENTS_PAGE = "aws-template-resource-type-ref.html"
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    generator = Generator()
    scraper = Scraper(DOCS_URL)
    classes = scraper.get_documentation_pages(CONTENTS_PAGE)

    property_types = {}
    for key, value in classes.items():
        properties = scraper.get_properties(value)
        if properties:
            property_types[key] = properties

    file_path = os.path.join(CURRENT_DIR, "aws_properties_map.json")
    with open(file_path, "w") as output_file:
        json.dump(property_types, output_file, sort_keys=True, indent=2)


if __name__ == '__main__':
    main()
