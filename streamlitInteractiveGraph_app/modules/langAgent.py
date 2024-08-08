from langchain.chat_models.openai import ChatOpenAI

from langchain.prompts.prompt import PromptTemplate

from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain.agents import AgentType, initialize_agent

from langchain.chains import LLMChain, RetrievalQA
from langchain_community.tools import YouTubeSearchTool, Tool
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.neo4j_vector import Neo4jVector

from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph

import os

from modules.initialPrompts import SYSTEM_MESSAGE, CYPHER_GENERATION_TEMPLATE

class consumerAgentDAO:

    def __init__(self, verbose: bool = True):
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model="gpt-4-1106-preview",
            temperature=0
        )

        #EMBEDDING
        embedding_provider = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

        #GRAPH
        graph = Neo4jGraph(
            url=os.getenv("AURA_URI"),
            username=os.getenv("AURA_USER"),
            password=os.getenv("AURA_PASSWORD"),
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
            verbose=True,
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
            agent_kwargs={"system_message": SYSTEM_MESSAGE}
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
    
# from dotenv import load_dotenv
# load_dotenv()
# oh = consumerAgentDAO()