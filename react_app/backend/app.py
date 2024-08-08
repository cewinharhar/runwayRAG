from langchain import ChatOpenAI
from neo4j import GraphDatabase
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize LangChain and Neo4j
langchain_api_key = ''
chat_model = ChatOpenAI(api_key=langchain_api_key)

neo4j_uri = ''
neo4j_user = 'neo4j'
neo4j_password = ''
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

app = Flask(__name__)
CORS(app)  # Enable CORS

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('input')x§
    response = chat_model.chat(user_input)
    graph_data = query_knowledge_graph(user_input)
    return jsonify({'response': response, 'graphData': graph_data})

def query_knowledge_graph(user_input):
    with driver.session() as session:
        result = session.run("""
            MATCH (n)-[r]->(m)
            WHERE n.name CONTAINS $input OR m.name CONTAINS $input
            RETURN n, r, m
        """, input=user_input)
        nodes = set()
        links = []
        for record in result:
            n = record['n']
            m = record['m']
            r = record['r']
            nodes.add((n.id, n['name']))
            nodes.add((m.id, m['name']))
            links.append({'source': n.id, 'target': m.id, 'label': r.type})
        nodes = [{'id': node_id, 'label': name} for node_id, name in nodes]
        return {'nodes': nodes, 'links': links}

if __name__ == '__main__':
    app.run(debug=True)
