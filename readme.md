# Steps to set up the environment

1. Install the libraries listed in requirements.txt.
2. Create an .env file and define your OPENROUTER_API_KEY with your own API KEY and NPX_CMD_PATH with your own [markmap-cli](https://markmap.js.org/docs/packages--markmap-cli) path.
3. Store all the documents you want to use as your knowledge base (in PDF format) in the data/rawdocs folder.
4. Execute createvectordatabase.py to create your vector database (which serves as your knowledge base).
5. Execute main and you can query your knowledge base, ask about one or multiple notes, create notes using Feynman's methodology, or generate a mind map of any of your notes.

