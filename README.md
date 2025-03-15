# SOPHIA AI
Our submission for NUS Health Hack. SOPHIA AI is a local LLM (llama3.2b) based solution that answers medical queries based on papers fetched from the PubMed PMC API. The main selling point of the product is privacy. The fact that since LLM is local, no sensitive patient info will ever leave the laptop. 

The flow of the solution is as such:
1. A medical query is entered
2. Several MeSH (Medical Subheadings) queries are generated by the LLM (this will enable us to search the PubMed PMC database for relevant papers)
3. A parser, based on traditional heuristic algorithm checks to see if the MeSH query is valid. It also attempts to fix minor formatting issues. The parser also checks all the MeSH keywords against the MeSH headings API to make sure they exist. If they don't and they are hallucinations, the parser will replace them with the closest MeSH keywords based on cosine similarity.
4. The PubMed PMC API is queried with the refined query, and up to 30 papers are returned.
5. The top 4 most relevant papers will then be selected with cosine similarity to the original question.
6. The LLM will generate an answer based on the papers pulled

# Python Dependencies
* requests
* httpx
* asyncio
* chromadb
* bioc
* ollama
* httpx-retries
* ttkbootstrap
* async-tkinter-loop
* ollama

# Running the program
Ensure you have Ollama running in the background, with llama3.2 3b installed.

After initialising a virtual environment run the following to install dependencies:

```python3 -m pip install -r requirements.txt```

Run the GUI via:

```python3 src/gui.py```

Alternatively you can run an interactive terminal version that allows you to chat with the LLM after it has generated your answer (feature will be added to GUI later):
```python3 src/interactive.py```