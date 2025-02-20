import asyncio
from lib import requestwrap
import re
import xml.etree.ElementTree as ET
from chromadb.utils import embedding_functions
from chromadb.utils import distance_functions

async def find_MeSH(phrases: list[str]) -> list[dict]:

    '''
    Find exact mesh terms that match that of what is in the descriptor
    '''

    # label builder
    labels = [item.replace(' ','%20') for item in phrases]

    # Batch search, idk why i dind't implement this elsewhere
    results = await asyncio.gather(*(requestwrap.get("https://id.nlm.nih.gov/mesh/lookup/descriptor?label="+label+"&match=contains&year=current&limit=30", headers={"accept":"application/json"}) for label in labels))
    results = [result.json() for result in results]
    return results

async def lit_search(query: str) -> dict:
    
    '''
    Function to use a mesh query to search for literature
    Sadly we're limited by open access papers... 
    '''

    result = await requestwrap.get('''https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term='''+query+'''&retmode=json&retmax=30''', headers={"accept":"application/json"})
    return result.json()

async def find_paper(id: int) -> dict:
    result = await requestwrap.get("https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC"+str(id)+"/unicode",headers={"accept": "application/xml, text/xml;q=0.9, */*;q=0.8"})
    return result.text

async def MeSH_refiner(query: str) -> tuple[int, str]:
    
    '''
    Returns a response to the LLM after checking its' output if it needs to regenerate it. In this situation, a tuple with 1 in index 0 will be returned.
    If the query does not need to be regenerated, a tuple with 0 in index 0 will be returned, along with the modified query
    If the query does not need to be modified, a tuple with 2 in index 0 will be returned, along with "" in index position 2
    '''

    keyword_chars = "QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm,1234567890"
    keywords = re.findall(r'"([^"]*)"', query)
    mesh = re.findall(r"\[([^\]]*)\]", query)

    for i in mesh:
        if i != "Mesh" or i != "MeSH":
            return (1,"Please regenerate the query. You are missing the [MeSH] in your query")
        
    if len(mesh) == 0:
        return (1,"Please regenerate the query. You are missing the [MeSH] in your query")
    
    refined_query = query
    refined_query.replace("Mesh", "MeSH")

    # Check if the keywords the llama is thinking of exist
    confirmed_keywords = await find_MeSH(keywords)

    confirmed_keywords = [keyword['label'] for keyword in confirmed_keywords[0]]

    for keyword in keywords:
        if keyword in confirmed_keywords:
            return (0,"") 

    # Find the closest real keywords to hallucinated keywords using cosine similarity
    vectorised_keywords = embedding_functions.DefaultEmbeddingFunction(keywords)

    vectorised_confirmed_keywords = embedding_functions.DefaultEmbeddingFunction(confirmed_keywords)
    
    distances: list[list] = []
    for i in vectorised_keywords:
        buffer = []
        for j in vectorised_confirmed_keywords:
            buffer.append(distance_functions.cosine(i, j))
        distances.append(buffer)

    corrected_keywords = []
    for dist in distances:
        selected_corrected_keyword = confirmed_keywords[dist.index(min(dist))]
        corrected_keywords.append(selected_corrected_keyword)
    
    for count, keyword in corrected_keywords:
        refined_query.replace(keywords[count], corrected_keywords)
