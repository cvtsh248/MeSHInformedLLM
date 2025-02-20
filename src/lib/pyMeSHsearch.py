import asyncio
from lib import requestwrap
import xml.etree.ElementTree as ET

async def find_mesh(phrases: list[str]) -> list[dict]:

    '''
    Find exact mesh terms that match that of what is in the descriptor
    '''

    # label builder
    labels = [item.replace(' ','%20') for item in phrases]

    results = await asyncio.gather(*(requestwrap.get("https://id.nlm.nih.gov/mesh/lookup/descriptor?label="+label+"&match=contains&year=current&limit=30", headers={"accept":"application/json"}) for label in labels))
    results = [result.json() for result in results]
    return results

async def lit_search(query: str) -> dict:
    result = await requestwrap.get('''https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term='''+query+'''&retmode=json&retmax=30''', headers={"accept":"application/json"})
    return result.json()

async def find_paper(id: int) -> dict:
    # result = await requestwrap.get("https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/17299597/unicode", headers={"accept":"application/json"})
    result = await requestwrap.get("https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC"+str(id)+"/unicode",headers={"accept": "application/xml, text/xml;q=0.9, */*;q=0.8"})
    return result.text

# async def main():
#     # out = await find_mesh(["Carcinoma Renal", "Antibiotic"])
#     # print(out[0][0]['label'])
#     papers = await lit_search('''"Carcinoma, Renal Cell"[MeSH]''')
#     print(papers["esearchresult"]["idlist"])

#     out = await find_paper(papers["esearchresult"]["idlist"][1])
#     root = ET.fromstring(out)
#     texts = [elem.text for elem in root.iter('text')]
#     print(texts)

# asyncio.run(main())
