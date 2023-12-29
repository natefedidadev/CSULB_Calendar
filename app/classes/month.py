import calendar
from PIL import Image, ImageDraw, ImageFont
from datetime import date
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
    def __init__(self, year, month, font: ImageFont, small_font: ImageFont, small_font_bold: ImageFont):
        self.day_colors = {}  # Format: {day: color, ...}
        self.day_bgcolors = {}  # Format: {day: bgcolor, ...}
        self.note = ""
        calendar.setfirstweekday(calendar.SUNDAY)
        self.cal = calendar.monthcalendar(year,month)
        self.month = month
        self.year = year
        self.font = font
        self.small_font = small_font
        self.small_font_bold = small_font_bold
        self.aspect_ratio = 320 / 300
        self.day_bold = []
        self.day_bold_outline = []
        # self.awd_cnt = 0
        # self.id_cnt = 0

    def set_day_color(self, day : int, color):
        """ Set the text color for a specific day."""
        self.day_colors[day] = color

    def set_day_bgcolor(self, day: int, bgcolor):
        """ Set the background color for a specific day."""
        self.day_bgcolors[day] = bgcolor

    def set_day_bold_outline(self, day: int):
        """ Set the calendar outline for the day to be bold"""
        self.day_bold_outline.append(day)

    def set_day_bold(self, day: int):
        """ Set the day text to be bold """
        self.day_bold.append(day)
    
    def set_month_note(self, text : str):
        """ Append a note for the month """
        self.note = text
    
    def get_month(self) -> date:
        """ Return the first of the month as a date object"""
        return date(self.year, self.month, 1)

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

    def _get_text_dimensions(self, draw, text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def draw(self, width):
        image_height = int(width / self.aspect_ratio) 
        scaled_height = 50 * (image_height / 200)
    
        day_names = list(calendar.day_abbr)[-1:] + list(calendar.day_abbr)[:-1]

        img = Image.new('RGB', (width, image_height), 'white')
        draw = ImageDraw.Draw(img)

        title = self.get_title()
        title_bbox = draw.textbbox((0, 0), title, font=self.font)
        title_w = title_bbox[2] - title_bbox[0]
        #title_h = title_bbox[3] - title_bbox[1]
        title_coords = ((width - title_w) / 2 - 15, 5 * image_height / 200)
        draw.text(title_coords, title, font=self.font, fill="dimgray")

        col_width = width / 8
        col_width_values = [idx * col_width for idx in range(8)]

        for idx, day_name in enumerate(day_names):
            day_name_coords = (col_width_values[idx] + 6, 25 * image_height / 150)
            draw.text(day_name_coords, day_name, font=self.small_font, fill="dimgray")

        rows = 7
        row_height = (image_height - scaled_height) / rows
        row_height_values = [scaled_height + row_idx * row_height for row_idx in range(rows)]

        for row_idx, rh in enumerate(row_height_values):
            for col_idx, day in enumerate(self.cal[row_idx] if row_idx < len(self.cal) else [0] * 7):
                day_color = self.day_colors.get(day, "red" if col_idx in [0, 6] else "black")
                bgcolor = self.day_bgcolors.get(day, "white")
                
                if row_idx == 6:
                    bottom_edge = image_height - 1
                else:
                    bottom_edge = row_height_values[row_idx + 1] - 1
                rect_coords = [col_width_values[col_idx] + 1, rh + 1, col_width_values[col_idx + 1] - 1, bottom_edge]
                
                if day:
                    font = self.small_font
                    if day in self.day_bold:
                        font = self.small_font_bold
                    text_bbox = draw.textbbox((col_width_values[col_idx], rh), str(day), font=font)
                    text_w, text_h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

                    x_text = col_width_values[col_idx] + (col_width - text_w) / 2
                    y_text = rh + (row_height - text_h) / 2 - 5
                    draw.rectangle(rect_coords, fill=bgcolor)
                    draw.text((x_text, y_text), str(day), font=font, fill=day_color)
                if row_idx < 6:
                    width = 1
                    if day in self.day_bold_outline:
                        width = 4
                    draw.rectangle(rect_coords, width=width, outline="black")
                else:
                    # day_bbox = draw.textbbox((col_idx * col_width, scaled_height + row_idx * row_height), "summer = 22", font=small_font)
                    draw.rectangle([(1, scaled_height + 6 * row_height + 1), (7*col_width-1, scaled_height + 7 * row_height-1)], width=1, outline="black")
                    text_bbox = draw.textbbox(rect_coords, self.note, font=self.small_font)
                    text_w = text_bbox[2] - text_bbox[0]
                    text_h = text_bbox[3] - text_bbox[1]
                    draw.text((2*(col_width), scaled_height + row_idx * row_height+(0.5*text_h)), self.note, font=self.small_font, fill="black")
        return img
        #img.save('calendar.png')