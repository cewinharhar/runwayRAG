import streamlit as st
from dotenv import load_dotenv
from modules.initialPrompts import GREETING 
from modules.langAgent import consumerAgentDAO
import logging
from time import sleep

from streamlit_agraph import agraph, TripleStore, Config, Node, Edge


def main():
    st.set_page_config(page_title="Swiss Startup Assistant", page_icon="🚀", layout="centered", initial_sidebar_state="auto")
    st.title("Ask questions about Swiss startups. If they are on the ventureLab website I know about them 💬")
    st.info("More [info](https://runway-incubator.ch/)", icon="📃")

    load_dotenv()

    def load_agent():
        st.session_state.agentDAO = consumerAgentDAO(verbose=True)
        return True

    if 'agentDAO' not in st.session_state:
        try:
            with st.spinner(text="Waking up VC partners... hang tight! This should take a few seconds."):
                load_agent()
                st.success("Agent locked and loaded")
        except Exception as err:
            st.error("Failed to load agent 😔. Did you start the neo4j graph?")
            st.stop()

    agentDAO = st.session_state.agentDAO

    if "messages" not in st.session_state.keys(): 
        st.session_state.messages = [{"role": "assistant", "content": GREETING}]    

    #setting graph data to false
    graph_data = False
    if prompt := st.text_input("Your question"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Thinking..."):
            try:
                #TODO include language respond AND nodes
                response, graph_data = st.session_state.agentDAO.genRes(prompt)
                if graph_data:
                    st.warning('graphdata was collected', icon="⚠️")                
                # response = agentDAO.generate_response(prompt) #TODO add generate_response function for agentDAO
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error("Failed to generate response.")
                st.stop()

    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # if "graph_query" not in st.session_state:
    #     st.session_state.graph_query = ""

    #graph_query = st.text_area("Write a Cypher query to visualize the graph", value=st.session_state.graph_query)

    #TODO CHECK IF ANSWER RETURNES GRAPH DATA, IF YES GENERATE NEW GRAPH, IF NO DO NOT 
    if graph_data:
        print("entering graph generation part")

        # graph_data = agentDAO.query_graph(graph_data)
        nodes = [Node(id=n['id'], label=n['label'], **n['properties']) for n in graph_data['nodes']]
        edges = [Edge(source=e['source'], target=e['target'], label=e['label']) for e in graph_data['links']]

        config = Config(height=1000, width=1000, nodeHighlightBehavior=True, highlightColor="#F7A7A6", directed=True, collapsible=True)
        return_value = agraph(nodes=nodes, edges=edges, config=config)
            

    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking..."):                 

                    # Placeholder for streaming the response
                    response_placeholder = st.empty()

                    # Initialize an empty string to accumulate the response
                    current_text = ""

                    # Split the response into words and stream them #TODO improve styling in the responses
                    for word in response.split():
                        current_text += word + ' '
                        response_placeholder.markdown(current_text)  # Using markdown for consistent styling
                        sleep(0.1)  # Adjust the sleep time to control the speed of streaming

                    # Add the full response to the message history after streaming
                    message = {"role": "assistant", "content": response}
                    st.session_state.messages.append(message)

            except Exception as e:
                logging.error(f"Error generating response: {e}")
                st.error("Failed to generate response.")    


if __name__ == "__main__":
    main()
