# noqa: E501
from calendar import Calendar, day_abbr as day_abbrs, month_name as month_names
from datetime import datetime, timedelta

import streamlit as st
import streamlit.components.v1 as components
from dateutil.relativedelta import relativedelta
from datetime import date
import holidays
import pandas as pd
import plotly.graph_objects as go
#from .classes.month import CalMonth
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

us_holidays = holidays.US()

# Requests Tutorial
# https://www.geeksforgeeks.org/python-requests-tutorial/#

# Set Default Page Width = WIDE
st.set_page_config(layout='wide')

# Streamlit Global Environment Variables
if 'first_day' not in st.session_state:
    st.session_state.first_day = None


def build_year_request(dt : datetime):
    #dt = datetime.strptime(selected_year, "%Y-%m-%d")
    # Making a POST request
    payload = {'month':dt.month, 'day':dt.day, 'year':dt.year}

    response = requests.post("http://127.0.0.1:8000/calendar/build_year", json = payload)

    if response.status_code == 200:
        img_bytes = BytesIO(response.content)
        img = Image.open(img_bytes)
        return img
    else:
        return {"msg":"error"}

# GUI
st.markdown("## CSULB Academic Calender Generator")

with st.expander("Open to see the hard rules"):
    st.markdown("""
                **Hard Rules:**
                * Instructional Days is 147 ± 2 days
                * Academic Work Days is 147 ± 2 days
                * Fall and Spring semesters do not start on a Friday
                * Fall and Spring finals are 5 weekdays and one Saturday (either before, in the middle , or after)
                * Fall semester must start between Aug 17 and Sep 1
                * Spring semester must start on or after Jan 15 (or Jan 16, if it is a leap year)
                * Spring semester must start on or after before May 31
                * 2-5 days between Convocation and the beginning of Fall semester
                * 10-15 winter session Instructional Days
                * Summer session is at least 12 calendar weeks
                * 4 days between the end of Spring finals and before Summer start date are reserved for Commencement
                * Spring break is a calendar week
                * Fall Break is the Wednesday before Thanksgiving, Thursday, and Friday
                * Holidays are always considered to be of day type Holiday
                Holidays that fall on weekend are observed on the nearest ____
                Academic Work Days include Instructional, Final, and Commencement
                Convocation is held on an Academic Work Day between the first _______

                ---
    """)
with st.form("input_form"):

    st.session_state.first_day = st.date_input("Select the first day of fall semester", format="MM/DD/YYYY")
    st.markdown("""**Select the checkboxes of the soft rules to guarantee (Please select ___)** """)
    c1, c2 = st.columns(2)
    with c1:
        # Checkboxes:
        even = st.checkbox('Even distribution of one day per week classes (14-15)')
        friday_convocation = st.checkbox("Convocation is a Friday before the First Instructional Day (ID)")
        monday_fall = st.checkbox("Fall semester starts on a Monday")
        extended_fall = st.checkbox("Extended Fall break (take off Monday-Wednesday before Thanksgiving)")
        monday_final = st.checkbox("Fall semester finals start on a Monday")
        summer_fall_difference = st.checkbox("Difference between the end of Summer and start of Fall semester is more than 7 calendar days")
    
    with c2:
        caesar_chavez = st.checkbox("Put Cesar Cavez Day in Spring Break (after if not selected)")
        monday_spring_final = st.checkbox("Spring semester finals start on a Monday")
        non_monday_commencement = st.checkbox("Commencement is Tuesday-Friday")
        memorial_commencement = st.checkbox("Commencement is before Memorial Day")
        winter_session_len = st.checkbox("Limit winter session to 10 days long")
        MLK_spring = st.checkbox("Spring starts after MLK")
        submitted = st.form_submit_button("Submit")


color_dict1 = {
    "academic_work_day": "lightsteelblue",
    "instructional_day": "lightyellow",
    "convocation": "darkblue",
    "commencement": "lightbrown",
    "finals": "pink",
    "holiday": "white",
    "semester_start": "green",
    "no_class_campus_open": "purple",
    "summer_session": "orange",
    "winter_session": "grey"
}

color_dict2 = {
    "academic_work_day": "turquoise",
    "instructional_day": "navajowhite",
    "convocation": "darkblue",
    "commencement": "lightbrown",
    "finals": "darkgreen",
    "holiday": "pink",
    "semester_start": "lightpurple",
    "no_class_campus_open": "darkpurple",
    "summer_session": "yellow",
    "winter_session": "steelblue"
}

if submitted:
    with st.expander("Option 1"):
        col1, col2, col3 = st.columns([1,15,1])
        with col1:
            st.write(' ')
        with col2:
            #st.image(build_year(selected_year))
            # call the build_year endpoint on the server, -> get the image
            # display the image
            img = build_year_request(st.session_state.first_day)
            #st.write(img)
            st.image(img, output_format="PNG")
        with col3:
            st.write(' ')  

