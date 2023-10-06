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
    
    def draw(self, year, month, day, width):
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
                image = cmonth.draw(m_width)
            else:
                image = cmonth.draw(m_width)
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
        awd_fall = [12, 21, 22, 19, 19]
        id_fall = [6, 21, 22, 16, 9]
        
        # Create Table and display it
        byte_stream = BytesIO(self.create_plotly_table(months_list[:5], awd_fall, id_fall))
        im = Image.open(byte_stream)
        result_image.paste(im, [0, 3*m_height+200])

        # reference color_legend and display it
        im = self.get_legend_table()
        result_image.paste(im, [width//2-403, 0]) #TODO: Fit more evenly

        return result_image
    
    def create_plotly_table(self, months: list, awd: list, id: list) -> bytes:
        '''Creates''' 
        # Data for the table
        header = ['Fall', 'AWD', 'ID']
        # Final output row
        months.append("Total")
        awd.append(sum(awd))
        id.append(sum(id))

        # Create the table using plotly.graph_objects
        fig = go.Figure(data=[go.Table(
            header=dict(values=header, line = dict(color='black', width=1)),
            cells=dict(values=[
                months,
                awd,
                id,
            ],
            fill_color=[
                ['white'] * 6,  # Month column background color
                self.color_dict["AWD"] * 6,   # AWD column background color
                self.color_dict["ID"] * 6,    # ID column background color
            ],
            line = dict(color='black', width=1)
            )
        )])
        # Define size of image
        fig.update_layout(
            autosize=False,
            width=650,
            height=1250
        )

        # Show the table
        return fig.to_image(format='png')
    
    def get_legend_table(self):
        img = Image.open("test_legend.png")
        return img
              