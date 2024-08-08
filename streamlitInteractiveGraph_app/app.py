import streamlit as st
from dotenv import load_dotenv
from modules.initialPrompts import GREETING
from modules.langAgent import consumerAgentDAO
import logging
from time import sleep
from streamlit_agraph import agraph, TripleStore, Config, Node, Edge
import pandas as pd
import numpy as np

def main():
    st.set_page_config(page_title="Swiss Startup Assistant", page_icon="🚀", layout="wide", initial_sidebar_state="auto")
    st.title("Swiss Startup Assistant 💬")
    # st.info("More [info](https://runway-incubator.ch/)", icon="📃")

    load_dotenv()

    def load_agent():
        st.session_state.agentDAO = consumerAgentDAO(verbose=True)
        return True

    if 'agentDAO' not in st.session_state:
        try:
            with st.spinner("Waking up VC partners... hang tight! This should take a few seconds."):
                load_agent()
                # st.success("Agent locked and loaded")
        except Exception as err:
            st.error("Failed to load agent 😔. Did you start the neo4j graph?")
            st.stop()

    agentDAO = st.session_state.agentDAO

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": GREETING}]    

    # Main layout
    col1, col2, col3 = st.columns([0.3, 0.4, 0.3])

    with col1:
        print("col 2")
        # st.header("Chat")
        if prompt := st.chat_input("Your question"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("Thinking..."):
                try:
                    response, graph_data, graph_df = agentDAO.genRes(prompt)
                    if graph_data:
                        st.warning('Graph data collected', icon="⚠️")                
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error("Failed to generate response.")
                    st.stop()

        for message in st.session_state.get("messages", []):
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                try:
                    with st.spinner("Thinking..."):                 
                        response_placeholder = st.empty()
                        current_text = ""
                        for word in response.split():
                            current_text += word + ' '
                            response_placeholder.markdown(current_text)
                            sleep(0.1)
                        message = {"role": "assistant", "content": response}
                        st.session_state.messages.append(message)
                except Exception as e:
                    logging.error(f"Error generating response: {e}")
                    st.error("Failed to generate response.")    

    with col2:
        print("col 1")
        # st.header("Graph Visualization")
        if 'graph_data' in locals() and graph_data:

            nodes = [Node(id=n['title'], label=n['title']) for n in graph_data['nodes']]
            edges = [Edge(source=e['source'], target=e['target'], label=e['label']) for e in graph_data['links']]
            config = Config(height=800, width=800, nodeHighlightBehavior=True, highlightColor="#F7A7A6", directed=True, collapsible=True)
            return_value = agraph(nodes=nodes, edges=edges, config=config)                    

    with col3: 
        print("col 3")
        try:       
            if "graph_df" in locals():
                print("WE INSIDE")
                # print(graph_df.head())
                # st.session_state.df = graph_df[["title", "subtitle"]]

                st.dataframe(
                    graph_df,
                    hide_index=True
                )

        except Exception as err:
            print(err)

    

if __name__ == "__main__":
    main()
