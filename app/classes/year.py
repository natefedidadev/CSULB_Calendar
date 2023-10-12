import calendar
from PIL import Image, ImageDraw, ImageFont
from .month import DayType, Day, CalMonth
import holidays
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from io import BytesIO
from enum import Enum
import multiprocessing as mp

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

class CalYear:
    
    def __init__(self, start_date : date, font_path = "fonts/OpenSans-Regular.ttf",font_path_bold = "fonts/OpenSans-Bold.ttf"):
        self.legend_data = {
            "None": "#FFFFFF",
            "AWD": "#F5A623",
            "ID": "#6DC7BE",
            "Convocation": "#50E3C2",
            "Finals": "#4A90E2",
            "No Class, Campus Open": "#B8E986",
            "Commencement": "#BD10E0",
            "Summer Session": "#9013FE",
            "Winter Session": "#F8E71C"
        }
        # TODO: look into cesar chavez day observed
        self.holiday_list = ['Martin Luther King Jr. Day', 'Labor Day', 'Thanksgiving', 'Day After Thanksgiving', 'New Year\'s Day', 'New Year\'s Day (Observed)', 'Independence Day', 'Independence Day (Observed)', 'Cesar Chavez Day', 'Cesar Chavez Day (Observed)', 'Veterans Day', 'Veterans Day (Observed)', 'Christmas Day (Observed)']
        self.font_size = 22
        self.small_font_size = 18
        self.font = ImageFont.truetype(font_path_bold, self.font_size)
        self.small_font = ImageFont.truetype(font_path, self.small_font_size)
        self.small_font_bold = ImageFont.truetype(font_path_bold, self.small_font_size)
        self.cal_dict = {}
        self.holiday_days = {}
        self.us_holidays = holidays.country_holidays('US') + holidays.country_holidays('US','CA') + holidays.country_holidays('US','VI')
        self.start_date = start_date
        self.setup_calendar()

    
    async def gen_schedule(self):
        # 170 <= Acadmeic Work Days (AWD) <= 180
        # 145 <= Instructional Days (ID) <= 149
        # Avoid starting a semester on a Friday.
                 
        # clear current calendar list
        current_calendar = []

        # Calc semester start day
        sem_start_date = self.start_date
        if self.start_date.weekday() == 4: # Friday
            # Calculate the timedelta to add to the input_date to get to the next Monday
            days_until_monday = (7 - self.start_date.weekday()) % 7
            sem_start_date = self.start_date + timedelta(days=days_until_monday)   
        
        # Convocation Date
        days_until_friday = (4 - sem_start_date.weekday() + 7) % 7
        convocation = sem_start_date + timedelta(days=days_until_friday)
        
        self.compute_holidays()
        self.compute_awd()

        # Build calendar year starting at start date
        for i in range(13):
            cur_date = self.start_date + relativedelta(months=i)
            cmonth = CalMonth(cur_date.year,cur_date.month, self.font, self.small_font, self.small_font_bold)

            if cmonth.month == self.start_date.month:
                pass
                # AWD until Convocation calculator
                # if cur_date.month == start_date.month and cur_date.year == start_date.year:
                #     for j in range(convocation.day - sem_start_date.day + 1):
                #         cmonth.set_day_bgcolor(sem_start_date.day+j, self.legend_data["AWD"])
                #     cmonth.set_day_bold(convocation.day)

            current_calendar.append(cmonth)
        
        # Color the days based on type
        for i in range(13):
            cur_day = date(current_calendar[i].year, current_calendar[i].month, 1)
            end_day = cur_day + relativedelta(months=1)
            while cur_day < end_day:
                if cur_day in self.cal_dict and DayType.AWD == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bgcolor(cur_day.day, self.legend_data["AWD"])
                elif cur_day in self.cal_dict and DayType.NO_CLASS_CAMPUS_OPEN == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bgcolor(cur_day.day, self.legend_data["No Class, Campus Open"])
                elif cur_day in self.cal_dict and DayType.WINTER_SESSION == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bgcolor(cur_day.day, self.legend_data["Winter Session"])
                elif cur_day in self.cal_dict and DayType.FINALS == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bgcolor(cur_day.day, self.legend_data["Finals"])
                elif cur_day in self.cal_dict and DayType.HOLIDAY == self.cal_dict[cur_day]:
                    current_calendar[i].set_day_bold(cur_day.day)
                cur_day = cur_day + relativedelta(days=1)

        return await self.adraw(current_calendar)
        # compute AWD

    #TODO: Optimize / change this function
    def compute_awd(self):
        """ AWD must be between 170 - 180 """
        cur_date = self.start_date
        awd_cnt = 0
        christmas = date(self.start_date.year, 12, 25) # self.us_holidays.get_named("Christmas Day (observed)")[2]

        # Calculate the date two weeks before Christmas
        two_weeks_before_christmas = christmas - timedelta(weeks=1)

        # weekday() returns 0 for Monday, 1 for Tuesday, and so on
        days_to_go_back = two_weeks_before_christmas.weekday()
        nearest_monday = two_weeks_before_christmas - timedelta(days=days_to_go_back)
        
        # For Fall Semester, While the current date is before Christmas
        while cur_date < date(self.start_date.year+1, self.start_date.month+1, self.start_date.day):
            # if current day isn't a Sunday, Saturday, or is a US Holiday
            if (cur_date.weekday() != 6 and cur_date.weekday() != 5) and self.cal_dict[cur_date] == DayType.NONE and awd_cnt <= 180:
                if cur_date >= nearest_monday and cur_date < nearest_monday + relativedelta(days=7):
                    self.cal_dict[cur_date] = DayType.FINALS
                else: 
                    self.cal_dict[cur_date] = DayType.AWD
                awd_cnt+=1
            cur_date = cur_date + relativedelta(days=1)
    
    def compute_holidays(self, winter_sess_len = 14, summer_sess_len = 15):
        """ Calculates spring break """
        # Calculate Spring Break (5 consecutive days w/o classes) - LBCC week preceeding easter
        easter_monday_following_year = self.us_holidays.get_named("Easter Monday")[1]
        for i in range(3,8):
            self.cal_dict[easter_monday_following_year + relativedelta(days=-i)] = DayType.NO_CLASS_CAMPUS_OPEN
        
        # Calculate Winter Session, starts after New Years
        New_Years = date(self.start_date.year+1, 1, 1)
        for i in range(winter_sess_len):
            cur_date = New_Years + relativedelta(days=i)
            if (cur_date.weekday() != 6 and cur_date.weekday() != 5):
                self.cal_dict[cur_date] = DayType.WINTER_SESSION

        # Calculate Summer Session, starts the first work day in June

            
    def setup_calendar(self):
        """ Initialize calendar and setup permanent holidays """
        cur_date = self.start_date
        # For Fall Semester, While the current date is before Christmas
        while cur_date < date(self.start_date.year+1, self.start_date.month+1, self.start_date.day):
            day = self.us_holidays.get(cur_date)
            if day in self.holiday_list:
                self.cal_dict[cur_date] = DayType.HOLIDAY
            else:
                self.cal_dict[cur_date] = DayType.NONE
                
            cur_date = cur_date + relativedelta(days=1)
        
        # Thanksgiving week off
        for i in range(1,4):
            self.cal_dict[self.us_holidays.get_named("Thanksgiving")[0] + relativedelta(days=-i)] = DayType.NO_CLASS_CAMPUS_OPEN

    async def adraw(self, calendar : list[CalMonth], m_width=350, m_height=350):
        # Create a blank canvas (resulting image)
        width, height = 5 * m_width, 4 * m_height + 200  # Size of the resulting image 
        result_image = Image.new("RGB", (width, height), (255, 255, 255))
        months_list = []

        # Load and resize multiple PIL images (you can replace these with your own images)
        images = []
        j = 0
        for month in calendar:
            image = await month.adraw(m_width)
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

        im = Image.open("./table.png")
        awd_month_fall = [12, 21, 22, 19, 19, 42, 41, 32, 49, 39]
        id_month_fall = [6, 21, 22, 16, 9, 45, 23, 21, 29, 26]
        
        # Create Month_Table and paste it to result img
        im = await self.acreate_months_table(months_list[:10], awd_month_fall, id_month_fall)
        box = (0, 3*m_height+125)
        result_image.paste(im, box)

        # Create Day_Table and paste it to result img
        awd_day_fall = [12, 21, 22, 19, 19, 42, 41, 32, 49, 39, 12, 14]
        id_day_fall = [6, 21, 22, 16, 9, 45, 23, 21, 29, 26, 12, 14]
        im = await self.acreate_days_table(awd_day_fall, id_day_fall)
        box = (650, 3*m_height+125)
        result_image.paste(im, box)

        # reference color_legend and display it
        im = await self.acreate_table_key(self.legend_data)#self.get_legend_table()
        result_image.paste(im, [width//2-500, 0]) #TODO: Fit more evenly

        return result_image        

    async def acreate_table_key(self, legend_data, cell_height=30, padding=5):
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

    async def acreate_months_table(self, months: list, awd: list, id: list, table_width: int = 550, cell_height: int = 40, font_size: int = 16) -> bytes:
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
    
    async def acreate_days_table(self, awd: list, id: list, table_width: int = 550, cell_height: int = 40, font_size: int = 16) -> bytes:
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
              