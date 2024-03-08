import _tkinter as tk
from _tkinter import scrolledtext
import Retriever

class SearchApp:
    def __init__(self, retriever):
        self.retriever = retriever
        self.window = tk.Tk()
        self.window.title("Simple Search Engine")

        self.query_label = tk.Label(self.window, text="Enter your query:")
        self.query_label.pack()

        self.query_entry = tk.Entry(self.window, width=50)
        self.query_entry.pack()

        self.search_button = tk.Button(self.window, text="Search", command=self.search)
        self.search_button.pack()

        self.results_text = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, width=80, height=20)
        self.results_text.pack()

    def search(self):
        query = self.query_entry.get().lower().split()
        if not query:
            return
        results = self.retriever.search_query(query)
        self.display_results(results)

    def display_results(self, results):
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Number of results found: {len(results)}\n\n")
        for link in results[:20]:
            url = self.retriever.bookkeeping_file.get(link.link, "URL not found")
            self.results_text.insert(tk.END, f"{url}\n\n")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    retriever = Retriever.Retriever("/Users/z/Library/Mobile Documents/com~apple~CloudDocs/compsci_121/cs121-Project3/inverted_index_2gram.json")
    app = SearchApp(retriever)
    app.run()
