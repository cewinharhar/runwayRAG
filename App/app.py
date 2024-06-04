import streamlit as st
from dotenv import load_dotenv
from modules.initialPrompts import GREETING 
from modules.langAgent import consumerAgentDAO
import logging
from time import sleep

def main():
    try:
        st.set_page_config(page_title="Swiss startup assistant", page_icon="🚀", layout="centered", initial_sidebar_state="auto", menu_items=None)
        st.title("Ask questions about Swiss startups. If they are on the ventureLab website I know about them 💬")
        st.info("More [info](https://runway-incubator.ch/)", icon="📃")

        # query_params = st.query_params()
        # st.write(query_params)
        load_dotenv()    

        if "messages" not in st.session_state.keys(): 
            st.session_state.messages = [{"role": "assistant", "content": GREETING}]

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

        if prompt := st.chat_input("Your question"):
            st.session_state.messages.append({"role": "user", "content": prompt})

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                try:
                    with st.spinner("Thinking..."):
                        response = st.session_state.agentDAO.generate_response(prompt)

                        # Placeholder for streaming the response
                        response_placeholder = st.empty()

                        # Initialize an empty string to accumulate the response
                        current_text = ""

                        # Split the response into words and stream them
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

    except Exception as e:
        logging.error(f"Unexpected error in the application: {e}")
        st.error("An unexpected error occurred.")

if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print("Error sleeping 10s")
        sleep(10)
        main()
    finally:
        exit()