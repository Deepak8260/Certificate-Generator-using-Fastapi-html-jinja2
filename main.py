from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_path
import os

app = FastAPI()

# Static + templates setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

GENERATED_DIR = "generated"
os.makedirs(GENERATED_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "certificate_url": None})


@app.post("/generate")
async def generate_certificate(name: str = Form(...)):
    template_pdf = "static/cert.pdf"

    # Convert first page of PDF template to image
    images = convert_from_path(template_pdf)
    image = images[0].convert("RGB")

    draw = ImageDraw.Draw(image)
    # Try to use a more elegant font, fallback to arial if not found
    try:
        font = ImageFont.truetype("BRUSHSCI.TTF", 120)  # Brush Script MT
    except:
        try:
            font = ImageFont.truetype("SCRIPTBL.TTF", 120)  # Script Bold
        except:
            font = ImageFont.truetype("arial.ttf", 100)  # Fallback with larger size

    # Center text
    W, H = image.size
    text = name.title()
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    position = ((W - w) / 2, (H / 2) - 50)  # Adjusted position to move slightly down

    # Draw the name
    draw.text(position, text, fill="black", font=font)

    # Save generated certificate image
    img_path = os.path.join(GENERATED_DIR, f"{name}_certificate.png")
    image.save(img_path)

    # Redirect directly to preview (like Drive)
    return RedirectResponse(url=f"/preview/{name}_certificate.png", status_code=303)


@app.get("/preview/{filename}")
async def preview_certificate(filename: str):
    """
    Direct image preview (like Google Drive). 
    Browser allows 'Print → Save as PDF' or 'Right-click → Save as...'
    """
    return FileResponse(f"generated/{filename}", media_type="image/png")
