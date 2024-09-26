# noqa: E501
from datetime import datetime, date
import streamlit as st
import base64
from PIL import Image
import requests
from io import BytesIO

# Requests Tutorial
# https://www.geeksforgeeks.org/python-requests-tutorial/#


def build_years_request(dt : datetime, input_dict : dict):
    #dt = datetime.strptime(selected_year, "%Y-%m-%d")
    # Making a POST request
    payload = input_dict

    response = requests.post("http://127.0.0.1:8000/calendar/build_years", json=payload)
    # response = requests.post("http://127.0.0.1:8000/calendar/build_years_test", json = payload)

    if response.status_code == 200:
        result = response.json()
        return result
    else:
        return None
    
def download_calendar():
    url = "http://127.0.0.1:8000/calendar/download_excel_colored"  # Ensure your FastAPI server is running

    # Sample data to send with the request
    req_data = {
        "some_field": "value"  # Update this with the appropriate fields for Calendar_Input
    }
    
    # Make a POST request to the FastAPI endpoint
    response = requests.post(url, json=req_data)
    
    if response.status_code == 200:
        # Retrieve the file content from FastAPI
        excel_data = response.content

        # Streamlit download button for downloading the file
        st.download_button(
            label="Download Excel Calendar",
            data=excel_data,
            file_name="calendar_colored.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Failed to download calendar")

def main():
    # Set Default Page Width = WIDE
    input_dict = None
    st.set_page_config(layout='wide')

    # Streamlit Global Environment Variables
    if 'first_day' not in st.session_state:
        st.session_state.first_day = None
    if 'excel_contents' not in st.session_state:
        st.session_state.excel_contents = {}

    # GUI
    st.markdown("## CSULB Academic Calender Generator")

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
    with st.form("input_form"):

        # Update the date_input to allow for a broader year range (up to 2050)
        st.session_state.first_day = st.date_input(
            "Select the first day of fall semester (15th - 30th of August ONLY)", 
            format="MM/DD/YYYY", 
            value=date(2025, 8, 18),  # Default value
            min_value=date(2025, 8, 15),  # Minimum selectable date
            max_value=date(2050, 8, 30)   # Maximum selectable date extended to 2050
        )

        st.markdown("""**Select the checkboxes of the soft rules to guarantee (Please select ___)** """)
        c1, c2 = st.columns(2)
        with c1:
            # Checkboxes:
            even = st.checkbox('Even distribution of one day per week classes (14-15)')
            friday_convocation = st.checkbox("Convocation is a Friday before the First Instructional Day (ID)")
            monday_fall = st.checkbox("Fall semester starts on a Monday")
            monday_final = st.checkbox("Fall semester finals start on a Monday")
            monday_spring_final = st.checkbox("Spring semester finals start on a Monday")
            summer_sessession_start = st.checkbox("Summer Session Starts after Memorial Day")

        with c2:
            extended_fall = st.checkbox("Extended Fall break (take off Monday-Wednesday before Thanksgiving)", value=True)
            cesar_chavez = st.checkbox("Put Cesar Chavez Day in Spring Break (after if not selected)", value=True)
            non_monday_commencement = st.checkbox("Commencement is Tuesday-Friday", value=True)
            limit_winter_session = st.checkbox("Limit winter session to 10 days long")
            MLK_spring = st.checkbox("Spring starts after MLK")
            submitted = st.form_submit_button("Submit")


    if submitted:
        input_dict = {
            'year': st.session_state.first_day.year,
            'month': st.session_state.first_day.month,
            'day': st.session_state.first_day.day,
            'even':even,
            'friday_convocation':friday_convocation,
            'monday_fall':monday_fall,
            'extended_fall':extended_fall,
            'monday_final':monday_final,
            'summer_sessession_start':summer_sessession_start,
            'cesar_chavez':cesar_chavez,
            'monday_spring_final':monday_spring_final,
            'non_monday_commencement':non_monday_commencement,
            'limit_winter_session':limit_winter_session,
            'MLK_spring':MLK_spring
        }
        if st.session_state.first_day < date(st.session_state.first_day.year, 8, 15) or st.session_state.first_day > date(st.session_state.first_day.year, 8, 30):
            st.markdown("""#### Invalid Semester Start Date
                            Please choose a date between August 15 and August 30th """)
        else:
            with st.spinner("Building Calendars"):
                results = build_years_request(st.session_state.first_day, input_dict)
                if results:
                    i = 1
                    for result in results:
                        if result["image"]:
                            with st.expander(f"Option {i}"):
                                col1, col2, col3 = st.columns([1, 15, 1])
                                with col1:
                                    st.write(' ')
                                with col2:
                                    img = base64.b64decode(result['image'])
                                    st.image(img, output_format="PNG")
                                with col3:
                                    st.write(' ')

                            # Generate Excel for this option
                            if st.button(f'Generate Excel for Option {i}', key=f'generate_button_{i}'):
                                excel_content = download_calendar(input_dict)
                                if excel_content:
                                    st.session_state.excel_contents[i] = excel_content
                                    st.success(f"Excel for Option {i} generated!")

                            # Show the download button for generated Excel
                            if i in st.session_state.excel_contents:
                                st.download_button(
                                    label=f"Download Excel for Option {i}",
                                    data=st.session_state.excel_contents[i],
                                    file_name=f"calendar_option_{i}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )

                            i += 1
                else:
                    st.markdown("#### No Valid Calendars Found. Please adjust your settings.")

if __name__ == '__main__':
    main()