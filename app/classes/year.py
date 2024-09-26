from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
from .month import DayType, Day, CalMonth
import holidays
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from io import BytesIO
from enum import Enum
from typing import Optional
import multiprocessing as mp
import random
from typing import Dict, Any
import hashlib
import json

class Day(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

class Calendar_Input(BaseModel):
    month: int
    day : int 
    year: int
    even: bool
    friday_convocation: bool
    monday_fall: bool
    extended_fall: bool
    monday_final: bool
    summer_sessession_start: bool
    cesar_chavez: bool
    monday_spring_final: bool
    non_monday_commencement: bool
    limit_winter_session: bool
    MLK_spring: bool
    
    width: Optional[int] = 350

class DayType(Enum):
    NONE = 0
    AWD = 1
    CONVOCATION = 2
    ID = 3
    FINALS = 4
    NO_CLASS_CAMPUS_OPEN = 5
    COMMENCEMENT = 6
    SUMMER_SESSION = 7
    WINTER_SESSION = 8
    HOLIDAY = 9
    VOID = 10

class CalYear:
    def __init__(self, inputs : Calendar_Input, font_path = "fonts/OpenSans-Regular.ttf",font_path_bold = "fonts/OpenSans-Bold.ttf"):
        self.legend_data = {
            "None": "#FFFFFF",
            "AWD": "#ccecff",
            "ID": "#efef95",
            "Convocation": "#50E3C2",
            "Finals": "#f8cbad",
            "No Class, Campus Open": "#ae76c7",
            "Commencement": "#BD10E0",
            "Summer Session": "#c5e0b4",
            "Winter Session": "#cfcfcf"
        }
        self.holiday_list = ['Martin Luther King Jr. Day', 'Labor Day', 'Thanksgiving', 'Day After Thanksgiving', 'New Year\'s Day', 'New Year\'s Day (Observed)', 'Independence Day', 'Independence Day (Observed)', 'Cesar Chavez Day', 'Cesar Chavez Day (Observed)', 'Veterans Day', 'Veterans Day (Observed)', 'Christmas Day', 'Christmas Day (Observed)', 'Memorial Day', 'Juneteenth National Independence Day']
        self.font_size = 22
        self.small_font_size = 18
        self.font = ImageFont.truetype(font_path_bold, self.font_size)
        self.small_font = ImageFont.truetype(font_path, self.small_font_size)
        self.small_font_bold = ImageFont.truetype(font_path_bold, self.small_font_size)
        self.holiday_days : dict = {}
        self.us_holidays = holidays.country_holidays('US') + holidays.country_holidays('US','CA') + holidays.country_holidays('US','VI')
        self.day_id_count: dict = {"fall": {Day.MONDAY: 0, Day.TUESDAY: 0, Day.WEDNESDAY: 0, Day.THURSDAY: 0, Day.FRIDAY: 0},
                                   "spring": {Day.MONDAY: 0, Day.TUESDAY: 0, Day.WEDNESDAY: 0, Day.THURSDAY: 0, Day.FRIDAY: 0}}
        self.day_awd_count: dict = {"fall": {Day.MONDAY: 0, Day.TUESDAY: 0, Day.WEDNESDAY: 0, Day.THURSDAY: 0, Day.FRIDAY: 0, Day.SATURDAY: 0},
                                   "spring": {Day.MONDAY: 0, Day.TUESDAY: 0, Day.WEDNESDAY: 0, Day.THURSDAY: 0, Day.FRIDAY: 0, Day.SATURDAY: 0}}

        self.inputs = inputs
        self.start_date = date(inputs.year, inputs.month, inputs.day)
        self.valid = True
        self.months = []

        if self.start_date < date(inputs.year, 8, 15) or self.start_date >= date(inputs.year, 9, 1):
            self.valid = False
            return

        # Instantiate empty stats dict
        self.reset()
        self.setup_calendar()

    def reset(self):
        self.months = []
        self.month_stats : dict = {}
        self.cal_dict : dict = {}
        self.day_id_count: dict = {"fall": {Day.MONDAY: 0, Day.TUESDAY: 0, Day.WEDNESDAY: 0, Day.THURSDAY: 0, Day.FRIDAY: 0},
                                   "spring": {Day.MONDAY: 0, Day.TUESDAY: 0, Day.WEDNESDAY: 0, Day.THURSDAY: 0, Day.FRIDAY: 0}}
        self.day_awd_count: dict = {"fall": {Day.MONDAY: 0, Day.TUESDAY: 0, Day.WEDNESDAY: 0, Day.THURSDAY: 0, Day.FRIDAY: 0, Day.SATURDAY: 0},
                                   "spring": {Day.MONDAY: 0, Day.TUESDAY: 0, Day.WEDNESDAY: 0, Day.THURSDAY: 0, Day.FRIDAY: 0, Day.SATURDAY: 0}}
        # Important dates
        self.fall_semester_start : date = None
        self.spring_semester_start : date = None
        self.commencement_end : date = None
        self.summer_session_start : date = None
        self.winter_session_start : date = None
        self.winter_session_end : date = None
        self.pre_fall_semester_start: date = None
        self.convocation_day: date = None
        self.commencement_start: date = None
        self.summer_session_id: int = 0
        self.winter_session_id: int = 0
        self.num_awd: int = 0
        self.num_id: int = 0

        cur_date = date(self.start_date.year, self.start_date.month, 1)
        for _ in range(13):
            self.month_stats[cur_date] = {"ID": 0, "AWD": 0, "SUM": 0, "WIN": 0}
            cur_date = cur_date + relativedelta(months=1)
    
    def gen_schedule(self, awd: int = 170, id: int = 145, convocation: int = 2, winter: int = 12) -> Image and str:
        # 170 <= Acadmeic Work Days (AWD) <= 180
        # 145 <= Instructional Days (ID) <= 149
        # Avoid starting a semester on a Friday.
        self.reset()  
        self.setup_calendar()      
        # clear current calendar list
        current_calendar: list[CalMonth] = []
        
        # Test if start date is valid weekday and not on the weekend
        if is_weekend(self.start_date):
            print("ERROR: cannot begin calendar on a weekend")
            return None, None
        # Compute Validity tests
        if not self.compute_spring_break(combine_cc_day=self.inputs.cesar_chavez):
            return None, None
        if not self.compute_winter_session(winter):
            return None, None
        if not self.compute_id(id, convocation):
            return None, None
        if not self.compute_summer_session():
            return None, None
        if not self.compute_awd(awd):
            return None, None
            
        # Build calendar year starting at start date
        for i in range(13):
            cur_date = self.start_date + relativedelta(months=i)
            cmonth = CalMonth(cur_date.year,cur_date.month, self.font, self.small_font, self.small_font_bold)

            if cmonth.month == self.start_date.month:
                pass
            current_calendar.append(cmonth)
        
        # Color the days based on type
        for i in range(13):
            cur_day = date(current_calendar[i].year, current_calendar[i].month, 1)
            end_day = cur_day + relativedelta(months=1)
            while cur_day < end_day:
                if cur_day in self.cal_dict and DayType.AWD == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bgcolor(cur_day.day, self.legend_data["AWD"])
                elif cur_day in self.cal_dict and DayType.ID == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bgcolor(cur_day.day, self.legend_data["ID"])
                elif cur_day in self.cal_dict and DayType.NO_CLASS_CAMPUS_OPEN == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bgcolor(cur_day.day, self.legend_data["No Class, Campus Open"])
                elif cur_day in self.cal_dict and DayType.WINTER_SESSION == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bgcolor(cur_day.day, self.legend_data["Winter Session"])
                elif cur_day in self.cal_dict and DayType.FINALS == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bgcolor(cur_day.day, self.legend_data["Finals"])
                elif cur_day in self.cal_dict and DayType.HOLIDAY == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bold(cur_day.day)
                elif cur_day in self.cal_dict and DayType.SUMMER_SESSION == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bgcolor(cur_day.day,self.legend_data["Summer Session"])
                elif cur_day in self.cal_dict and DayType.CONVOCATION == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bgcolor(cur_day.day,self.legend_data["Convocation"])
                elif cur_day in self.cal_dict and DayType.COMMENCEMENT == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bgcolor(cur_day.day,self.legend_data["Commencement"])
                cur_day = cur_day + timedelta(days=1)

            #note = f"AWD={self.month_stats[current_calendar[i].get_month()]['AWD']}, ID={self.month_stats[current_calendar[i].get_month()]['ID']}"
            note = ""
            if self.month_stats[current_calendar[i].get_month()]['AWD']:
                note += f"AWD={self.month_stats[current_calendar[i].get_month()]['AWD']}"
            if self.month_stats[current_calendar[i].get_month()]['ID']:
                note += f" ID={self.month_stats[current_calendar[i].get_month()]['ID']}"
            if self.month_stats[current_calendar[i].get_month()]['SUM']:
                note += f" SUM={self.month_stats[current_calendar[i].get_month()]['SUM']}"
            if self.month_stats[current_calendar[i].get_month()]['WIN']:
                note += f" WIN={self.month_stats[current_calendar[i].get_month()]['WIN']}"
            current_calendar[i].set_month_note(note)

        current_calendar[(self.fall_semester_start.month+5)%13].set_day_bold_outline(self.fall_semester_start.day)
        current_calendar[(self.spring_semester_start.month-1+5)%13].set_day_bold_outline(self.spring_semester_start.day)
        current_calendar[(self.summer_session_start.month-1+5)%13].set_day_bold_outline(self.summer_session_start.day)
        return self.draw(current_calendar), self.dict_hash(self.cal_dict)
        # compute AWD

    def compute_awd(self, num_awd_days: int = 170) -> bool | int:
        """ AWD must be between 170 - 180 """
        if num_awd_days < 170 or num_awd_days > 180:
            return False

        cur_date = self.start_date
        self.num_awd = 0
        # christmas = date(self.start_date.year, 12, 25) # self.us_holidays.get_named("Christmas Day (observed)")[2]

        # For the week before instructional days start
        prelim_days_list = []
        while cur_date < self.fall_semester_start:
            # if current day isn't a Sunday, Saturday, or is a US Holiday
            if not is_weekend(cur_date):
                if self.cal_dict[cur_date] == DayType.NONE:
                    self.cal_dict[cur_date] = DayType.AWD
                    if cur_date <= self.fall_semester_start + relativedelta(days=-2):
                        prelim_days_list.append(cur_date)
                        
                self.num_awd += 1
                self.month_stats[date(cur_date.year, cur_date.month, 1)]["AWD"] += 1
                self.calc_awd_days(cur_date)
            cur_date = cur_date + relativedelta(days=1)

        if self.convocation_day == None:
            self.convocation_day = random.choice(prelim_days_list)
            self.cal_dict[self.convocation_day] = DayType.CONVOCATION
        else:
            self.calc_awd_days(self.convocation_day)
        # self.month_stats[date(cur_date.year, cur_date.month, 1)]["AWD"] += 1
        # self.num_awd +=1    
        
        # For Fall Semester, While the current date is before Christmas
        # while cur_date < date(self.start_date.year+1, self.start_date.month+1, self.start_date.day):
            # if current day isn't a Sunday, Saturday, or is a US Holiday
        while self.num_awd < num_awd_days:
            if cur_date >= self.summer_session_start:
                print("ERROR: AWD goes into summer session")
                return False
            if self.cal_dict[cur_date] in [DayType.ID, DayType.AWD, DayType.FINALS, DayType.CONVOCATION, DayType.COMMENCEMENT]:
                # these days are also AWD
                self.num_awd += 1
                self.month_stats[date(cur_date.year, cur_date.month, 1)]["AWD"] += 1
                self.calc_awd_days(cur_date)
            elif not is_weekend(cur_date) and self.cal_dict[cur_date] == DayType.NONE:
                self.cal_dict[cur_date] = DayType.AWD
                self.num_awd += 1
                self.month_stats[date(cur_date.year, cur_date.month, 1)]["AWD"] += 1
                self.calc_awd_days(cur_date)
                
            cur_date = cur_date + relativedelta(days=1)

        if cur_date <= self.commencement_end:
            print("ERROR: Not enough AWD to build Calendar")
            return False
        
        if not is_weekend(cur_date) and self.cal_dict[cur_date] == DayType.NONE:
            print("ERROR: Gap between end of spring and start of summer")
            return False

        # if not (is_weekend(cur_date) or self.cal_dict[cur_date] == self.summer_session_start or self.cal_dict[cur_date] == DayType.AWD):
        #     print("ERROR: Not enough AWD to finish commencement")
        #     return False

        if self.cal_dict[self.winter_session_end + relativedelta(days=1)] == DayType.AWD:
            print("ERROR: Spring cannot start on a Friday")
            return False
        
        return self.num_awd
    
    def compute_id(self, num_id_days:int = 145, num_convocation_days = 2) -> bool:
        """ Compute Instructional Days (ID) """
        # Total for Fall and Spring 145-149
        if num_id_days < 145 or num_id_days > 149:
            return False
        self.num_id = 0
        
        """ FALL SEMESTER START DATE """
        # We need to first figure out the convocation day.
        if self.inputs.friday_convocation:
            # get the next friday from the start date
            days_until_friday = (4 - self.start_date.weekday() + 7) % 7
            self.convocation_day = self.start_date + relativedelta(days=days_until_friday)
            self.cal_dict[self.convocation_day] = DayType.CONVOCATION
        
        self.fall_semester_start = add_weekdays(self.start_date, num_convocation_days)

        # If Fall semester start date is a friday, push to monday
        if self.fall_semester_start.weekday() == 4:
            self.fall_semester_start = self.fall_semester_start + relativedelta(days=3)
        
        if self.convocation_day:
            if self.fall_semester_start < self.convocation_day:
                print("ERROR: Fall Semester start day must be after convocation day")
                return False
        
        # NEW CODE, return FALSE if fall semester doesn't start on a monday
        if self.inputs.monday_fall and self.fall_semester_start.weekday() != 0:
            print("ERROR: Fall Semester start day must be a monday")
            return False
        
        # Leave at least 4 AWD for grading before Christmas (HARD RULE?)
        christmas_date = self.us_holidays.get_named("Christmas Day")[0]
        cur_date = christmas_date
        day_cnt = 0
        while day_cnt < 4:
            cur_date = cur_date + relativedelta(days=-1)
            if cur_date.weekday() != 5 and cur_date.weekday() != 6:
                self.cal_dict[cur_date] = DayType.AWD
                day_cnt += 1
        
        # compute fall finals
        day_cnt = 0
        start_of_fall_finals = None
        if not self.inputs.monday_final:
            # we don't have to worry about starting finals on monday
            while day_cnt < 6: # 6 days of finals
                cur_date = cur_date + relativedelta(days=-1)
                if cur_date.weekday() != 6: # not sunday
                    self.cal_dict[cur_date] = DayType.FINALS
                    day_cnt += 1
            start_of_fall_finals = cur_date
        else:
            # we have to start the finals on a Monday, that means finals will end on Sat
            cur_date = cur_date + relativedelta(days=-1)
            # find end date first (we want a Sat)
            while cur_date.weekday() != 5:
                # set dates to AWD until we find our day
                if not is_weekend(cur_date):
                    self.cal_dict[cur_date] = DayType.AWD
                cur_date = cur_date + relativedelta(days=-1)
            # we found the day, set 6 days of finals
            while day_cnt < 6: # 6 days of finals
                if cur_date.weekday() != 6: # not sunday
                    self.cal_dict[cur_date] = DayType.FINALS
                    day_cnt += 1
                cur_date = cur_date + relativedelta(days=-1)
            start_of_fall_finals = cur_date + relativedelta(days=1)
            
        # Fill ID through start of Fall Finals
        fall_id_cnt = 0
        cur_date = self.fall_semester_start
        while cur_date < start_of_fall_finals:
            if self.cal_dict[cur_date] == DayType.NONE and (cur_date.weekday() != 6 and cur_date.weekday() != 5):
                self.cal_dict[cur_date] = DayType.ID
                fall_id_cnt += 1
                self.month_stats[date(cur_date.year, cur_date.month, 1)]["ID"] += 1
                self.calc_id_days('fall', cur_date)

            cur_date = cur_date + relativedelta(days=1)
        print(f"Fall IDs: {fall_id_cnt}")
        # goto end of winter session
        cur_date = self.winter_session_end
        cur_date = cur_date + relativedelta(days=1)
        
        if self.inputs.even:
            for key in self.day_id_count['fall'].keys():
                if self.day_id_count['fall'][key] < 14 or self.day_id_count['fall'][key] > 15:
                    print("ERROR: instructional for fall are not equal")
                    return False

        """ SPRING SEMESTER START DATE """
        # (must start on or after Jan 15, or 16 if leap year)
        is_leap_year = date(self.start_date.year+1, 1, 1).year % 4 == 0
        spring_start_date = date(self.start_date.year+1, 1, 15)
        if is_leap_year:
            spring_start_date = date(self.start_date.year+1, 1, 16)
        if self.inputs.MLK_spring:
            # set spring start date to after MLK
            spring_start_date = self.us_holidays.get_named("Martin Luther King Jr. Day")[1] + relativedelta(days=1)
        while cur_date < spring_start_date:
            # set days to start of spring semester as AWD -- TODO: check if correct
            if not is_weekend(cur_date) and self.cal_dict[cur_date] == DayType.NONE:
                self.cal_dict[cur_date] = DayType.AWD
            cur_date = cur_date + relativedelta(days=1)
        while is_weekend(cur_date) or self.cal_dict[cur_date] != DayType.NONE:
            # we need to keep incrementing the day pointer until we get to a valid start date for spring
            cur_date = cur_date + relativedelta(days=1)
        self.spring_semester_start = cur_date
        
        # If Spring semester start date is a friday, push to monday
        if self.spring_semester_start.weekday() == 4:
            self.spring_semester_start = self.spring_semester_start + relativedelta(days=3)

        # Fill ID through Spring Finals
        spring_id_cnt = 0
        min_remaining_ids = num_id_days - fall_id_cnt
        cur_date = self.spring_semester_start
        while spring_id_cnt < min_remaining_ids:
            if self.cal_dict[cur_date] == DayType.NONE and (cur_date.weekday() != 6 and cur_date.weekday() != 5):
                self.cal_dict[cur_date] = DayType.ID
                spring_id_cnt += 1
                self.month_stats[date(cur_date.year, cur_date.month, 1)]["ID"] += 1
                self.calc_id_days('spring', cur_date)
            cur_date = cur_date + relativedelta(days=1)
        # CHECK: spring end date must be May 31st or sooner (cur_date is now +1)
        if cur_date > date(cur_date.year, 6, 1):
            print("ERROR: Spring semester ended past May 31st")
            return False
        
        # This is the spring final exam start date
        spring_final_exam_start = cur_date 
        if spring_final_exam_start.weekday() == 6:
            spring_final_exam_start = spring_final_exam_start + relativedelta(days=1)
        remaining_id_buffer = 149 - num_id_days
        if self.inputs.monday_spring_final == True:
            while spring_final_exam_start.weekday() != 0:
                # TODO: any extra days will be marked as instructional days
                if not is_weekend(spring_final_exam_start) and remaining_id_buffer > 0:
                    self.cal_dict[spring_final_exam_start] = DayType.ID
                    remaining_id_buffer -= 1
                    spring_id_cnt += 1
                    self.month_stats[date(cur_date.year, cur_date.month, 1)]["ID"] += 1
                    self.calc_id_days('spring', cur_date)
                spring_final_exam_start = spring_final_exam_start + relativedelta(days=1)
        print(f"Spring IDs: {spring_id_cnt}")

        if self.inputs.even:
            for key in self.day_id_count['spring'].keys():
                if self.day_id_count['spring'][key] < 14 or self.day_id_count['spring'][key] > 15:
                    print("ERROR: instructional for spring are not equal")
                    return False

        # FILL IN SPRING FINAL EXAMS HERE
        day_cnt = 0
        cur_date = spring_final_exam_start
        while day_cnt < 6:
            # If the day is not a Sunday
            if cur_date.weekday() != 6:
                self.cal_dict[cur_date] = DayType.FINALS
                day_cnt += 1
            cur_date = cur_date + relativedelta(days=1)
        
        # Calculate commencment start date
        while self.commencement_start == None:
            if not is_weekend(cur_date):
                if self.inputs.non_monday_commencement:
                    if cur_date.weekday() == 1:
                        self.commencement_start = cur_date
                else:
                    self.commencement_start = cur_date
            cur_date = cur_date + relativedelta(days=1)

        cur_date = self.commencement_start

        day_cnt = 0
        while day_cnt < 4: 
            if not is_weekend(cur_date):
                self.cal_dict[cur_date] = DayType.COMMENCEMENT
                day_cnt += 1
            cur_date = cur_date + relativedelta(days=1)

        self.commencement_end = cur_date + relativedelta(days=-1)

        self.num_id = fall_id_cnt + spring_id_cnt
        # #CHECK: commencement goes into summer session
        # cur_date = cur_date + relativedelta(days=-1)
        # if cur_date >= self.summer_session_start:
        #     print("ERROR: commencement overran summer session start date")
        #     return False
        return True
    
    def compute_spring_break(self, combine_cc_day=True) -> bool:
        """ Calculates spring break and ensures Cesar Chavez Day is correctly assigned """
        cesar_date = None

        # Get Cesar Chavez Day, if it's a weekend, get the observed date
        for cd in self.us_holidays.get_named("Cesar Chavez Day"):
            if cd.year == (self.start_date.year + 1):
                cesar_date = cd
                if is_weekend(cesar_date):
                    if cesar_date.weekday() == 5:  # Saturday
                        cesar_date = cesar_date + relativedelta(days=2)  # Move to Monday
                    elif cesar_date.weekday() == 6:  # Sunday
                        cesar_date = cesar_date + relativedelta(days=-2)  # Move to Friday
                    print(f"Cesar Chavez Day falls on a weekend. Observing it on {cesar_date}.")
                break  # Ensure we use the first instance found for the correct year

        # If no Cesar Chavez Day is found, raise an error (instead of using a fallback) to catch the issue
        if cesar_date is None:
            raise ValueError(f"ERROR: Cesar Chavez Day not found for year {self.start_date.year + 1}. This should not happen.")

        if combine_cc_day:
            # Cesar Chavez day is always March 31. So make it part of spring break.
            spring_break_start = get_monday(cesar_date)  # Get the Monday of the week that Cesar Chavez falls in
            cur_date = spring_break_start
            for i in range(0, 5):
                if cur_date != cesar_date:
                    self.cal_dict[cur_date] = DayType.NO_CLASS_CAMPUS_OPEN
                cur_date = cur_date + relativedelta(days=1)
        else:
            # Put spring break before Cesar Chavez Day
            easter_monday_following_year = self.us_holidays.get_named("Easter Monday")[1]
            spring_break_start = easter_monday_following_year + relativedelta(days=-7)
            spring_break_end = easter_monday_following_year + relativedelta(days=-3)
            if spring_break_start <= cesar_date <= spring_break_end:
                spring_break_start = spring_break_start + relativedelta(weeks=-1)  # Move spring break up one week
            for i in range(0, 5):
                self.cal_dict[spring_break_start + relativedelta(days=i)] = DayType.NO_CLASS_CAMPUS_OPEN

        return True

    def compute_winter_session(self, winter_sess_len = 12) -> bool:
        """ Calculates Winter and Summer Session """
        # Calculate Winter Session, starts after New Years
        # 12 days min, 15 days maximum
        New_Years = date(self.start_date.year+1, 1, 1)
        wnt_cnt = 1
        cur_date = New_Years 
        self.winter_session_start = cur_date + relativedelta(days=1)
        if self.inputs.limit_winter_session:
            winter_sess_len = 10
            self.winter_session_id = winter_sess_len
        while (wnt_cnt <= winter_sess_len):
            cur_date = cur_date + relativedelta(days=1)
            if (not is_weekend(cur_date)) and self.cal_dict[cur_date] == DayType.NONE:
                self.cal_dict[cur_date] = DayType.WINTER_SESSION
                wnt_cnt += 1
                self.winter_session_id += 1
                self.month_stats[date(cur_date.year, cur_date.month, 1)]["WIN"] += 1
        self.winter_session_end = cur_date
        return True
        
        # TODO - Might move this to ID()

    def compute_summer_session(self) -> bool:
        if self.inputs.summer_sessession_start:
            self.summer_session_start = self.us_holidays.get_named("Memorial Day")[1]
        else:
            self.summer_session_start = self.commencement_start + relativedelta(days=4)
        self.summer_session_start = self.summer_session_start + relativedelta(days=1)

        # Check if summer start date is Friday or Weekend
        if self.summer_session_start.weekday() >= 4:
            skip_days = 7 - self.summer_session_start.weekday()
            self.summer_session_start = self.summer_session_start + relativedelta(days=skip_days)

        # Check if Holiday
        if self.cal_dict.get(self.summer_session_start, DayType.NONE) == DayType.HOLIDAY:
            self.summer_session_start = self.summer_session_start + relativedelta(days=1)

        # Populate Calendar with Summer Session Days for 12 weeks 
        cur_date = self.summer_session_start
        summer_session_end = self.summer_session_start + timedelta(weeks=11) + timedelta(days=(6 - self.summer_session_start.weekday()))
        while cur_date <= summer_session_end:
            if (not is_weekend(cur_date)) and self.cal_dict.get(cur_date, DayType.NONE) == DayType.NONE:
                self.cal_dict[cur_date] = DayType.SUMMER_SESSION
                self.summer_session_id += 1
                self.month_stats[date(cur_date.year, cur_date.month, 1)]["SUM"] += 1

            # Move to the next day
            cur_date += timedelta(days=1)

        return True

    
    def setup_calendar(self):
        """Initialize calendar and setup permanent holidays, events, and special days"""

        # Reset the months list and set up other necessary data
        self.reset()

        # Initialize event lists inside setup_calendar
        self.awd_dates_list = []  # Populate with AWD event dates
        self.id_dates_list = []  # Populate with Instructional Day event dates
        self.finals_dates_list = []  # Populate with Final exam dates
        self.commencement_dates_list = []  # Populate with Commencement event dates
        self.no_class_campus_open_dates_list = []  # Populate with 'No Class, Campus Open' dates
        self.summer_session_dates_list = []  # Populate with Summer session dates
        self.winter_session_dates_list = []  # Populate with Winter session dates
        self.holiday_dates_list = []  # Populate with Holidays
        self.void_dates_list = []  # Populate with Void or inactive dates

        # Set up CalMonth objects for each month and store them in self.months
        cur_date = self.start_date
        for _ in range(12):  # Generate 12 months of calendar starting from self.start_date
            cal_month = CalMonth(cur_date.year, cur_date.month, self.font, self.small_font, self.small_font_bold)
            self.months.append(cal_month)
            cur_date = cur_date + relativedelta(months=1)

        # Populate the calendar with permanent holidays
        cur_date = self.start_date
        end_date = self.start_date + relativedelta(years=1)

        while cur_date < end_date:
            # Ensure all dates are added to cal_dict, initializing them as NONE by default
            self.cal_dict[cur_date] = DayType.NONE

            # Check if cur_date is a holiday using the self.us_holidays list
            if cur_date in self.us_holidays:
                # Check if the holiday is in your predefined list of holidays (e.g., Thanksgiving, Christmas, etc.)
                for holiday_name in self.holiday_list:
                    if holiday_name in self.us_holidays.get(cur_date):
                        self.cal_dict[cur_date] = DayType.HOLIDAY
                        break

            # Move to the next day
            cur_date = cur_date + relativedelta(days=1)

        # Handle special events like Thanksgiving week off if extended fall is selected
        if self.inputs.extended_fall:
            thanksgiving_day = self.us_holidays.get_named("Thanksgiving")[0]
            for i in range(1, 4):  # The three days before Thanksgiving
                self.cal_dict[thanksgiving_day - relativedelta(days=i)] = DayType.NO_CLASS_CAMPUS_OPEN

        # Handle the days from Christmas (Dec 26) to New Year's (Jan 1) as VOID days
        day_after_xmas = date(self.start_date.year, 12, 26)
        new_year = date(self.start_date.year + 1, 1, 1)
        cur_date = day_after_xmas
        while cur_date <= new_year:
            self.cal_dict[cur_date] = DayType.VOID
            cur_date = cur_date + relativedelta(days=1)

        # If there are additional AWD, ID, or Convocation events, populate them here
        self.populate_event_days()

    def populate_event_days(self):
        """Populate AWD, Convocation, ID, Finals, and other event days in the calendar"""

        # Example: Add AWD (Alternative Work Days) event days
        for awd_day in self.awd_dates_list:
            self.cal_dict[awd_day] = DayType.AWD
            print(f"AWD day populated: {awd_day} -> {DayType.AWD}")

        # Example: Add Instructional Days (ID) event days
        for id_day in self.id_dates_list:
            self.cal_dict[id_day] = DayType.ID
            print(f"ID day populated: {id_day} -> {DayType.ID}")

        # Example: Add Convocation Day
        if self.convocation_day:
            self.cal_dict[self.convocation_day] = DayType.CONVOCATION
            print(f"Convocation day populated: {self.convocation_day} -> {DayType.CONVOCATION}")
        
        # Example: Add Finals days
        for finals_day in self.finals_dates_list:
            self.cal_dict[finals_day] = DayType.FINALS
            print(f"Finals day populated: {finals_day} -> {DayType.FINALS}")
        
        # Example: Add Commencement days (for graduation events)
        for commencement_day in self.commencement_dates_list:
            self.cal_dict[commencement_day] = DayType.COMMENCEMENT
            print(f"Commencement day populated: {commencement_day} -> {DayType.COMMENCEMENT}")
        
        # Example: No Class but Campus Open days (typically holidays where staff might work, but classes aren't in session)
        for no_class_day in self.no_class_campus_open_dates_list:
            self.cal_dict[no_class_day] = DayType.NO_CLASS_CAMPUS_OPEN
            print(f"No Class/Campus Open day populated: {no_class_day} -> {DayType.NO_CLASS_CAMPUS_OPEN}")
        
        # Example: Add Summer Session days
        for summer_session_day in self.summer_session_dates_list:
            self.cal_dict[summer_session_day] = DayType.SUMMER_SESSION
            print(f"Summer Session day populated: {summer_session_day} -> {DayType.SUMMER_SESSION}")
        
        # Example: Add Winter Session days
        for winter_session_day in self.winter_session_dates_list:
            self.cal_dict[winter_session_day] = DayType.WINTER_SESSION
            print(f"Winter Session day populated: {winter_session_day} -> {DayType.WINTER_SESSION}")

        # Example: Add other holidays or custom events
        for holiday_date in self.holiday_dates_list:
            self.cal_dict[holiday_date] = DayType.HOLIDAY
            print(f"Holiday populated: {holiday_date} -> {DayType.HOLIDAY}")

        # If there are any VOID days (days that are inactive or unimportant in the calendar, e.g., non-working days in a session):
        for void_day in self.void_dates_list:
            self.cal_dict[void_day] = DayType.VOID
            print(f"VOID day populated: {void_day} -> {DayType.VOID}")


    def draw(self, calendar : list[CalMonth], m_width=350, m_height=350) -> Image:
        # Create a blank canvas (resulting image)
        width, height = 5 * m_width, 4 * m_height + 200  # Size of the resulting image 
        result_image = Image.new("RGB", (width, height), (255, 255, 255))
        months_list = []

        # Load and resize multiple PIL images (you can replace these with your own images)
        images = []
        j = 0
        for month in calendar:
            image = month.draw(m_width)
            images.append(image)
            months_list.append(month.get_abbr())

        # Define the grid layout (5x3)
        grid_size = (5, 3)

        # Paste each image onto the canvas at the specified positions
        for i, image in enumerate(images):
            row = i // grid_size[0]
            col = i % grid_size[0]
            position = (col * m_width, row * m_height + 100)
            result_image.paste(image, position)
        
        awd_month_fall = []
        id_month_fall = []

        draw = ImageDraw.Draw(result_image)
        draw.text((1100,900), f"Academic Work Days = {self.num_awd}\nInstructional Days = {self.num_id}\nWinter = {self.winter_session_id}\nSummer = {self.summer_session_id}", font=self.font, fill="black")
        
        # Populate ID and AWD List with the number of each day type per month
        cur_date = date(self.start_date.year, self.start_date.month, 1)
        while cur_date < date(calendar[10].year, calendar[10].month, 1):
            id_month_fall.append(self.month_stats[cur_date]["ID"])
            awd_month_fall.append(self.month_stats[cur_date]["AWD"])
            cur_date = cur_date + relativedelta(months=1)
        
        # Create Month_Table and paste it to result img
        im = self.create_months_table(months_list[:10], awd_month_fall, id_month_fall)
        box = (0, 3*m_height+125)
        # box = (1100, 2*m_height+150)
        result_image.paste(im, box)

        # Create Day_Table and paste it to result img
        awd_day_fall =  list(self.day_awd_count['fall'].values()) + list(self.day_awd_count['spring'].values()) 
        id_day_fall = list(self.day_id_count['fall'].values()) + [0] + list(self.day_id_count['spring'].values()) + [0]
        im = self.create_days_table(awd_day_fall, id_day_fall)
        box = (650, 3*m_height+125)
        result_image.paste(im, box)

        # reference color_legend and display it
        im = self.create_table_key(self.legend_data)#self.get_legend_table()
        result_image.paste(im, [width//2-500, 0]) #TODO: Fit more evenly

        return result_image        

    def create_table_key(self, legend_data, cell_height=30, padding=5):
        # Compute total width based on text length and padding
        total_width = sum([ImageDraw.Draw(Image.new('RGB', (1, 1))).textsize(text, self.small_font)[0] + padding*3 + cell_height for text in legend_data.keys()]) + padding
        # Create a new image with a white background
        img_width = total_width
        img_height = cell_height
        img = Image.new('RGB', (img_width, img_height), 'white')
        draw = ImageDraw.Draw(img)

        # Set font
        #font = ImageFont.truetype(font_path, font_size)

        # Draw each colored rectangle and label
        x_offset = 0
        for label, color in legend_data.items():
            # Draw rectangle
            draw.rectangle([(x_offset, padding), (x_offset + cell_height - 2*padding, img_height - padding)], fill=color)
        
            # Draw border around rectangle
            draw.rectangle([(x_offset, padding), (x_offset + cell_height - 2*padding, img_height - padding)], outline='black', width=1)
            x_offset += cell_height

            # Draw label
            text_width, _ = draw.textsize(label, font=self.small_font)
            draw.text((x_offset, (cell_height - self.small_font_size) // 2), label, font=self.small_font, fill='black')
            x_offset += text_width + padding*2

        return img

    def create_months_table(self, months: list, awd: list, id: list, table_width: int = 550, cell_height: int = 40, font_size: int = 16) -> bytes:
        '''Creates''' 
        # Data for the table
        header = ['Fall', 'AWD', 'ID', 'Spring', 'AWD', 'ID']
        
        #
        months_fall = months[0:5]
        months_spring = months[5:10]
        awd_fall = awd[0:5]
        awd_spring = awd[5:10]
        id_fall = id[0:5]
        id_spring = id[5:10]

        # Final output row
        months_fall.append("Total")
        awd_fall.append(sum(awd_fall))
        id_fall.append(sum(id_fall))

        months_spring.append("Total")
        awd_spring.append(sum(awd_spring))
        id_spring.append(sum(id_spring))

        # Create the table using plotly.graph_objects
        fig = go.Figure(data=[go.Table(
            header=dict(values=header, line = dict(color='black', width=1), height = cell_height, font = dict(size = font_size)),
            cells=dict(values=[months_fall,awd_fall,id_fall, months_spring, awd_spring, id_spring], 
                height = cell_height,

            fill_color=[
                ['white'] * 6,  # Month column background color
                [self.legend_data["AWD"]] * 6,   # AWD column background color
                [self.legend_data["ID"]] * 6,    # ID column background color

                ['white'] * 6,  # Month column background color
                [self.legend_data["AWD"]] * 6,   # AWD column background color
                [self.legend_data["ID"]]* 6,    # ID column background color
            ],

            line = dict(color='black', width=1),
            )
        )])
        # Define size of Overall Image
        fig.update_layout(
            autosize=False,
            width= table_width,
            height= 550,
            margin=dict(l=0, r=5, t=0, b=0)  # Add this line
        )
        fig.update_traces(cells_font=dict(size = font_size))

        # Show the table
        bytes = BytesIO(fig.to_image(format='png'))
        im = Image.open(bytes)
        return im
    
    def dict_hash(self, dictionary: Dict[str, Any]) -> str:
        """MD5 hash of a dictionary."""
        dhash = hashlib.md5()
        # We need to sort arguments so {'a': 1, 'b': 2} is
        # the same as {'b': 2, 'a': 1}
        convert_dict = {
            "fall_semester_start": self.fall_semester_start.strftime("%m/%d/%Y"),
            "spring_semester_start": self.spring_semester_start.strftime("%m/%d/%Y"),
            "summer_session_start": self.summer_session_start.strftime("%m/%d/%Y"),
            "winter_session_start": self.winter_session_start.strftime("%m/%d/%Y"),
            "winter_session_end": self.winter_session_end.strftime("%m/%d/%Y"),
            # "pre_fall_semester_start": self.pre_fall_semester_start.strftime("%m/%d/%Y"),
            "convocation_day": self.convocation_day.strftime("%m/%d/%Y"),
            "commencement_start": self.commencement_start.strftime("%m/%d/%Y"),
            "summer_session_id": self.summer_session_id,
            "winter_session_id": self.winter_session_id,
            "num_awd": self.num_awd,
            "num_id": self.num_id
                                                                  
        }
        # for key in dictionary.keys():
        #     keystr = key.strftime("%m/%d/%Y")
        #     convert_dict[keystr] = dictionary[key].value
        
        encoded = json.dumps(convert_dict, sort_keys=True).encode()
        dhash.update(encoded)
        return dhash.hexdigest()
    
    def create_days_table(self, awd: list, id: list, table_width: int = 550, cell_height: int = 40, font_size: int = 16) -> bytes:
        '''Creates''' 
        # Data for the table
        header = ['Fall', 'AWD', 'ID', 'Spring', 'AWD', 'ID']
        
        #
        days = ['M', 'T', 'W', 'R', 'F', 'Sa', 'Total']
        awd_fall = awd[0:6]
        awd_spring = awd[6:12]
        id_fall = id[0:6]
        id_spring = id[6:12]

        # Final output row
        awd_fall.append(sum(awd_fall))
        id_fall.append(sum(id_fall))

        awd_spring.append(sum(awd_spring))
        id_spring.append(sum(id_spring))

        # Create the table using plotly.graph_objects
        fig = go.Figure(data=[go.Table(
            header=dict(values=header, line = dict(color='black', width=1), height = cell_height, font = dict(size = font_size)),
            cells=dict(values=[days,awd_fall,id_fall, days, awd_spring, id_spring], 
                height = cell_height,

            fill_color=[
                ['white'] * 7,  # Month column background color
                [self.legend_data["AWD"]] * 7,   # AWD column background color
                [self.legend_data["ID"]] * 7,    # ID column background color

                ['white'] * 7,  # Month column background color
                [self.legend_data["AWD"]] * 7,   # AWD column background color
                [self.legend_data["ID"]] * 7,    # ID column background color
            ],

            line = dict(color='black', width=1),
            )
        )])
        # Define size of Overall Image
        fig.update_layout(
            autosize=False,
            width= table_width,
            height= 550,
            margin=dict(l=0, r=5, t=0, b=0)  # Add this line
        )
        fig.update_traces(cells_font=dict(size = font_size))

        # Show the table
        bytes = BytesIO(fig.to_image(format='png'))
        im = Image.open(bytes)
        return im
    
    def get_legend_table(self):
        im = Image.open('test_legend.png')
        return im
    
    def calc_id_days(self, semester: str, the_date: date):
        self.day_id_count[semester][Day(the_date.weekday())] += 1

    def calc_awd_days(self, the_date: date):
        if the_date < self.spring_semester_start:
            self.day_awd_count['fall'][Day(the_date.weekday())] += 1
        else:
            self.day_awd_count['spring'][Day(the_date.weekday())] += 1
    
    def get_day_type(self, year, month, day):
        """Return the day type for a specific date"""
        the_date = date(year, month, day)

        # Check if the date exists in the calendar dictionary
        if the_date in self.cal_dict:
            return self.cal_dict[the_date]  # Return the DayType enum
        else:
            return DayType.NONE  # Default to DayType.NONE if the date isn't in the dictionary



def add_weekdays(start_date : date, num_weekdays: int) -> date:
    current_date = start_date
    while num_weekdays > 0:
        # Increment the current date by one day
        current_date += timedelta(days=1)
        # Check if the current date is a weekday (0 = Monday, 4 = Friday)
        if current_date.weekday() < 5:
            num_weekdays -= 1
    return current_date

def is_weekend(the_date : date) -> bool:
    if the_date.weekday() < 5:
        return False
    return True

def get_monday(input_date):
    # Check if the input_date is already a Monday
    if input_date.weekday() == 0:  # Monday is represented as 0
        return input_date
    else:
        # Calculate the number of days to subtract to get to the previous Monday
        days_until_monday = input_date.weekday()
        monday_date = input_date - timedelta(days=days_until_monday)
        return monday_date