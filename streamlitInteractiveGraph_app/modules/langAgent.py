from langchain_openai import ChatOpenAI

from langchain.prompts.prompt import PromptTemplate

from langchain.chains.conversation.memory import ConversationBufferMemory
# from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain.agents import AgentType, initialize_agent

# from langchain.chains import LLMChain, RetrievalQA
from langchain_community.tools import YouTubeSearchTool, Tool
from langchain_community.embeddings import OpenAIEmbeddings
# from langchain.vectorstores.neo4j_vector import Neo4jVector

from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph

import os
import pandas as pd
from modules.initialPrompts import SYSTEM_MESSAGE, CYPHER_GENERATION_TEMPLATE

class consumerAgentDAO:

    def __init__(self, verbose: bool = True):
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model="gpt-4o",
            temperature=0
        )

        #EMBEDDING
        embedding_provider = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

        #GRAPH
        graph = Neo4jGraph(
            url=os.getenv("AURA_URI"),
            username=os.getenv("AURA_USER"),
            password=os.getenv("AURA_PASSWORD"),
            enhanced_schema=True
        )         
        #MEMORy
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        #--- TOOLS
        youtube = YouTubeSearchTool()

        #neo4jvector = Neo4jVector.from_existing_index(
        #    embedding_provider,                              # (1)
        #    url=os.getenv("NEO4J_DT_AURA_URI"),
        #    username=os.getenv("NEO4J_DT_AURA_USERNAME"),
        #    password=os.getenv("NEO4J_DT_AURA_PASSWORD"),
        #    index_name="index_diseaseDescription",                 # (5)
        #    # node_label="Disease",                      # (6)
        #    text_node_property="description",               # (7)
        #    embedding_node_property="embedding_description" # (8)
        #)

        #retriever = neo4jvector.as_retriever()

        #self.kg_qa = RetrievalQA.from_chain_type(
        #    llm         =llm,
        #    chain_type  ="stuff",
        #    retriever   =retriever,
        #)

        #------------------------------------------------------
        # CYPHER QUERY SEARCH   
        #------------------------------------------------------
        self.cypher_generation_prompt = PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)

        self.cypher_chain = GraphCypherQAChain.from_llm(
            llm,
            graph=graph,
            cypher_prompt=self.cypher_generation_prompt,
            # output_parser=SimpleJsonOutputParser(),
            verbose=False,
            return_intermediate_steps=True,
            return_direct=True
        )  


        self.tools = [
            # Tool.from_function(
            #     name="ChatOpenAI",
            #     description="For when you need to chat about general topics like health, action points, lifestyle. The question will be a string. Return a string.",
            #     func=chat_chain.run,
            #     return_direct=True
            # ),
            # ,
            #Tool.from_function(
            #    name="YouTubeSearchTool",
            #    description="For when you need a link to a certain topic or startup video. The question will be a string. Return a link to a YouTube video.",
            #    func=youtube.run,
            #    return_direct=True
            #),
            #Tool.from_function(
            #    name="Vector Search Index",
            #    description="Provides information about diseases using Vector search",
            #    func=self.kg_qa,
            #),
            Tool.from_function(
                name="Graph Cypher QA Chain",
                description="Provides information about the the startups, their relationship and properties.",
                func=self.cypher_chain,
            )
        ]

        self.agent = initialize_agent(
            self.tools, llm, memory=self.memory,
            verbose=verbose,
            handle_parsing_errors=True,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            agent_kwargs={"system_message": SYSTEM_MESSAGE},
            return_intermediate_steps=True
        )        

    def kg_qa_fun(self, query: str):
        results = self.retrievalQA(query)
        return str(results)
    
    def generate_response(self, prompt):
        """
        Create a handler that calls the Conversational agent
        and returns a response to be rendered in the UI
        """

        response = self.agent(prompt)

        return response['output']
    
    def genRes(self, prompt):
        """
        Create a handler that calls the Conversational agent
        and returns a response to be rendered in the UI
        """
        res = self.agent(prompt)

        # Get the text responds
        textRes = res["output"]

        #Get graph data
        graphRes = res["intermediate_steps"][0][1]["result"]

        nodes = {}
        links = []
                
        for record in graphRes:
            s1 = record.get('s1')
            s2 = record.get('s2')
            r = record.get('r')
            
            if s1.get('title') not in nodes:
                nodes[s1.get('title')] = {
                    'id': s1.get('title'),
                    'title': s1.get('title'),
                    'subtitle': s1.get('subtitle'),
                    'description': s1.get('description'),
                    'incorporation': s1.get('incorporation'),
                    'headquarters': s1.get('headquarters'),
                    'sectors': s1.get('sectors'),
                    'social_links': s1.get('social_links'),
                    'awards': s1.get('awards'),
                    'url': s1.get('url')
                }
            
            if s2.get('title') not in nodes:
                nodes[s2.get('title')] = {
                    'id': s2.get('title'),
                    'title': s2.get('title'),
                    'subtitle': s2.get('subtitle'),
                    'description': s2.get('description'),
                    'incorporation': s2.get('incorporation'),
                    'headquarters': s2.get('headquarters'),
                    'sectors': s2.get('sectors'),
                    'social_links': s2.get('social_links'),
                    'awards': s2.get('awards'),
                    'url': s2.get('url')
                }
            
            links.append({
                'source': s1['title'],
                'target': s2['title'],
                'label': 'SIMILAR'
            })
        
        nodes_list = list(nodes.values())
        nodes_df = pd.DataFrame(nodes_list)    

        graph_data =  {'nodes': nodes_list, 'links': links}        

        return textRes, graph_data, nodes_df

    
# from dotenv import load_dotenv
# load_dotenv()
# oh = consumerAgentDAO()

# if __name__ == "__main__":
    # from dotenv import load_dotenv
    # load_dotenv("streamlitInteractiveGraph_app\.env")

    # llm = ChatOpenAI(
    #     openai_api_key=os.getenv("OPENAI_API_KEY"),
    #     model="gpt-4o",
    #     temperature=0
    # )

#     #GRAPH
#     graph = Neo4jGraph(
#         url=os.getenv("AURA_URI"),
#         username=os.getenv("AURA_USER"),
#         password=os.getenv("AURA_PASSWORD"),
#         enhanced_schema=True
#     )       

#     cypher_generation_prompt = PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)

#     cypher_chain = GraphCypherQAChain.from_llm(
#         llm,
#         graph=graph,
#         cypher_prompt=cypher_generation_prompt,
#         # output_parser=SimpleJsonOutputParser(),
#         verbose=True,
#         return_intermediate_steps=True,
#         return_direct=True
#     )  

#     result = cypher_chain.invoke({"query": "Which startups are similar to beekeeper AG?"})

#     results = result["result"]

#     nodes = {}
#     links = []
            
#     for record in results:
#         s1 = record.get('s1')
#         s2 = record.get('s2')
#         r = record.get('r')
        
#         if s1['title'] not in nodes:
#             nodes[s1['title']] = {
#                 'id': s1['title'],
#                 'label': s1['title'],
#                 'properties': {
#                     'subtitle': s1['subtitle'],
#                     'description': s1['description'],
#                     'incorporation': s1['incorporation'],
#                     'headquarters': s1['headquarters'],
#                     'sectors': s1['sectors'],
#                     'social_links': s1['social_links'],
#                     'awards': s1['awards'],
#                     'url': s1['url']
#                 }
#             }
        
#         if s2['title'] not in nodes:
#             nodes[s2['title']] = {
#                 'id': s2['title'],
#                 'label': s2['title'],
#                 'properties': {
#                     'subtitle': s2['subtitle'],
#                     'description': s2['description'],
#                     'incorporation': s2['incorporation'],
#                     'headquarters': s2['headquarters'],
#                     'sectors': s2['sectors'],
#                     'social_links': s2['social_links'],
#                     'awards': s2['awards'],
#                     'url': s2['url']
#                 }
#             }
        
#         links.append({
#             'source': s1['title'],
#             'target': s2['title'],
#             'label': 'SIMILAR'
#         })
    
#     returnFile =  {'nodes': list(nodes.values()), 'links': links}




    
#     print(res["query"])
#     print(res["result"])
#     print(res["intermediate_steps"])

#     len(res["result"])

#     res["result"][0]
#     len(res["result"][4])

#     res["result"].keys()
#     res["result"][0].keys()
#     res["result"][0]["s2"].keys()

    # agent = consumerAgentDAO(verbose=True)

    # resp = agent.genRes("Which startups are similar to beekeeper AG?")

    # resp[2]

#     resp = agent.genRes("Which startups are similar to Komed Health AG?")

#     resp.keys()

#     resp["intermediate_steps"]
#     resp["intermediate_steps"][0][1]["result"][0].keys()
#     results = resp["intermediate_steps"][0][1]["result"]