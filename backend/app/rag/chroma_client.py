import chromadb

client = chromadb.Client(
    settings=chromadb.config.Settings(
        presistent_history = './chroma_db'
    )
)

collection = client.get_or_create_collection("arch_docs")   
