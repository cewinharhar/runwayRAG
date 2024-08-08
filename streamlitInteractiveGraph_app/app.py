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

    if prompt := st.text_input("Your question"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Thinking..."):
            try:
                #TODO include language respond AND nodes
                response = agentDAO.generate_response(prompt) #TODO add generate_response function for agentDAO
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error("Failed to generate response.")
                st.stop()

    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if "graph_query" not in st.session_state:
        st.session_state.graph_query = ""

    #graph_query = st.text_area("Write a Cypher query to visualize the graph", value=st.session_state.graph_query)

    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking..."):

                    response, graph_data = st.session_state.agentDAO.generate_response(prompt)
                    #TODO CHECK IF ANSWER RETURNES GRAPH DATA, IF YES GENERATE NEW GRAPH, IF NO DO NOT 
                    if graph_data:
                        try:
                            nodes = []
                            edges = []
                            for node in graph_data['nodes']:
                                nodes.append(Node(id=node['id'], label=node['label']))
                            for edge in graph_data['links']:
                                edges.append(Edge(source=edge['source'], target=edge['target'], label=edge['label']))

                            config = Config(height=600, width=800, nodeHighlightBehavior=True, highlightColor="#F7A7A6", directed=True, collapsible=True)
                            agraph(nodes=nodes, edges=edges, config=config)
                        except Exception as e:
                            st.error("Failed to execute graph query.")                    

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
