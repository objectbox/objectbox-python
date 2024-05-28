# Example: Using ObjectBox with Ollama 

based on https://ollama.com/blog/embedding-models

## Setup

 1. Install ollama. See instructions at https://ollama.com/download

 2. Pull models

        ollama pull llama3
        ollama pull mxbai-embed-large

 3. Change to example directory:

        cd example/ollama

 3. Recommended: Create a new venv

        python3 -m venv .venv
        source .venv/bin/activate

 4. Install Python Bindings and ObjectBox: 

        pip install ollama
        pip install objectbox

    Or: 

        pip install -r requirements.txt


## Run Example
        
```
$ python main.py 

Llamas are members of the camel family, which includes other large, even-toed ungulates such as camels, dromedaries, and Bactrian camels. Llamas are most closely related to alpacas, which are also native to South America and share many similarities in terms of their physical characteristics and behavior. Both llamas and alpacas belong to the family Camelidae, and are classified as ruminants due to their unique digestive system that allows them to break down cellulose in plant material.
```
