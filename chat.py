import streamlit as st
import random
import time
import requests
import json
import yaml

projects = []
project_ids = []


def load_config():
    with open('config.yaml', 'r') as file:
        config_content = yaml.safe_load(file)
    return config_content


config = load_config()
api_key = config['AAI-Brain']['API-KEY']
api_secret = config['AAI-Brain']['API-Secret']


def clear_session_state():
    st.session_state.messages = []
    print("cleared")


def create_chat(project_id):
    st.session_state.messages = []
    url_create = "https://api.getodin.ai/chat/create"
    payload = json.dumps({'project_id': project_id})
    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key,
        "X-API-SECRET": api_secret,
        "content-type": "application/json"
    }
    response_create = requests.post(url_create, data=payload, headers=headers)
    conv_id = json.loads(response_create.content)["chat_id"]
    return conv_id


def get_projects():
    url_projects = "https://api.getodin.ai/projects"
    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key,
        "X-API-SECRET": api_secret,
    }

    response_projects = requests.get(url_projects, headers=headers)
    projects_json = json.loads(response_projects.content)
    global projects
    projects = [project for project in projects_json['projects']]
    global project_ids
    project_ids = [project['name'] for project in projects_json['projects']]
    return projects, project_ids


# Call Projects function to fill the select-box element
get_projects()


@st.experimental_fragment
def sidebar_update():
    project_name = st.selectbox(
        "Select Project name",
        project_ids,
        index=None,
        placeholder="Select Project name...",
    )

    for project in projects:
        if project['name'] == project_name:
            project_id_selected = project['id']
            st.session_state["project_id_selected"] = project_id_selected



# Create streaming Object from Response
def response_generator(response_str):
    full_response = ""
    for word in response_str:
        time.sleep(0.01)
        yield word

st.set_page_config(page_title='Automation Anywhere - AAI Brain', page_icon = 'https://chat-beta.automationanywhere.com/assets/icon/favicon.ico', layout='wide')
st.header("Automation Anywhere - AAI Brain")
# st.image("https://chat-beta.automationanywhere.com/static/media/aa-gen-ai-logo.17572d7b831dd1a39cf8.png")
st.html("""
    <!doctype html>
    <html lang="en">
    <head>
    	<meta charset="utf-8"/>
    <title>AAI Enterprise Knowledge</title>
    </head>
    <body>
    <center> 
    <img src=https://chat-beta.automationanywhere.com/static/media/aa-gen-ai-logo.17572d7b831dd1a39cf8.png width=200>
    </center>
    </html>
""")

# Create a sidebar using Streamlit's built-in function
with st.sidebar:
    # Call the sidebar_update() function decorator
    sidebar_update()
    # Create a primary button in the sidebar with the label "Create a new Chat"
    if st.button("Create a new Chat", type="primary"):
        clear_session_state()
        clear_session_state()
        # Set the value of the session state variable 'chat_id' to the result of calling create_chat()
        # with the 'project_id_selected' value from the session state
        st.session_state['chat_id'] = create_chat(st.session_state["project_id_selected"])


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get('image', 0) != 0:
            # print(message["image"])
            st.image(message["image"], 'Generated Image(s)')
        else:
            st.markdown(message["content"])
            # pass


# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    session_state_test = st.session_state
    # Check if a chat ID has been set in the session state.
    # If not, check if a project ID has been selected.
    if session_state_test.get('chat_id', 0) == 0:
        # If no chat ID, but a project ID has been selected, create a new chat.
        if session_state_test.get('project_id_selected', 0) == 0:
            # Display a toast message prompting the user to select a project.
            st.toast('Select a project first', icon='🚨')
            st.stop()
        else:
            # Create a new chat with the selected project ID and set it as the chat ID.
            st.session_state["chat_id"] = create_chat(st.session_state['project_id_selected'])

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    # Display user message in chat message container
    with st.chat_message("assistant"):
        chat_id = st.session_state["chat_id"]
        project_id = st.session_state["project_id_selected"]
        print(f"chat with project {project_id}")
        url_message = "https://api.getodin.ai/v2/chat/message"
        payload = f"-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"agent_type\"\r\n\r\nchat_agent\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"message\"\r\n\r\n{prompt}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"project_id\"\r\n\r\n{project_id}\r\n-----011000010111000001101001--"
        chat_headers = {
            "accept": "application/json",
            "X-API-KEY": api_key,
            "X-API-SECRET": api_secret,
            "content-type": "multipart/form-data; boundary=---011000010111000001101001"
        }

        response = requests.post(url_message, data=payload, headers=chat_headers)

        response_message = st.write_stream(response_generator(json.loads(response.text)['message']['response']))
        images = []
        if (json.loads(response.text)['message']).get('image_urls', 0) != 0:
            print('got an image')
            print(json.loads(response.text)['message']['image_urls'][0])

            for index, image in enumerate(json.loads(response.text)['message']['image_urls'], start=1):
                images.append(image)
            image_message = st.image(images, caption=f'Generated Image(s)')
    if len(images) > 0:
        st.session_state.messages.append({"role": "assistant", "content": response_message})
        st.session_state.messages.append({"role": "assistant", "image": images})
    else:
        st.session_state.messages.append({"role": "assistant", "content": response_message})


