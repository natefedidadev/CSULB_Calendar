# noqa: E501
from datetime import datetime, date
import streamlit as st
import base64
from PIL import Image
import requests
from io import BytesIO
import logging

st.set_page_config(layout='wide')

logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w')

# Requests Tutorial
# https://www.geeksforgeeks.org/python-requests-tutorial/#


def build_years_request(dt : datetime, input_dict : dict):
    #dt = datetime.strptime(selected_year, "%Y-%m-%d")
    # Making a POST request
    payload = input_dict
    print(payload)

    response = requests.post("http://127.0.0.1:8000/calendar/build_years", json=payload)
    # response = requests.post("http://127.0.0.1:8000/calendar/build_years_test", json = payload)

    print(response.status_code)
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        return None
    
def download_calendar(input_dict, option_parameters):
    logging.debug("Attempting to download calendar with input_dict:")
    logging.debug(input_dict)

    url = "http://127.0.0.1:8000/calendar/download_excel_colored"  # Ensure your FastAPI server is running

    # Merge input_dict with option_parameters
    req_data = {**input_dict, **option_parameters}

    # Make a POST request to the FastAPI endpoint
    response = requests.post(url, json=req_data)

    if response.status_code == 200:
        # Retrieve the file content from FastAPI
        excel_data = response.content
        logging.debug("Excel file downloaded successfully.")
        return excel_data
    else:
        logging.error(f"Failed to download calendar. Status code: {response.status_code}")
        st.error("Failed to download calendar")
        return None



def main():

    # Initialize or retrieve session state variables
    if 'first_day' not in st.session_state:
        st.session_state.first_day = date(2025, 8, 18)  # Default value
    if 'excel_contents' not in st.session_state:
        st.session_state.excel_contents = {}
    if 'input_dict' not in st.session_state:
        st.session_state.input_dict = {}
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    if 'results' not in st.session_state:
        st.session_state.results = None

    # GUI
    st.markdown("## CSULB Academic Calendar Generator")

    with st.expander("Open to see the hard rules"):
        st.markdown("""
            **Hard Rules:**
            * Instructional Days is 147 ± 2 days
            * Academic Work Days is 175 ± 5 days
            * Fall and Spring semesters do not start on a Friday
            * Fall and Spring finals are 5 weekdays and one Saturday (either before, or after)
            * Fall semester must start between Aug 17 and Sep 1
            * Spring semester must start on or after Jan 15 (or Jan 16, if it is a leap year)
            * 2-5 days between Convocation and the beginning of Fall semester
            * 10-15 winter session Instructional Days
            * Summer session is at least 12 calendar weeks
            * 4 days between the end of Spring finals and before Summer start date are reserved for Commencement
            * Spring break is a calendar week
            * Fall Break is the Wednesday before Thanksgiving, Thursday, and Friday
            * Holidays are always considered to be of day type Holiday
            * Holidays that fall on weekend are observed on the nearest workdays
            * Academic Work Days include Instructional, Final, and Commencement
            * Convocation is held on an Academic Work Day between the first day of Fall and the first day of Fall classes.

            ---
        """)

    # Inputs
    st.session_state.first_day = st.date_input(
        "Select the first day of fall semester (15th - 30th of August ONLY)",
        value=st.session_state.first_day,
        min_value=date(2025, 8, 15),
        max_value=date(2050, 8, 30)
    )

    st.markdown("**Select the checkboxes of the soft rules to guarantee (Please select ___)**")
    c1, c2 = st.columns(2)
    with c1:
        # Checkboxes with default values from session_state
        even = st.checkbox('Even distribution of one day per week classes (14-15)', value=st.session_state.input_dict.get('even', False))
        friday_convocation = st.checkbox("Convocation is a Friday before the First Instructional Day (ID)", value=st.session_state.input_dict.get('friday_convocation', False))
        monday_fall = st.checkbox("Fall semester starts on a Monday", value=st.session_state.input_dict.get('monday_fall', False))
        monday_final = st.checkbox("Fall semester finals start on a Monday", value=st.session_state.input_dict.get('monday_final', False))
        monday_spring_final = st.checkbox("Spring semester finals start on a Monday", value=st.session_state.input_dict.get('monday_spring_final', False))
        summer_sessession_start = st.checkbox("Summer Session Starts after Memorial Day", value=st.session_state.input_dict.get('summer_sessession_start', False))

    with c2:
        # extended_fall = st.checkbox("Extended Fall break (take off Monday-Wednesday before Thanksgiving)", value=st.session_state.input_dict.get('extended_fall', True))
        # cesar_chavez = st.checkbox("Put Cesar Chavez Day in Spring Break (after if not selected)", value=st.session_state.input_dict.get('cesar_chavez', True))
        # non_monday_commencement = st.checkbox("Commencement is Tuesday-Friday", value=st.session_state.input_dict.get('non_monday_commencement', True))

        extended_fall = st.checkbox("Extended Fall break (take off Monday-Wednesday before Thanksgiving)", value=st.session_state.input_dict.get('extended_fall', False))
        cesar_chavez = st.checkbox("Put Cesar Chavez Day in Spring Break (after if not selected)", value=st.session_state.input_dict.get('cesar_chavez', False))
        non_monday_commencement = st.checkbox("Commencement is Tuesday-Friday", value=st.session_state.input_dict.get('non_monday_commencement', False))
        limit_winter_session = st.checkbox("Limit winter session to 10 days long", value=st.session_state.input_dict.get('limit_winter_session', False))
        MLK_spring = st.checkbox("Spring starts after MLK", value=st.session_state.input_dict.get('MLK_spring', False))

    if st.button("Submit"):
        # Update session_state with inputs
        st.session_state.input_dict = {
            'year': st.session_state.first_day.year,
            'month': st.session_state.first_day.month,
            'day': st.session_state.first_day.day,
            'even': even,
            'friday_convocation': friday_convocation,
            'monday_fall': monday_fall,
            'extended_fall': extended_fall,
            'monday_final': monday_final,
            'summer_sessession_start': summer_sessession_start,
            'cesar_chavez': cesar_chavez,
            'monday_spring_final': monday_spring_final,
            'non_monday_commencement': non_monday_commencement,
            'limit_winter_session': limit_winter_session,
            'MLK_spring': MLK_spring,
            'width': 350
        }
        st.session_state.submitted = True
        st.session_state.results = None
        st.session_state.excel_contents = {}

    # Validate the date
    if st.session_state.first_day < date(st.session_state.first_day.year, 8, 15) or st.session_state.first_day > date(st.session_state.first_day.year, 8, 30):
        st.markdown("#### Invalid Semester Start Date\nPlease choose a date between August 15 and August 30th.")
    elif st.session_state.submitted:
        with st.spinner("Building Calendars"):
            results = build_years_request(st.session_state.first_day, st.session_state.input_dict)
            st.session_state.results = results
            st.session_state.submitted = False

    # Display results
    if st.session_state.results:
        for i, result in enumerate(st.session_state.results, start=1):
            if result["image"]:
                # Ensure the expander remains open after interaction
                expander_key = f"option_{i}_expander"
                if expander_key not in st.session_state:
                    st.session_state[expander_key] = True

                with st.expander(f"Option {i}", expanded=st.session_state[expander_key]):
                    img = base64.b64decode(result['image'])
                    st.image(img, output_format="PNG")

                    # Generate and download Excel file
                    if st.button(f'Generate Excel for Option {i}', key=f'generate_button_{i}'):
                        logging.debug(f"Generating Excel for Option {i}")
                        excel_content = download_calendar(st.session_state.input_dict, result["parameters"])
                        if excel_content:
                            st.session_state.excel_contents[i] = excel_content
                            st.session_state[expander_key] = True  # Keep expander open
                            st.success(f"Excel for Option {i} generated!")
                        else:
                            st.error("Failed to generate Excel file.")

                    # Show the download button for generated Excel
                    if i in st.session_state.excel_contents:
                        st.download_button(
                            label=f"Download Excel for Option {i}",
                            data=st.session_state.excel_contents[i],
                            file_name=f"calendar_option_{i}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f'download_button_{i}'
                        )
    else:
        if st.session_state.submitted:
            st.error("No valid calendars found. Please adjust your settings.")


if __name__ == '__main__':
    main()