import chromadb
from lib import pyMeSHsearch
import asyncio
import xml.etree.ElementTree as ET

def search():
    pass
async def main():
    # await pyMeSHsearch.find_mesh()
    papers = await pyMeSHsearch.lit_search('''"Carcinoma, Renal Cell"[MeSH]''')
    literature = await asyncio.gather(*(pyMeSHsearch.find_paper(id) for id in papers["esearchresult"]["idlist"]))
    filtered_literature = []
    filtered_ids = []
    
    for count, item in enumerate(literature):
        if '[Error] : No result can be found.' not in item:
            filtered_literature.append(item)
            filtered_ids.append(papers["esearchresult"]["idlist"][count])
    # literature = [item for item in literature if '[Error] : No result can be found.' not in item]

    documents = []
    for paper in filtered_literature:
        print(paper)
        root = ET.fromstring(paper)
        text = '\n'.join([elem.text for elem in root.iter('text')])
        documents.append(text)
        # documents += [elem.text for elem in root.iter('text')]

    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection(name="temp_query_db")

    collection.add(
        documents=documents,
        ids=filtered_ids
    )

    results = collection.query(
        query_texts=["What is the cause of renal cell carcinoma"], # Chroma will embed this for you
        n_results=len(filtered_ids) # how many results to return
    )
    print(results["distances"])
    print(results["ids"])
    print(len(literature))

asyncio.run(main())