# CSULB Academic Calendar Project

## Overview
This project encompasses the design and deployment of the official Academic Calendar Generator for California State University, Long Beach (CSULB). The front-end is located in the *gui* folder and the back-end is located in the *app* folder.

## Key Features
- **FastAPI Backend**: Robust and scalable back-end using FastAPI.
- **Streamlit Frontend**: Efficient and visually appealing front-end using Streamlit.
- **Multiprocessing**: Leverages Python's multiprocessing capabilities for enhanced performance.
- **Dynamic Calendar Generation**: Programmatic construction of calendars with customization options.
- **Data Visualization**: Utilizes PIL (Python Imaging Library) for visualizing calendars and Streamlit along with Plotly for front-end visualizations.


## How to Launch Back-end:
To start backend server locally:
1. Clone the repository.
2. Install the required dependencies located in the requirements.txt: 
    
    `pip install -r requirements.txt`

3. Run the application using Uvicorn:
    
    `uvicorn app.main:app --host 127.0.0.1 --port 8000`

## How to Launch Front-end:

1. Install the required dependencies located in the requirements.txt: 
    
    `cd gui`

    `pip install -r requirements.txt`

2. Run streamlit

    `streamlit gui.py`
