import xml.etree.ElementTree as ET

def extract_text(xml_string):
    root = ET.fromstring(xml_string)
    text = '\n'.join([elem.text for elem in root.iter('text')])
    return text

# I ripped this from chatGPT
def get_paper_info(xml_string):
    root = ET.fromstring(xml_string)

    papers = []

    for document in root.findall(".//document"):
        paper_data = {}

        # Extract Paper ID
        id_element = document.find("id")
        if id_element is not None:
            paper_data["ID"] = id_element.text

        # Extract DOI
        doi_element = document.find('.//infon[@key="article-id_doi"]')
        if doi_element is not None:
            paper_data["DOI"] = doi_element.text

        # Extract Authors
        authors_element = document.find('.//passage/infon[@key="name_0"]')
        if authors_element is not None:
            paper_data["First author"] = authors_element.text

        papers.append(paper_data)

    return papers