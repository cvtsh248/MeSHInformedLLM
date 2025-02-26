import asyncio
from lib import genAIhandler

chat_history = []
references = ""

user_input = input("Please enter your query: ")
print("Please wait a moment. Generating MeSH queries and Searching MeSH databases for answers to your query. May take up to 2 minutes.")
result = asyncio.run(genAIhandler.generate_MeSH_response(user_input))
chat_history.append(result["response"])

references = "\n".join(result["papers"])
print("Answer: \n------------------------\n")
print(result["response"])
print("Sources: \n------------------------\n")
for source in result["sources"]:
    print("DOI: "+source["DOI"])
    print("Authors: "+source["First author"].split("surname:")[1].split(";")[0]+" et al.")
print(result["sources"])

while True:
    user_input = input(">>> ")
    result = asyncio.run(genAIhandler.general_chat(user_input, "\n".join(chat_history), references))
    print(result["response"])
    chat_history.append(result["response"])
    chat_history.append(result["input"])
    

