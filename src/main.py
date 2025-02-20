import chromadb
from lib import pyMeSHsearch
import asyncio
import xml.etree.ElementTree as ET
import ollama

async def main():

    question = "What are some of the most effective medications in treating pneumococcal infections?"
    MeSHgen_prompt = '''Consider the following question: '''+question+'''. Do not answer the question. Instead, output a three MeSH queries that you think would yield the most relevant papers. The MeSH query should follow the NIH standard. The NIH standard involves the following rules. Firstly, queries are formatted as such: "Carcinoma, Renal Cell" [MeSH] AND "Cause of" [MeSH]. Note that quotes must be put around the MeSH term. In addition, take note of the case of the letters. Also, realise that between a MeSH term and [MeSH], there must be no brackets. Note that between quotes, a single MeSH keyword should be used. Finally, only return the MeSH query. Do not return any other messages.'''
    initial_query = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": MeSHgen_prompt}], stream=True) # Seems to be performing better than deepseek's distilled models
    # await pyMeSHsearch.find_MeSH()

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