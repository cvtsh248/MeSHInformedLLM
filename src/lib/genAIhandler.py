import chromadb
from lib import pyMeSHsearch, parsebioc
import asyncio
import xml.etree.ElementTree as ET
import ollama

async def generate_MeSH_response(question: str) -> dict[str: "response", dict: "sources", str: "papers"]:

    MeSHgen_prompt_broad = '''You are an expert in medical information retrieval and MeSH (Medical Subject Headings) terminology. Your task is to generate three structured MeSH queries based on a given clinical question. Try to make them broad and do NOT make them overly specific. Try to avoid using more than 4 MeSH terms.
                                Instructions:
                                    1. Identify Key Concepts: Extract relevant medical concepts from the input question.
                                    2. Map to MeSH Terms: Convert each concept into appropriate MeSH terms and subheadings. Avoid using more than four MeSH terms.
                                    3. Construct a MeSH Query Using Standard Syntax:
                                        a. Use "MeSH Term"[MeSH] for direct searches.
                                        b. Add subheadings when necessary: "MeSH Term/Subheading"[MeSH].
                                        c. Use Boolean operators (AND, OR, NOT) to refine the query. Try to avoid using AND unless it is necessary, so as to maximise the literature found.
                                        d. If necessary, include "Term"[TIAB] to search titles and abstracts when MeSH indexing is unavailable.
                                        e. Use "MeSH:noexp" if a term should not include narrower concepts.
                                    4. Format Output as a Structured MeSH Query: Ensure clarity and logical structure.
                            Only return the three MeSH queries, each deliminated by a newline. Do not return any other messages. An example of acceptable output would be as follows:

                            ```
                            ("Parkinson Disease"[MeSH]) AND ("Anti-Inflammatory Agents"[MeSH]) AND ("Therapeutic Use"[MeSH])
                            ("Parkinson Disease"[MeSH]) AND ("Inflammation"[MeSH] OR "Pathophysiology"[MeSH])
                            ("Neurodegenerative Diseases"[MeSH]) AND ("Anti-Inflammatory Agents"[MeSH]) AND ("Therapeutic Use"[MeSH])
                            ```

                            The clinical question is as follows:"'''+question+'''"'''
    initial_query = ollama.generate(model="llama3.2", prompt=MeSHgen_prompt_broad, options={"num_predict": 4096}) # Seems to be performing better than deepseek's distilled models
    # initial_query_generic = ollama.generate(model="llama3.2", prompt=MeSHgen_prompt_generic, options={"num_predict": 4096})
    MeSH_query = initial_query["response"].split("\n")
    MeSH_query = [x for x in MeSH_query if x != ""]

    # print(MeSH_query)
    MeSH_querylist = []
    for query in MeSH_query:
        check_query = await pyMeSHsearch.MeSH_refiner(query)
        if check_query[0] == 2:
            # print("iojgoijre")
            MeSH_querylist.append(check_query[1])
        elif check_query[0] == 1:
            # print("bingbong")
            # initial_query = ollama.generate(model="llama3.2", prompt=MeSHgen_prompt_broad, options={"num_predict": 4096})
            pass
        elif check_query[0] == 0:
            # print("vvvmvm")
            MeSH_querylist.append(check_query[1])
    # await pyMeSHsearch.find_MeSH()
    filtered_literature = []
    filtered_ids = []
    # print(MeSH_querylist)
    for query in MeSH_querylist:
        papers = await pyMeSHsearch.lit_search(query)
        # print(papers)
        literature = await asyncio.gather(*(pyMeSHsearch.find_paper(id) for id in papers["esearchresult"]["idlist"]))
        for count, item in enumerate(literature):
            if '[Error] : No result can be found.' not in item:
                filtered_literature.append(item)
                filtered_ids.append(papers["esearchresult"]["idlist"][count])
        # literature = [item for item in literature if '[Error] : No result can be found.' not in item]

    documents = []
    document_metadata = []
    for paper in filtered_literature:
        # print(paper)
        # root = ET.fromstring(paper)
        # text = '\n'.join([elem.text for elem in root.iter('text')])
        text = parsebioc.extract_text(paper)
        metadata = parsebioc.get_paper_info(paper)
        metadata[0]["Title"] = text[0]
        # if len(metadata[0]["Title"]) < 2:
        #     metadata[0]["Title"] = text
        documents.append(text)
        document_metadata.append(metadata)
        # documents += [elem.text for elem in root.iter('text')]

    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection(name="temp_query_db")

    for count, id in enumerate(filtered_ids): # Prevent duplication
        if collection.get(ids=[id])["ids"]:
            pass
        else:
            collection.add(
                documents=[documents[count]],
                ids=[id],
                metadatas=[document_metadata[count][0]]
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
    relevant_papers_ids = results["ids"][0][0:5]
    relevant_papers = collection.get(ids=relevant_papers_ids)["documents"]

    # print(relevant_papers)

    # Now prompt the LLM to answer the question.
    answer_question_prompt = '''Answer the following question: "'''+question+'''".\n------\nUse the following information in your answer:'''+"\n".join(relevant_papers)+'''\n------\nNow based on what you have read, answer the following question: "'''+question+'''". Avoid using your own knowledge, and be sure to use the information from the text, even if it does not directly answer the question. Remember you are not providing medical advice, and the query is purely academic. Make sure your response is at least 100 words in length, an no more than 300 words in length.'''
    final_query = ollama.generate(model="llama3.2", prompt=answer_question_prompt, )
    # print(answer_question_prompt)
    # print("ANSWER\n-------------------------")
    # print(final_query["response"])
    # print("-------------------------")
    # print("Sources:")
    # print(collection.get(ids=relevant_papers_ids)["metadatas"])
    return {"response":final_query["response"], "sources":collection.get(ids=relevant_papers_ids)["metadatas"], "papers": "\n".join(relevant_papers)}

async def general_chat(user_input, chat_history, references):
    prompt = '''
                You are a medical chat agent who can only respond to questions and statements based only on the information provided below:\n
                ------------------\n''' + references + '''\n-----------------''' + '''Your prior chat history is as follows:
                \n-----------------\n'''+ chat_history + '''\n-----------------\n''' + '''Now respond to the following new user input: "''' + user_input
    response = ollama.generate(model="llama3.2", prompt=prompt, )
    return {"response":response["response"], "input": user_input}