

import os
import sys
from flask import Flask, request, jsonify, render_template

import openai
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.llms import OpenAI
from langchain.vectorstores import Chroma

import constants

os.environ["OPENAI_API_KEY"] = constants.APIKEY

# Enable to save to disk & reuse the model (for repeated queries on the same data)
PERSIST = False

# Flask app
app = Flask(__name__)

@app.route('/')
def chatbot():
    return render_template('ai_chatbot.html')

# Initialize the ConversationalRetrievalChain
if PERSIST and os.path.exists("persist"):
    print("Reusing index...\n")
    vectorstore = Chroma(persist_directory="persist", embedding_function=OpenAIEmbeddings())
    index = VectorStoreIndexWrapper(vectorstore=vectorstore)
else:
    #loader = TextLoader("data/data.txt") # Use this line if you only need data.txt
    loader = DirectoryLoader("data/")
    if PERSIST:
        index = VectorstoreIndexCreator(vectorstore_kwargs={"persist_directory": "persist"}).from_loaders([loader])
    else:
        index = VectorstoreIndexCreator().from_loaders([loader])

chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model="gpt-3.5-turbo"),
    retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
)

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    query = data.get('query')
    chat_history = data.get('chat_history', [])
    
    if query:
        result = chain({"question": query, "chat_history": chat_history})
        answer = result['answer']
        chat_history.append((query, answer))
        return jsonify({"answer": answer, "chat_history": chat_history})
    else:
        return jsonify({"error": "No query provided"}), 400

if __name__ == '__main__':
    app.run(debug=True)


    #host="0.0.0.0" # Listen for connections _to_ any server
    
