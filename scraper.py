from bs4 import BeautifulSoup
from urllib.request import urlopen

import os, pprint, re

class Scraper(object):
    """ Class for retrieving AWS documentation """
    def __init__(self, docs_url):
        self.docs_url = docs_url


    def get_documentation_pages(self, toc_page):
        """ Given a URL representing the table of contents, find every link
        on the page map its text to it's href
        Returns a dictionary in the format { "link text": "docs_page.html", ...}
        """
        docs_page = urlopen("%s/%s" % (self.docs_url, toc_page))
        soup = BeautifulSoup(docs_page)
        links = soup.find_all('a')

        # Parse the list of all classes to get names and URLS
        pages = {}
        for link in links:
            if not link.getText() or 'AWS' not in link.getText():
                continue
            cleanKey = link.getText().replace('\n', '').replace(' ', '')
            pages[cleanKey] = link['href']

        return pages


    def get_property_list(self, page_url):
        """ Takes the given page_url and appends it to the docs_url.
        From this new URL, extract the text from the code block.
        Return the extracted code """

        if 'aws' not in page_url or 'cfn' in page_url or '.html' not in page_url:
            return None

        print("Fetching: %s" % page_url)
        class_page = urlopen("%s/%s" % (self.docs_url, page_url))
        if class_page:
            soup = BeautifulSoup(class_page)
            properties = soup.find_all('pre')
            if len(properties) > 0:
                return properties[0].getText()
            else:
                return None
        return None


    def get_properties(self, page_url):
        print("Fetching: %s" % page_url)
        class_page = urlopen("%s/%s" % (self.docs_url, page_url))
        if class_page:
            property_types = []
            soup = BeautifulSoup(class_page)
            try:
                properties_list = soup.dl.contents
            except:
                print("No docs for page %s" % page_url)
                return None

            # Break the docs up into sections by property
            sections = []
            section = []
            for item in properties_list:
                if item.name == 'dt':
                    if len(section) > 0:
                        sections.append(section)
                    section = []

                section.append(item)

            # Create a dictionary for each property type
            for s in sections:
                property_dict = {
                    'name': s[0].getText(),
                    'list': False,
                    'href': None
                }
                dds = s[1:]
                for dd in dds:
                    ps = dd.findAll('p')
                    for p in ps:
                        textContents = p.getText()
                        if "Type:" in textContents:
                            cleanText = re.sub(' +', ' ', textContents)\
                                    .replace('Type:', '')\
                                    .replace('.', '')\
                                    .replace('\n', '').strip()
                            if 'list of' in cleanText.lower():
                                property_dict['list'] = True
                                cleanText = cleanText.lower()\
                                        .replace('a list of', '')\
                                        .replace('list of', '').strip().title()
                            if p.a:
                                property_dict['href'] = p.a.get('href')
                            property_dict['type'] = cleanText

                property_types.append(property_dict)
            return property_types

        return None

    def clean_property_map(self, json_string):
        """ Takes an invalid "JSON" string (retrieved from the get_property_list
        function) and creates dictionary from it.
        Returns a dictionary representing the clean json_string """

        lines = json_string.split("\n")

        # Throw away the lines that arne't properties
        property_lines = [l.strip() for l in lines \
                if ':' in l \
                and '::' not in l \
                and 'Properties' not in l]

        # Create a dict of the properties
        property_map = {}
        for l in property_lines:
            properties = l.split(':')
            key = properties[0].replace('"', '').strip()
            value = properties[1].replace(',', '').strip()

            # Identify property types
            if 'JSON' in value:
                property_map[key] = "Object"
            elif '{' in value and ('String' in value or 'Ref' in value):
                property_map[key] = "Ref"
            elif '}' in value:
                clean_value = value.replace('.', '').replace('{', '').replace('}', '').strip()
                property_map[key] = 'ResourceProperty("%s")' % clean_value
            elif ']' in value:
                clean_value = value.replace('.', '').replace('[', '').replace(']', '').strip()
                property_map[key] = 'Array("%s")' % clean_value
            elif 'Integer' in value or 'Number' in value:
                property_map[key] = "Number"
            else:
                property_map[key] = value

        return property_map
