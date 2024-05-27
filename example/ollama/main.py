# Example based on https://ollama.com/blog/embedding-models
# using objectbox as a vector store

import ollama
from objectbox import *

documents = [
  "Llamas are members of the camelid family meaning they're pretty closely related to vicuñas and camels",
  "Llamas were first domesticated and used as pack animals 4,000 to 5,000 years ago in the Peruvian highlands",
  "Llamas can grow as much as 6 feet tall though the average llama between 5 feet 6 inches and 5 feet 9 inches tall",
  "Llamas weigh between 280 and 450 pounds and can carry 25 to 30 percent of their body weight",
  "Llamas are vegetarians and have very efficient digestive systems",
  "Llamas live to be about 20 years old, though some only live for 15 years and others live to be 30 years old",
]

# Have fresh data for each start
Store.remove_db_files("objectbox")

@Entity()
class DocumentEmbedding:
    id = Id()
    document = String()
    embedding = Float32Vector(index=HnswIndex(
        dimensions=1024,
        distance_type=VectorDistanceType.COSINE
    ))

store = Store()
box = store.box(DocumentEmbedding)

print("Documents to embed: ", len(documents))

# store each document in a vector embedding database
for i, d in enumerate(documents):
  response = ollama.embeddings(model="mxbai-embed-large", prompt=d)
  embedding = response["embedding"]

  box.put(DocumentEmbedding(document=d,embedding=embedding))
  print(f"Document {i + 1} embedded")
 
# an example prompt
prompt = "What animals are llamas related to?"

# generate an embedding for the prompt and retrieve the most relevant doc
response = ollama.embeddings(
  prompt=prompt,
  model="mxbai-embed-large"
)

query = box.query(
    DocumentEmbedding.embedding.nearest_neighbor(response["embedding"], 1)
).build()

results = query.find_with_scores()
data = results[0][0].document 

print(f"Data most relevant to \"{prompt}\" : {data}")

print("Generating the response now...")

# generate a response combining the prompt and data we retrieved in step 2
output = ollama.generate(
  model="llama3",
  prompt=f"Using this data: {data}. Respond to this prompt: {prompt}"
)

print(output['response'])
