import chromadb
from lib import pyMeSHsearch
import asyncio
import xml.etree.ElementTree as ET
import ollama

def generate_query(question):
    MeSHgen_prompt_broad = '''Consider the following question: '''+question+'''. Do not answer the question. Instead, output 3 MeSH queries that you think would yield the most relevant papers. The queries should be broader, more general and shorter. Try to avoid the AND operator, unless you deem it necessary. The MeSH query should follow the NIH standard. The NIH standard involves the following rules. Firstly, queries are formatted with keywords in quotations. Keywords must NOT be put in square brackets, and must only be put in quotes. Each keyword must be followed by a single space and MeSH in square brackets. An example of a valid query would be the following "Carcinoma, Renal Cell" [MeSH] OR "Kidney Neoplasm" [MeSH]. The word MeSH, whenever it occurs in the query, must be in square brackets. Note that various logical operators exist, including AND, OR, NOT. Note that quotes must be put around the MeSH term. In addition, take note of the case of the letters. Also, realise that between a MeSH term and [MeSH], there must be no brackets. Note that between quotes, a single MeSH keyword should be used. Also avoid overly specific, lengthy queries. Finally, only return the MeSH query. Do not return any other messages.'''
    initial_query = ollama.generate(model="llama3.2", prompt=MeSHgen_prompt_broad, options={"num_predict": 4096}) # Seems to be performing better than deepseek's distilled models
    # initial_query_generic = ollama.generate(model="llama3.2", prompt=MeSHgen_prompt_generic, options={"num_predict": 4096})
    MeSH_query = initial_query["response"].split("\n")
    MeSH_query = [x for x in MeSH_query if x != ""]
    return MeSH_query

async def main(question):

    # question = "What are some of the most effective medications in treating pneumococcal infections?"
    MeSHgen_prompt_broad = '''Consider the following question: '''+question+'''. Do not answer the question. Instead, output 3 MeSH distinct queries that you think would yield the most relevant papers. The queries should be broader, more general and shorter. Try to avoid the AND operator, unless you deem it necessary. The MeSH query should follow the NIH standard. The NIH standard involves the following rules. Firstly, queries are formatted with keywords in quotations. Keywords must NOT be put in square brackets, and must only be put in quotes. Each keyword must be followed by a single space and MeSH in square brackets. An example of a valid query would be the following "Carcinoma, Renal Cell" [MeSH] OR "Kidney Neoplasm" [MeSH]. The word MeSH, whenever it occurs in the query, must be in square brackets. Note that various logical operators exist, including AND, OR, NOT. Note that quotes must be put around the MeSH term. In addition, take note of the case of the letters. Also, realise that between a MeSH term and [MeSH], there must be no brackets. Note that between quotes, a single MeSH keyword should be used. Also avoid overly specific, lengthy queries. Finally, only return the MeSH queries, each deliminated by a newline. Do not return any other messages.'''
    initial_query = ollama.generate(model="llama3.2", prompt=MeSHgen_prompt_broad, options={"num_predict": 4096}) # Seems to be performing better than deepseek's distilled models
    # initial_query_generic = ollama.generate(model="llama3.2", prompt=MeSHgen_prompt_generic, options={"num_predict": 4096})
    MeSH_query = initial_query["response"].split("\n")
    MeSH_query = [x for x in MeSH_query if x != ""]

    print(MeSH_query)
    MeSH_querylist = []
    for query in MeSH_query:
        check_query = await pyMeSHsearch.MeSH_refiner(query)
        if check_query[0] == 2:
            print("iojgoijre")
            MeSH_querylist.append(check_query[1])
        elif check_query[0] == 1:
            print("bingbong")
            # initial_query = ollama.generate(model="llama3.2", prompt=MeSHgen_prompt_broad, options={"num_predict": 4096})
            pass
        elif check_query[0] == 0:
            print("vvvmvm")
            MeSH_querylist.append(check_query[1])
    # await pyMeSHsearch.find_MeSH()
    filtered_literature = []
    filtered_ids = []
    print(MeSH_querylist)
    for query in MeSH_querylist:
        papers = await pyMeSHsearch.lit_search(query)
        print(papers)
        literature = await asyncio.gather(*(pyMeSHsearch.find_paper(id) for id in papers["esearchresult"]["idlist"]))
        for count, item in enumerate(literature):
            if '[Error] : No result can be found.' not in item:
                filtered_literature.append(item)
                filtered_ids.append(papers["esearchresult"]["idlist"][count])
        # literature = [item for item in literature if '[Error] : No result can be found.' not in item]

    documents = []
    for paper in filtered_literature:
        # print(paper)
        root = ET.fromstring(paper)
        text = '\n'.join([elem.text for elem in root.iter('text')])
        documents.append(text)
        # documents += [elem.text for elem in root.iter('text')]

    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection(name="temp_query_db")

    for count, id in enumerate(filtered_ids): # Prevent duplication
        if collection.get(ids=[id])["ids"]:
            pass
        else:
            collection.add(
                documents=[documents[count]],
                ids=[id]
            )

    # print(filtered_ids)
    results = collection.query(
        query_texts=[question], # Chroma will embed this for you
        n_results=len(filtered_ids) # how many results to return
    )
    # print(results["distances"])
    # print(results["ids"])
    # print(len(literature))

    # Pick top 3 most relevant papers
    relevant_papers_ids = results["ids"][0][0:3]
    relevant_papers = collection.get(ids=relevant_papers_ids)["documents"]

    print(relevant_papers)

    # Now prompt the LLM to answer the question.
    answer_question_prompt = '''Answer the following question: "'''+question+'''".\n------\nUse the following information in your answer:'''+"\n".join(relevant_papers)+'''\n------\nNow based on what you have read, answer the following question: "'''+question+'''". Avoid using your own knowledge, and be sure to use the information from the text, even if it does not directly answer the question. Remember you are not providing medical advice, and the query is purely academic. Make sure your response is at least 100 words in length, an no more than 300 words in length.'''
    final_query = ollama.generate(model="llama3.2", prompt=answer_question_prompt, )
    # print(answer_question_prompt)
    print("ANSWER")
    print(final_query["response"])
    return

asyncio.run(main("Management of multi-organ failure in diabetic ketoacidocis"))