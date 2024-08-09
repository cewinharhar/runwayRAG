import csv
import ast
from neo4j import GraphDatabase
import pandas as pd
import numpy as np
import time

from streamlitInteractiveGraph_app.modules.similarity_functions import similarity_embedding_cosine, similarity_sector, similarity_jaccard

def compute_similarity_score(startup1, startup2, weights):
    # Compute individual similarity scores
    text_similarity = similarity_embedding_cosine([startup1['description_embedding']], [startup2['description_embedding']])[0][0]
    sector_similarity = similarity_sector(startup1['sectors'], startup2['sectors'])
    location_similarity = 1 if startup1['headquarters'] == startup2['headquarters'] else 0
    # incorporation_similarity = 1 - abs(startup1['incorporation'] - startup2['incorporation']) / max_year_difference
    social_links_similarity = similarity_jaccard(startup1['social_links'], startup2['social_links'])
    awards_similarity = similarity_jaccard(startup1['awards'], startup2['awards'])
    
    # Combine them using weights
    similarity_score = (weights['text'] * text_similarity +
                        weights['sector'] * sector_similarity +
                        weights['location'] * location_similarity +
                        # weights['incorporation'] * incorporation_similarity +
                        weights['social_links'] * social_links_similarity +
                        weights['awards'] * awards_similarity)
    
    return similarity_score

# Example weights (these can be tuned)
weights = {
    'text': 0.3,
    'sector': 0.2,
    'location': 0.1,
    # 'incorporation': 0.1,
    'social_links': 0.2,
    'awards': 0.1
}


def create_knowledge_graph(csv_path, driver, threshold_percentage = 0.5): #TODO restructure function make more professional
    def get_data_from_csv(csv_path):
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=',')
            data = [row for row in reader]
        return data
    
    @staticmethod
    def _dynamic_tx(tx, query, **kwargs):
        """Use for queries with no dynamic paramters
        """
        assert isinstance(query, str)
        res = tx.run(query, **kwargs)

        return [re for re in res]

    def create_graph(data, driver): 
        with driver.session() as session:
            dataLen = len(data)
            for i, row in enumerate(data):
                print(f"{i}/{dataLen}", end = "\r")
                try:
                    sectors = ast.literal_eval(row['sectors']) if row else ""
                    social_links = ast.literal_eval(row['social_links']) if row and row['social_links'] else ""
                    awards = ast.literal_eval(row['awards']) if row and row['awards'] else ""
                                        
                    # Convert complex types to strings
                    #sectors_str = str(sectors)
                    social_links_str = str(social_links)
                    #awards_str = str(awards)
                    
                    session.run(
                        """
                        MERGE (n:Startup {title: $title})
                        SET n.subtitle = $subtitle, n.description = $description, 
                            n.incorporation = $incorporation, n.headquarters = $headquarters,
                            n.sectors = $sectors, n.social_links = $social_links,
                            n.awards = $awards, n.url = $url
                        """,
                        title=row['title'], subtitle=row['subtitle'], description=row['description'],
                        incorporation=row['incorporation'], headquarters=row['headquarters'],
                        sectors=sectors, social_links=social_links_str, awards=awards, url=row['url']
                    )
                except Exception as err:
                    print(f"problem with {row}")
                    print(f"Error: {err}")
                    time.sleep(10)

            for i, row1 in enumerate(data):
                if not row1 or not ast.literal_eval(row1['sectors']):
                    continue
                sectors1 = ast.literal_eval(row1['sectors'])

                for j, row2 in enumerate(data):
                    print(f"Comparing {i} with {j}     ", end="\r")
                    if i >= j or not row2:
                        continue
                    sectors2 = ast.literal_eval(row2['sectors'])
                    if not sectors2:
                        continue

                    if similarity_sector(sectors1, sectors2, threshold_percentage):
                        query = (
                            """
                            MATCH (a:Startup {title: $title1}), (b:Startup {title: $title2})
                            MERGE (a)-[:SIMILAR]-(b)
                            """
                            )
                        session.execute_write(_dynamic_tx, query=query, title1=row1['title'], title2=row2['title'])

    data = get_data_from_csv(csv_path)
    create_graph(data, driver)


if __name__ == "__main__":

    # Example usage:
    uri = "neo4j+s://5443700b.databases.neo4j.io"
    user = "neo4j"
    password = "iY3025ukPp_wipI18MvSVhUihygL3P_kX_WxppqcDOY"
    csv_path = r"C:\Users\kevin\OneDrive - TrueYouOmics\PERSONAL\_GITHUB\runwayRAG\App\data\ventureLabStartupInfo_clean.csv"
    driver = GraphDatabase.driver(uri, auth=(user, password))
    assert driver.verify_connectivity() is None
    create_knowledge_graph(csv_path, driver, threshold_percentage=0.6)
    driver.close()