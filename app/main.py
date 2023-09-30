from fastapi import FastAPI
from pydantic import BaseModel
from calendar import Calendar, day_abbr as day_abbrs, month_name as month_names
from datetime import datetime, timedelta

import streamlit as st
import streamlit.components.v1 as components
from dateutil.relativedelta import relativedelta
from datetime import date
import holidays
import pandas as pd
import uvicorn
from .classes.month import CalMonth
from fastapi.responses import StreamingResponse
import io
from PIL import Image, ImageDraw, ImageFont


# https://www.geeksforgeeks.org/python-requests-tutorial/#

app = FastAPI()

class Month(BaseModel):
    month: int = 1
    day_colors : list | None = ['red','blue']

class Calendar_Input(BaseModel):
    month: int
    day : int 
    year: int


@app.post("/calendar/test")
async def test(req : Month):
    return {
                "message": "hello world",
                "month": month_dict[req.month],
                "day_colors": req.day_colors
            }


@app.post("/calendar/build_year")
def build_year(start_date : Calendar_Input):
    cmonth = CalMonth()
    # Create a blank canvas (resulting image)
    width, height = 5 * 350, 3 * 220  # Size of the resulting image TODO: make 350 & 200 into variables
    result_image = Image.new("RGB", (width, height), (255, 255, 255))
    

    # Load and resize multiple PIL images (you can replace these with your own images)
    images = []
    j = 0
    start_datetime = datetime(start_date.year, start_date.month,start_date.day) 
    for i in range(13):
        cur_date = start_datetime + relativedelta(months=i)
        if start_date.month+i <= 12:
            cmonth.set_day_bgcolor(1, "red")
            image = cmonth.draw(300,start_date.year,cur_date.month)
        else:
            image = cmonth.draw(300,start_date.year+1,cur_date.month)
        images.append(image)
        

    # Define the grid layout (5x3)
    grid_size = (5, 3)

    # Paste each image onto the canvas at the specified positions
    for i, image in enumerate(images):
        row = i // grid_size[0]
        col = i % grid_size[0]
        position = (col * 350, row * 220)
        result_image.paste(image, position)

    # Save or display the resulting image
    #return result_image
    # Save the PIL image to a BytesIO object
    img_bytes_io = io.BytesIO()
    result_image.save(img_bytes_io, format='PNG')
    
    # Rewind the BytesIO object to the start
    img_bytes_io.seek(0)
    
    # Return a StreamingResponse object
    return StreamingResponse(img_bytes_io, media_type="image/png")

###  { "color":"purple"}

month_dict= {
    1 : "Jan",
    2 : "Feb",
    3 : "March"
}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)