# CSULB Academic Calendar Project

## Overview
This project encompasses the design and deployment of the official Academic Calendar Generator for California State University, Long Beach (CSULB). The front-end is located in the *gui* folder and the back-end is located in the *app* folder.

## Key Features
- **FastAPI Backend**: Robust and scalable back-end using FastAPI.
- **Streamlit Frontend**: Efficient and visually appealing front-end using Streamlit.
- **Multiprocessing**: Leverages Python's multiprocessing capabilities for enhanced performance.
- **Dynamic Calendar Generation**: Programmatic construction of calendars with customization options.
- **Data Visualization**: Utilizes PIL (Python Imaging Library) for visualizing calendars and Streamlit along with Plotly for front-end visualizations.


## Initial set-up:
To start backend server locally:
1. Clone the repository.

2. Activate the virtual environment (on the host server, not applicable to those cloning the repo on their machines for the first time)

   `source venv/bin/activate`

3. Install the required dependencies located in the requirements.txt on both the home directory of the repo and the gui/ directory: 
    
    `pip install -r requirements.txt`

## Starting GNU Screen sessions and booting the web app within them

   * Before creating new sessions, run `screen -ls` to check if there are already screen sessions. If there are, use those ones as they are already running the web app on them. Otherwise follow the steps below to create new ones.

   1. Start the GNU Screen sessions for both the frontend and the backend. This is crucial as the server tends to log out users for inactivity (which also kills processes), so to keep the web app running we must start screen sessions

    We will start two separate sessions. You can replace the words 'backend' and 'frontend' with anything you like, as these are just the names of the sessions.

    `screen -S backend`
    `screen -S frontend`

    To enter/attach to a screen session, use `screen -r <name of session>`. To detach from a screen session, use Ctrl + A then D.

   * Backend

   (On the backend screen session) Run the application using Uvicorn:
    
    `uvicorn app.main:app --host 127.0.0.1 --port 8000`

   * Frontend

   Run streamlit

    `streamlit gui.py`

   ** VERY IMPORTANT: When you finish running the web app on the screen sessions, make sure you detach from the screen session using Ctrl + A then D. This is important for allowing the web app to run indefinitely even if the server logs you out **
