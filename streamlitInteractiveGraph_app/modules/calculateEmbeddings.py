import os 
import openai
from openai import OpenAI
from neo4j import GraphDatabase, Result
from neo4j.exceptions import DatabaseError
import pandas as pd
from time import sleep
from dotenv import load_dotenv
import requests
from pandas import DataFrame


def check_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.ConnectionError:
        return False

def quickConnect():
    load_dotenv()

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )
    assert driver.verify_connectivity() is None    
    return driver


def get_embedding(text, model="text-embedding-ada-002", client=None):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding



def addEmbeddingToDf(df: DataFrame, colToEmbed: str = "name", embedColName: str = "embedding", embedModel = 'text-embedding-ada-002', csvPath: str = None):
    # openai.api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI()
    #-------------------------------------------------------------------------------------------------------------------------------
    df[embedColName] = df[colToEmbed].apply(lambda x: get_embedding(x, model=embedModel, client=client))
    #-------------------------------------------------------------------------------------------------------------------------------
    if csvPath:
        df.to_csv(csvPath, index=False)    
    else:
        return df
    
def addPropertyFromCSVToNeo4j(csvUrl: str, nodeType: str, 
                              csvNewPropertyColName: str, neo4jNewPropertyName: str,
                              neo4jNodeMap: str = "id", csvNodeMap: str = "id"):
    """
    Add a new property to nodes in a Neo4j database from a CSV file.

    Parameters:
    - csvUrl (str): URL of the CSV file to load.
    - nodeType (str): Type of the nodes to be updated.
    - csvNodeColName (str): Name of the column in the CSV file that contains node names.
    - csvNewPropertyColName (str): Name of the column containing the new property data.
    - neo4jNewPropertyName (str): Node property name for the new property in Neo4j.

    Returns:
    None

    Raises:
    Exception: If the provided URL is invalid, or if no matching records are found in Neo4j.
    """

    try:
        driver = quickConnect()
        assert check_url(csvUrl), "The provided URL is invalid."

        updatePropertyQuery = f"""
        LOAD CSV WITH HEADERS FROM '{csvUrl}' AS row
        MATCH (d:{nodeType} {{{neo4jNodeMap}: row.{csvNodeMap}}})
        SET d.{neo4jNewPropertyName} = row.{csvNewPropertyColName}
        RETURN count(*)"""

        result = driver.execute_query(updatePropertyQuery, database="neo4j")

        print(f"{neo4jNewPropertyName} property successfully added to \n {result} \n nodes.")

    except AssertionError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.close()

def set_embeddings(df, driver, nodeType, neo4jNodeMap, csvNodeMap, neo4jEmbeddingPropertyName, csvEmbeddingColName):
    # Function to execute the query for each row in the DataFrame
    def add_embedding(tx, row):
        query = f"""
        MATCH (d:{nodeType} {{{neo4jNodeMap}: $node_id}})
        CALL db.create.setNodeVectorProperty(d, '{neo4jEmbeddingPropertyName}', apoc.convert.fromJsonList($embedding))
        RETURN count(*)
        """
        result = tx.run(query, node_id=row[csvNodeMap], embedding=str(row[csvEmbeddingColName]))
        return result.single()[0]

    with driver.session() as session:
        for index, row in df.iterrows():
            count = session.execute_write(add_embedding, row)
            print(f"Processed {count} nodes for row {index}", end="\r")
        print()        

def addEmbeddingsFromCSVToNeo4j(csvUrl: str, nodeType: str, 
                                csvEmbeddingColName: str, neo4jEmbeddingPropertyName: str, 
                                neo4jNodeMap: str = "id", csvNodeMap: str = "id"):
    """
    Add embeddings to nodes in a Neo4j database from a CSV file.

    Parameters:
    - csvUrl (str): URL of the CSV file to load.
    - nodeType (str): Type of the nodes to be updated.
    - csvNodeColName (str): Name of the column in the CSV file that contains node names.
    - csvEmbeddingColName (str): Name of the column containing the embedding data.
    - neo4jEmbeddingPropertyName (str): Node property name for the embedding in Neo4j.

    Returns:
    None

    Raises:
    Exception: If the provided URL is invalid, or if no matching records are found in Neo4j.
    """

    try:
        driver = quickConnect()
        assert check_url(csvUrl), "The provided URL is invalid."

        setEmbeddings = f"""
        LOAD CSV WITH HEADERS FROM '{csvUrl}' AS row
        MATCH (d:{nodeType} {{{neo4jNodeMap}: row.{csvNodeMap}}})
        CALL db.create.setNodeVectorProperty(d, '{neo4jEmbeddingPropertyName}', apoc.convert.fromJsonList(row.{csvEmbeddingColName}))
        RETURN count(*)"""

        result = driver.execute_query(setEmbeddings, database="neo4j")

        print(f"{neo4jEmbeddingPropertyName} embeddings successfully added to {result} nodes.")

    except AssertionError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.close()



def createVectorIndex(indexName: str, label: str, driver = None, propertyKey: str = "embedding", vectorDimension: int = 1536, vectorSimilarityFunction: str = "cosine") -> None:
    """
    Create a vector node index in a Neo4j database.
    
    Args:
    - indexName: The name of the index. Ex: diseasesIndex
    - label: The node label on which to index. Ex: disease
    - propertyKey: The property key on which to index.
    - vectorDimension: The dimension of the embedding (default 1536).
    - vectorSimilarityFunction: The similarity function (euclidean or cosine).

    Returns:
    None. Prints indexing status during the process.
    """
    
    cmd = f"""CALL db.index.vector.createNodeIndex(
        '{indexName}',
        '{label}',
        '{propertyKey}',
        {vectorDimension},
        '{vectorSimilarityFunction}'
    )"""

    try:
        
        if not driver:
            driver = quickConnect()

        createVectorIndexResult = driver.execute_query(cmd, database="neo4j")

        indexingFinished = 0
        while indexingFinished < 100.0:
            indexingFinished = list(checkIndexCreationStatus(driver=driver, indexingName=indexName)["populationPercent"])[0]
            print(f"Indexing status at: {indexingFinished} %", end="\r")

        print("Successfully added the vector index")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.close()    

def checkIndexCreationStatus(driver = None, indexingName: str = None):
    
    if not driver:
        driver = quickConnect()

    def cics():
        return """SHOW INDEXES  YIELD id, name, type, state, populationPercent WHERE type = 'VECTOR'"""
    def cicsWithName(indexingName):
        return f"""SHOW INDEXES  YIELD id, name, type, state, populationPercent WHERE type = 'VECTOR' AND name = '{indexingName}'"""

    if indexingName:
        return driver.execute_query(cicsWithName(indexingName), result_transformer_=Result.to_df)
    else:
        return driver.execute_query(cics(), result_transformer_=Result.to_df)


def dropVectorIndex(indexName: str, driver: GraphDatabase.driver):
 
    try:
        driver.execute_query(f"DROP INDEX `{indexName}`")
        print("Index successfully deleted")
    except DatabaseError: 
        print(f"Vector index {indexName} already deleted or doesnt exist")


def queryVectorIndex_similarEmbedding(nodeType: str, nodeProperty_name: str, indexName: str, numberOfNearestNeighbours: int = 6, nodeProperty_embeddingName: str = "embedding"):
    """Syntax:
    CALL db.index.vector.queryNodes(
    indexName :: STRING,
    numberOfNearestNeighbours :: INTEGER,
    query :: LIST<FLOAT>
    ) YIELD node, score
    """
    driver = quickConnect()

    cmd = f"""MATCH (d:{nodeType} {{name: '{nodeProperty_name}'}})
    CALL db.index.vector.queryNodes('{indexName}', {numberOfNearestNeighbours}, d.{nodeProperty_embeddingName})
    YIELD node, score
    RETURN node.id as id, node.name as name, node.source as source, score"""
    
    res = driver.execute_query(cmd, result_transformer_= Result.to_df)

    return res

def clean_column_names(df: pd.DataFrame, columns: list, chars_to_replace: list, replaceChar: str = " ") -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            for char in chars_to_replace:
                df[col] = df[col].str.replace(char, replaceChar, regex=False)
    return df
 

