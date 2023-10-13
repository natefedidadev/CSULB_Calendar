from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from .classes.month import CalMonth
from .classes.year import CalYear, Calendar_Input
from fastapi.responses import StreamingResponse
import io
from datetime import date

# https://www.geeksforgeeks.org/python-requests-tutorial/#

app = FastAPI()

class Month(BaseModel):
    month: int = 1
    day_colors : list | None = ['red','blue']

class Base_Input(BaseModel):
    month: int
    day : int 
    year: int
    



@app.post("/calendar/test")
async def testThree(req : Month):
    return {
                "message": "hello world",
                "day_colors": req.day_colors
            }

@app.post("/calendar/table")
async def testTwo(req : Month):
    year = CalYear()
    awd_fall = [12, 21, 22, 19, 19]
    id_fall = [6, 21, 22, 16, 9]
    months = ['Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    img = year.create_months_table(awd=awd_fall, id=id_fall, months=months)
    
    # Save the PIL image to a BytesIO object
    img_bytes_io = io.BytesIO()
    img.save(img_bytes_io, format='PNG')
    
    # Rewind the BytesIO object to the start
    img_bytes_io.seek(0)

    # Return a StreamingResponse object
    return StreamingResponse(img_bytes_io, media_type="image/png")

@app.post("/calendar/month")
async def testOne(req : Calendar_Input):
    cmonth = CalMonth(req.year, req.month)
    img = cmonth.draw(req.width)
    # Save the PIL image to a BytesIO object
    img_bytes_io = io.BytesIO()
    img.save(img_bytes_io, format='PNG')
    
    # Rewind the BytesIO object to the start
    img_bytes_io.seek(0)
    
    # Return a StreamingResponse object
    return StreamingResponse(img_bytes_io, media_type="image/png")

@app.post("/calendar/build_year")
async def build_year(req : Calendar_Input):    
    calyear = CalYear(req)
    result_image = await calyear.gen_schedule()
    
    # Save the PIL image to a BytesIO object
    img_bytes_io = io.BytesIO()
    result_image.save(img_bytes_io, format='PNG')
    
    # Rewind the BytesIO object to the start
    img_bytes_io.seek(0)
    
    # Return a StreamingResponse object
    return StreamingResponse(img_bytes_io, media_type="image/png")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)