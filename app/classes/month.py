import calendar
from PIL import Image, ImageDraw, ImageFont

from enum import Enum

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

class Day:
    type : DayType = DayType.NONE
    num : int  = 0

class CalMonth:
    def __init__(self, year, month):
        self.day_colors = {}  # Format: {day: color, ...}
        self.day_bgcolors = {}  # Format: {day: bgcolor, ...}
        calendar.setfirstweekday(calendar.SUNDAY)
        self.cal = calendar.monthcalendar(year,month)
        self.month = month
        self.year = year
        
    def set_day_color(self, day, color):
        """Set the text color for a specific day."""
        self.day_colors[day] = color

    def set_day_bgcolor(self, day, bgcolor):
        """Set the background color for a specific day."""
        self.day_bgcolors[day] = bgcolor
    
    def get_title(self)->str:
        return calendar.month_name[self.month] + " " + str(self.year)
    
    def get_abbr(self)->str:
        """returns the abbreviation of the month name"""
        months_abbr = {
            1: "Jan",
            2: "Feb",
            3: "Mar",
            4: "Apr",
            5: "May",
            6: "Jun",
            7: "Jul",
            8: "Aug",
            9: "Sep",
            10: "Oct",
            11: "Nov",
            12: "Dec"
        }
        return months_abbr[self.month]

    def draw(self, width):
        aspect_ratio = 320 / 300  # based on previous image dimensions
        image_height = int(width / aspect_ratio) 
        scaled_height = 50 * (image_height / 200)
    
        day_names = list(calendar.day_abbr)[-1:] + list(calendar.day_abbr)[:-1]

        img = Image.new('RGB', (width, image_height), 'white')
        draw = ImageDraw.Draw(img)

        #font_path = "fonts/DejaVuSans.ttf"
        #font_path_bold = "fonts/DejaVuSans-Bold.ttf"
        font_path = "fonts/OpenSans-Regular.ttf"
        font_path_bold = "fonts/OpenSans-Bold.ttf"

        font = ImageFont.truetype(font_path_bold, int(22 * width / 350))
        small_font = ImageFont.truetype(font_path, int(18 * width / 350))

        title = self.get_title()
        title_bbox = draw.textbbox((0, 0), title, font=font)
        title_w = title_bbox[2] - title_bbox[0]
        title_h = title_bbox[3] - title_bbox[1]
        draw.text(((width - title_w) / 2 - 15, 5 * image_height / 200), title, font=font, fill="dimgray")

        col_width = width / 8
        for idx, day_name in enumerate(day_names):
            #color = "red" if idx == 0 or idx == 6 else "dimgray"
            color = "dimgray"
            draw.text((idx * col_width + 6, 25 * image_height / 150), day_name, font=small_font, fill=color)

        rows = 7
        row_height = (image_height - scaled_height) / rows
        for row_idx in range(rows):
            for col_idx, day in enumerate(self.cal[row_idx] if row_idx < len(self.cal) else [0]*7):
                day_color = self.day_colors.get(day, "red" if col_idx == 0 or col_idx == 6 else "black")
                bgcolor = self.day_bgcolors.get(day, "white")

                if day != 0:
                    day_str = str(day)
                    text_bbox = draw.textbbox((col_idx * col_width, scaled_height + row_idx * row_height), day_str, font=small_font)
                    text_w = text_bbox[2] - text_bbox[0]
                    text_h = text_bbox[3] - text_bbox[1]

                    x_text = col_idx * col_width + (col_width - text_w) / 2
                    y_text = scaled_height + row_idx * row_height + (row_height - text_h) / 2 - 5

                    draw.rectangle([col_idx * col_width+1, scaled_height + row_idx * row_height + 1, 
                                    (col_idx + 1) * col_width - 1, scaled_height + (row_idx + 1) * row_height - 1], fill=bgcolor)

                    draw.text((x_text, y_text), day_str, font=small_font, fill=day_color)
                if row_idx < 6:
                    draw.rectangle([col_idx * col_width + 1 , scaled_height + row_idx * row_height + 1,
                                (col_idx + 1) * col_width - 1, scaled_height + (row_idx + 1) * row_height - 1], width=1, outline="black")
                else:
                    # day_bbox = draw.textbbox((col_idx * col_width, scaled_height + row_idx * row_height), "summer = 22", font=small_font)
                    draw.rectangle([(1, scaled_height + 6 * row_height + 1), (7*col_width-1, scaled_height + 7 * row_height-1)], width=1, outline="black")
                    text_bbox = draw.textbbox((col_idx * col_width, scaled_height + row_idx * row_height), day_str, font=small_font)
                    text_w = text_bbox[2] - text_bbox[0]
                    text_h = text_bbox[3] - text_bbox[1]
                    draw.text((3*col_width-(text_w), scaled_height + row_idx * row_height+(0.5*text_h)), "summer = 22", font=small_font, fill="black")
        return img
        #img.save('calendar.png')