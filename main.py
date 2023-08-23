# noqa: E501
from calendar import Calendar, day_abbr as day_abbrs, month_name as month_names

from bokeh.document import Document
from bokeh.embed import file_html
from bokeh.layouts import gridplot
from bokeh.models import (CategoricalAxis, CategoricalScale, ColumnDataSource,
                          FactorRange, HoverTool, Plot, Rect, Text)
from bokeh.sampledata.us_holidays import us_holidays
from bokeh.util.browser import view
from bokeh.plotting import figure
import streamlit as st




def make_calendar(year: int, month: int, firstweekday: str = "Mon") -> Plot:
    firstweekday = list(day_abbrs).index(firstweekday)
    calendar = Calendar(firstweekday=firstweekday)

    month_days  = [ None if not day else str(day) for day in calendar.itermonthdays(year, month) ]
    month_weeks = len(month_days)//7

    workday = "linen"
    weekend = "lightsteelblue"

    def weekday(date):
        return (date.weekday() - firstweekday) % 7

    def pick_weekdays(days):
        return [ days[i % 7] for i in range(firstweekday, firstweekday+7) ]

    day_names = pick_weekdays(day_abbrs)
    week_days = pick_weekdays([workday]*5 + [weekend]*2)

    source = ColumnDataSource(data=dict(
        days            = list(day_names)*month_weeks,
        weeks           = sum([ [str(week)]*7 for week in range(month_weeks) ], []),
        month_days      = month_days,
        day_backgrounds = sum([week_days]*month_weeks, []),
    ))

    holidays = [ (date, summary.replace("(US-OPM)", "").strip()) for (date, summary) in us_holidays
        if date.year == year and date.month == month and "(US-OPM)" in summary ]

    holidays_source = ColumnDataSource(data=dict(
        holidays_days  = [ day_names[weekday(date)] for date, _ in holidays ],
        holidays_weeks = [ str((weekday(date.replace(day=1)) + date.day) // 7) for date, _ in holidays ],
        month_holidays = [ summary for _, summary in holidays ],
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

    rect = Rect(x="holidays_days", y="holidays_weeks", width=0.9, height=0.9, fill_color="pink", line_color="indianred")
    rect_renderer = plot.add_glyph(holidays_source, rect)

    text = Text(x="days", y="weeks", text="month_days", text_align="center", text_baseline="middle")
    plot.add_glyph(source, text)

    xaxis = CategoricalAxis()
    xaxis.major_label_text_font_size = "11px"
    xaxis.major_label_standoff = 0
    xaxis.major_tick_line_color = None
    xaxis.axis_line_color = None
    plot.add_layout(xaxis, 'above')

    hover_tool = HoverTool(renderers=[rect_renderer], tooltips=[("Holiday", "@month_holidays")])
    plot.tools.append(hover_tool)

    return plot

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
    first_day = st.date_input("Select the first day of fall semester", format="MM/DD/YYYY")

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
    
if submitted:
    with st.expander("Option 1"):
        st.bokeh_chart(make_calendar(2015,4))
    with st.expander("Option 2"):
        st.bokeh_chart(make_calendar(2016,5))


# Output
# col_list = st.columns(3,gap="medium")
# # Print the months in a year
# for i in range(1, 13):
#     with col_list[i%3]:
#         st.bokeh_chart(make_calendar(2015, i))


