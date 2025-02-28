import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from lib import genAIhandler
import asyncio
from async_tkinter_loop import async_handler, async_mainloop

chat_history = []

def get_medical_papers(query):
   
    papers = [
        {
            "title": "The Effects of Medication A on Disease B",
            "authors": "Smith J, Doe A",
            "journal": "Medical Journal",
            "year": "2022",
            "abstract": "Study on Medication A and Disease B..."
        },
        {
            "title": "A Comprehensive Review of Treatment C",
            "authors": "Brown C, Lee D",
            "journal": "Health Science Reviews",
            "year": "2021",
            "abstract": "Review of treatments for condition C..."
        }
    ]
    if not query:
        return []
    return [p for p in papers if query.lower() in p["title"].lower()]

class ScrollableFrame(tb.Frame):
    def __init__(self, container, **kwargs):
        super().__init__(container, **kwargs)
        canvas = tk.Canvas(self, bg="#2E2E2E", highlightthickness=0)
        scrollbar = tb.Scrollbar(self, orient="vertical", command=canvas.yview)

        self.scrollable_frame = tb.Frame(canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

async def search_papers():
    
    references_text.config(state="normal")
    chat_text.config(state="normal")

    results = []
    query = query_entry.get().strip()

    if chat_history == []:
        references_text.delete("1.0", "end")
        chat_text.delete("1.0", "end")
    
        # references_text.config(state="disabled")
        # chat_text.config(state="disabled")

        status_bar.config(text="Searching...")

        
        # results = get_medical_papers(query)
        chat_text.insert("end", "Please wait a moment. Generating MeSH queries and searching MeSH databases for answers to your query. May take up to 2 minutes.")
        print(chat_text.tk)
        # root.update()

        results = await genAIhandler.generate_MeSH_response(query)

        if not results:
            references_text.insert("end", "No references found.\n")
        else:
            references_text.insert("end", "Papers referenced:\n\n")
            chat_text.insert("end", "\n\nResponse based on research:\n")
            chat_history.append("MeSH expert: " + results["response"])
            chat_text.insert("end", results["response"])
            for paper in results['sources']:
                references_text.insert("end", f"• {"DOI: "+paper["DOI"]+", Authors: "+paper["First author"].split("surname:")[1].split(";")[0]+" et al."}\n")

        status_bar.config(text="Search complete.")
    else:
        status_bar.config(text="Thinking...")
        new_result = await genAIhandler.general_chat(query, "\n".join(chat_history), "\n".join(results["papers"]))
        chat_history.append("User: "+query)
        chat_history.append("MeSH expert: "+new_result["response"])
        chat_text.insert("end", new_result["response"])
        status_bar.config(text="Done.")


root = tb.Window(themename="darkly")
root.title("MeSH augmented LLM")
root.geometry("900x700")
root.configure(background="#2E2E2E")

# Header
header_frame = tb.Frame(root, padding=20)
header_frame.pack(side="top", fill="x")

header_label = tb.Label(
    header_frame,
    text="MeSH augmented LLM",
    font=("Helvetica", 18, "bold"),
    bootstyle="info"
)
header_label.pack(anchor="center")

separator = tb.Separator(root, orient="horizontal")
separator.pack(fill="x", padx=20, pady=(0,20))

# Top frame: Search Bar
top_frame = tb.Frame(root, padding=10)
top_frame.pack(side="top", fill="x", padx=20)

query_label = tb.Label(top_frame, text="Query:")
query_label.pack(side="left", padx=(0,10))

query_entry = tb.Entry(top_frame, width=50)
query_entry.pack(side="left", fill="x", expand=True)

search_button = tb.Button(top_frame, text="Submit", command=async_handler(search_papers), bootstyle="primary")
search_button.pack(side="left", padx=(10,0))

# Main Content: Two Columns
content_frame = tb.Frame(root)
content_frame.pack(side="top", fill="both", expand=True, padx=20, pady=10)

content_frame.columnconfigure(0, weight=1)
content_frame.columnconfigure(1, weight=1)
content_frame.rowconfigure(0, weight=1)  

# Left column: Chat response
left_frame = tb.Frame(content_frame)
left_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 10), pady=10)
left_frame.rowconfigure(1, weight=1)

chat_label = tb.Label(
    left_frame,
    text="Response",
    font=("Helvetica", 14, "bold"),
    bootstyle="info"
)
chat_label.pack(anchor="nw", pady=(0,5))

chat_text = tb.Text(
    left_frame,
    wrap="word",
    relief="flat",
    background="#1E1E1E",
    foreground="#FFFFFF",
    insertbackground="#FFFFFF"
)
chat_text.pack(fill="both", expand=True)
chat_text.config(state="disabled")


# A scrollable frame that we do NOT fill
# results_container = ScrollableFrame(left_frame)
# results_container.pack(fill="both", expand=True, padx=(10,0))

# Right column: Papers Referenced
right_frame = tb.Frame(content_frame)
right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 10), pady=10)
right_frame.rowconfigure(1, weight=1)

references_label = tb.Label(
    right_frame,
    text="References",
    font=("Helvetica", 14, "bold"),
    bootstyle="info"
)
references_label.pack(anchor="nw", pady=(0,5))

references_text = tb.Text(
    right_frame,
    wrap="word",
    relief="flat",
    background="#1E1E1E",
    foreground="#FFFFFF",
    insertbackground="#FFFFFF"
)
references_text.pack(fill="both", expand=True)
references_text.config(state="disabled")

# Status Bar
status_bar = tb.Label(root, text="Ready", anchor="w", padding=5)
status_bar.pack(side="bottom", fill="x")

async_mainloop(root)