import calendar
from PIL import Image, ImageDraw, ImageFont
from .month import DayType, Day, CalMonth
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from io import BytesIO

class CalYear:
    
    def __init__(self):
        self.color_dict = {
            'NONE': 'gray',
            'AWD': ['#CCECFF'],
            'CONVOCATION': 'green',
            'ID': ['#FFFFCC'],
            'FINALS': 'yellow',
            'NO_CLASS_CAMPUS_OPEN': 'orange',
            'COMMENCEMENT': 'purple',
            'SUMMER_SESSION': 'pink',
            'WINTER_SESSION': 'brown'
        }
            
        self.font_path = "fonts/OpenSans-Regular.ttf"
        self.font_path_bold = "fonts/OpenSans-Bold.ttf"   
    
    async def adraw(self, year, month, day, width):
        m_width = 350
        m_height = 350
        # Create a blank canvas (resulting image)
        width, height = 5 * m_width, 4 * m_height + 200  # Size of the resulting image 
        result_image = Image.new("RGB", (width, height), (255, 255, 255))
        months_list = []

        # Load and resize multiple PIL images (you can replace these with your own images)
        images = []
        j = 0
        start_datetime = datetime(year, month, day) 
        for i in range(13):
            cur_date = start_datetime + relativedelta(months=i)
            cmonth = CalMonth(year,cur_date.month)
            if month+i <= 12:
                cmonth.set_day_bgcolor(1, "yellow")
                image = await cmonth.adraw(m_width)
            else:
                image = await cmonth.adraw(m_width)
            images.append(image)
            months_list.append(cmonth.get_abbr())

        # Define the grid layout (5x3)
        grid_size = (5, 3)

        # Paste each image onto the canvas at the specified positions
        for i, image in enumerate(images):
            row = i // grid_size[0]
            col = i % grid_size[0]
            position = (col * m_width, row * m_height + 100)
            result_image.paste(image, position)

        # im = Image.open("./table.png")
        awd_month_fall = [12, 21, 22, 19, 19, 42, 41, 32, 49, 39]
        id_month_fall = [6, 21, 22, 16, 9, 45, 23, 21, 29, 26]
        
        # Create Month_Table and paste it to result img
        im = await self.acreate_months_table(months_list[:10], awd_month_fall, id_month_fall)
        box = (0, 3*m_height+100)
        result_image.paste(im, box)

        # Create Day_Table and paste it to result img
        awd_day_fall = [12, 21, 22, 19, 19, 42, 41, 32, 49, 39, 12, 14]
        id_day_fall = [6, 21, 22, 16, 9, 45, 23, 21, 29, 26, 12, 14]
        im = await self.acreate_days_table(awd_day_fall, id_day_fall)
        box = (650, 3*m_height+100)
        result_image.paste(im, box)

        # reference color_legend and display it
        im = self.get_legend_table()
        result_image.paste(im, [width//2-403, 0]) #TODO: Fit more evenly

        return result_image
    
    async def acreate_months_table(self, months: list, awd: list, id: list, table_width: int = 600, cell_height: int = 40, font_size: int = 16) -> bytes:
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
                self.color_dict["AWD"] * 6,   # AWD column background color
                self.color_dict["ID"] * 6,    # ID column background color

                ['white'] * 6,  # Month column background color
                self.color_dict["AWD"] * 6,   # AWD column background color
                self.color_dict["ID"] * 6,    # ID column background color
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
    
    async def acreate_days_table(self, awd: list, id: list, table_width: int = 600, cell_height: int = 40, font_size: int = 16) -> bytes:
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
                self.color_dict["AWD"] * 7,   # AWD column background color
                self.color_dict["ID"] * 7,    # ID column background color

                ['white'] * 7,  # Month column background color
                self.color_dict["AWD"] * 7,   # AWD column background color
                self.color_dict["ID"] * 7,    # ID column background color
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
              