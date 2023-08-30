# noqa: E501
from calendar import Calendar, day_abbr as day_abbrs, month_name as month_names
from datetime import datetime, timedelta

from bokeh.document import Document
from bokeh.embed import file_html
from bokeh.layouts import gridplot, layout
from bokeh.models import (CategoricalAxis, CategoricalScale, ColumnDataSource,
                          FactorRange, HoverTool, Plot, Rect, Text)
from bokeh.util.browser import view
from bokeh.plotting import figure
import streamlit as st
from dateutil.relativedelta import relativedelta
from bokeh.resources import INLINE
from bokeh.transform import factor_cmap
from bokeh.models.widgets import Div
from datetime import date
import holidays
import pandas as pd
us_holidays = holidays.US()

# Returns a "plot" object that displays a calendar month
def make_calendar(year: int, month: int, color_dict: dict, firstweekday: str = "Mon") -> Plot:
    firstweekday = list(day_abbrs).index(firstweekday)
    calendar = Calendar(firstweekday=firstweekday)

    month_days  = [ None if not day else str(day) for day in calendar.itermonthdays(year, month) ]
    month_weeks = len(month_days)//7

    workday = color_dict["instructional_day"]
    weekend = "white"
    holiday = color_dict["holiday"]

    def weekday(date):
        return (date.weekday() - firstweekday) % 7

    def pick_weekdays(days):
        return [ days[i % 7] for i in range(firstweekday, firstweekday+7) ]

    day_names = pick_weekdays(day_abbrs)
    week_days = pick_weekdays([workday]*5 + [weekend]*2)
    day_backgrounds = sum([week_days]*month_weeks, [])
    
    idx=0
    for day in month_days:
        if day:
            if date(year,month,int(day)) in us_holidays:
                # idx_day = month_days.index(day)
                day_backgrounds[idx] = holiday
        else:
            day_backgrounds[idx] = "white"
        idx+=1

    source = ColumnDataSource(data=dict(
        days            = list(day_names)*month_weeks,
        weeks           = sum([ [str(week)]*7 for week in range(month_weeks) ], []),
        month_days      = month_days,
        day_backgrounds = day_backgrounds,
    ))

    xdr = FactorRange(factors=list(day_names))
    ydr = FactorRange(factors=list(reversed([ str(week) for week in range(month_weeks) ])))
    x_scale, y_scale = CategoricalScale(), CategoricalScale()

    plot = Plot(x_range=xdr, y_range=ydr, x_scale=x_scale, y_scale=y_scale,
                width=300, height=300, outline_line_color=None)
    plot.title.text = month_names[month]
    plot.title.text_font_size = "16px"
    plot.title.text_color = "darkolivegreen"
    plot.title.offset = 25
    plot.min_border_left = 0
    plot.min_border_bottom = 5

    rect = Rect(x="days", y="weeks", width=0.9, height=0.9, fill_color="day_backgrounds", line_color="silver")
    plot.add_glyph(source, rect)

#    rect = Rect(x="holidays_days", y="holidays_weeks", width=0.9, height=0.9, fill_color="pink", line_color="indianred")
#    rect_renderer = plot.add_glyph(holidays_source, rect)

    text = Text(x="days", y="weeks", text="month_days", text_align="center", text_baseline="middle")
    plot.add_glyph(source, text)

    xaxis = CategoricalAxis()
    xaxis.major_label_text_font_size = "11px"
    xaxis.major_label_standoff = 0
    xaxis.major_tick_line_color = None
    xaxis.axis_line_color = None
    plot.add_layout(xaxis, 'above')

#    hover_tool = HoverTool(renderers=[rect_renderer], tooltips=[("Holiday", "@month_holidays")])
#    plot.tools.append(hover_tool)

    return plot

# Set Default Page Width = WIDE
st.set_page_config(layout='wide')

# Streamlit Global Environment Variables
if 'first_day' not in st.session_state:
    st.session_state.first_day = None


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

    # Checkboxes:
    even = st.checkbox('Even distribution of one day per week classes (14-15)')
    friday_convocation = st.checkbox("Convocation is a Friday before the First Instructional Day (ID)")
    monday_fall = st.checkbox("Fall semester starts on a Monday")
    extended_fall = st.checkbox("Extended Fall break (take off Monday-Wednesday before Thanksgiving)")
    monday_final = st.checkbox("Fall semester finals start on a Monday")
    summer_fall_difference = st.checkbox("Difference between the end of Summer and start of Fall semester is more than 7 calendar days")
    caesar_chavez = st.checkbox("Put Cesar Cavez Day in Spring Break (after if not selected)")
    monday_spring_final = st.checkbox("Spring semester finals start on a Monday")
    non_monday_commencement = st.checkbox("Commencement is Tuesday-Friday")
    memorial_commencement = st.checkbox("Commencement is before Memorial Day")
    winter_session_len = st.checkbox("Limit winter session to 10 days long")
    MLK_spring = st.checkbox("Spring starts after MLK")


    submitted = st.form_submit_button("Submit")

def make_grid(year: int):
    months = []
    rows = []
    for i in range(13):
        # Start our current month at August, and iterate until we reach August again
        cur_month = (7 + i) % 12 + 1

        # Move to next year once current month has gone past December
        if i <= 4:
            cur_year = year
        else:
            cur_year = year+1
        
        # Add generated month to array
        months.append(make_calendar(cur_year, cur_month))

        # Build each row of months and clear the array for the next months
        if (i+1) % 5 == 0 or i == 12:  # Every 5 months, start a new row
            rows.append(months)
            months = []

    grid = gridplot(toolbar_location=None, children=rows)
    return grid

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

def make_grid2(year: int, color_dict):
    months = []
    rows = []
    start_date = datetime(2013, 8, 1)
    j = 0
    for i in range(13):
        cur_date = start_date + relativedelta(months=i)
        months.append(make_calendar(cur_date.year, cur_date.month, color_dict))
        j += 1
        if j % 5 == 0:
            rows.append(months)
            months = []
        if i == 12:
            rows.append(months)
            # st.write(rows)
    
    grid = gridplot(toolbar_location=None, children=rows, width=200, height=200)
    return grid

if submitted:
    selected_year = st.session_state.first_day.year
    with st.expander("Option 1"):
        col1, col2, col3 = st.columns([1,15,1])
        with col1:
            st.write(' ')
        with col2:
            st.image("color_legend.png")
            st.bokeh_chart(make_grid2(selected_year, color_dict2), use_container_width= False)  # Display the grid for the selected year
        with col3:
            st.write(' ')  
    with st.expander("Option 2"):     
        col1, col2, col3 = st.columns([1,15,1])
        with col1:
            st.write(' ')
        with col2:
            st.image("table_test.png")
            st.bokeh_chart(make_grid2(selected_year, color_dict1), use_container_width= False)  # Display the grid for the selected year
        with col3:
            st.write(' ')  
        



