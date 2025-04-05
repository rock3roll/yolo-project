import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from io import BytesIO
import yolov5
import numpy as np
import cv2
from PIL import Image
import shutil
from fastapi.middleware.cors import CORSMiddleware
import json
from pydantic import BaseModel 
from dotenv import load_dotenv
import requests
import random
from pymongo import MongoClient


load_dotenv()


HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
MONGO_URI = os.getenv('MONGO_URI')

DETECTION_RESULTS = {}  # Store detections
FEEDBACK_FILE = "feedback.json"

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Allows specified origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


# Load YOLOv5 model    keremberke/yolov5n-garbage
model = yolov5.load('turhancan97/yolov5-detect-trash-classification')
#model = yolov5.load('keremberke/yolov5s-garbage')

model.conf = 0.25  # Confidence threshold
model.iou = 0.45  # IoU threshold
model.agnostic = False  # NMS class-agnostic
model.multi_label = False  # NMS multiple labels per box

# Path to save uploaded images
UPLOAD_DIR = "uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # Save the uploaded file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process the image with YOLOv5
    image = Image.open(file_path).convert("RGB")
    img_cv = np.array(image)
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

    # Perform inference
    results = model(img_cv)

    # Extract predictions
    predictions = results.xyxy[0].cpu().numpy()
    prediction_data = []

    # Draw bounding boxes and prepare results
    for s_no,pred in enumerate(predictions, start = 1):
        x1, y1, x2, y2, conf, cls = pred
        label = f"{s_no}: {model.names[int(cls)]} {conf:.2f}"

        # Draw rectangle
        cv2.rectangle(img_cv, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
        cv2.putText(img_cv, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 255, 0), 2)
        
        class_name = model.names[int(pred[5])]
       
        prediction_data.append({
            "s_no": s_no, 
            "class": class_name,
            "recyclable": "Yes" if class_name in ["Plastic", "Paper", "Glass", "Cardboard"] else "No",
            "dry_wet": "Dry" if class_name != "e-waste" else "Wet",
            "disposal_info": "Recycle at designated centers" if class_name in ["plastic", "paper", "glass", "cardboard"] else "Handle with care"
        })
        DETECTION_RESULTS[s_no] = {"coords": [int(x1), int(y1), int(x2), int(y2)], "pred_class": class_name}
        

    # Save the processed image
    output_image_path = os.path.join(UPLOAD_DIR, f"processed_{file.filename}")
    cv2.imwrite(output_image_path, img_cv)
    DETECTION_RESULTS['image_path'] = output_image_path
    
    return {"image_url": f"/image/{os.path.basename(output_image_path)}", "predictions": prediction_data}

    # Convert predictions to the desired format (Table format)
    
''' for s_no, pred in enumerate(predictions, start = 1):
        class_name = model.names[int(pred[5])]
        prediction_data.append({
            "s_no": s_no, 
            "class": class_name,
            "recyclable": "Yes" if class_name in ["plastic", "paper", "glass", "cardboard"] else "No",
            "dry_wet": "Dry" if class_name != "e-waste" else "Wet",
            "disposal_info": "Recycle at designated centers" if class_name in ["plastic", "paper", "glass", "cardboard"] else "Handle with care"
        })'''


@app.get("/image/{filename}")
async def get_image(filename: str):
    return FileResponse(os.path.join(UPLOAD_DIR, filename))


class FeedbackRequest(BaseModel):
    s_no: int
    actual_class: str
    predicted_class: str

'''
@app.post("/submit-feedback/")
async def submit_feedback(feedback: FeedbackRequest):
    """Handles feedback submission and stores data in feedback.json."""
    
    # Ensure `s_no` exists in detection results
    if feedback.s_no not in DETECTION_RESULTS:
        raise HTTPException(status_code=400, detail="Invalid Detection ID (s_no)")

    # Prepare feedback entry
    feedback_entry = {
        "s_no": feedback.s_no,
        "bounding_box": DETECTION_RESULTS[feedback.s_no]["coords"],
        "actual_class": feedback.actual_class,
        "predicted_class": DETECTION_RESULTS[feedback.s_no]["pred_class"],
        "image_path": DETECTION_RESULTS["image_path"]
        
        
        
    }

    # Ensure feedback file exists
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w") as f:
            json.dump([], f)

    # Read existing feedback
    try:
        with open(FEEDBACK_FILE, "r") as f:
            feedback_list = json.load(f)
            if not isinstance(feedback_list, list):
                feedback_list = []
    except json.JSONDecodeError:
        feedback_list = []  # Reset if file is corrupted

    # Append new feedback
    feedback_list.append(feedback_entry)

    # Save feedback
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(feedback_list, f, indent=4)

    return {"message": "Feedback submitted successfully"}
'''

client = MongoClient(MONGO_URI)
db = client["waste_management"]
feedback_collection = db["feedbacks"]

@app.post("/submit-feedback/")
async def submit_feedback(feedback: FeedbackRequest):
    """Handles feedback submission and stores data in MongoDB."""

    # Ensure `s_no` exists in detection results
    if feedback.s_no not in DETECTION_RESULTS:
        raise HTTPException(status_code=400, detail="Invalid Detection ID (s_no)")

    # Prepare feedback entry
    feedback_entry = {
        "s_no": feedback.s_no,
        "bounding_box": DETECTION_RESULTS[feedback.s_no]["coords"],
        "actual_class": feedback.actual_class,
        "predicted_class": DETECTION_RESULTS[feedback.s_no]["pred_class"],
        "image_path": DETECTION_RESULTS.get("image_path")  # Add image_path key properly
    }

    # Insert into MongoDB
    result = feedback_collection.insert_one(feedback_entry)

    if result.inserted_id:
        return {"message": "Feedback submitted successfully", "id": str(result.inserted_id)}
    else:
        raise HTTPException(status_code=500, detail="Failed to save feedback")


# Define expected request format using Pydantic





HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"
#HF_MODEL = 'google/flan-t5-large'

class ClassRequest(BaseModel):
    class_name: str

@app.post("/generate-disposal-info/")
def generate_disposal_info(req: ClassRequest):
  #  prompt = (
   #     f"List exactly 5 environmentally friendly and practical disposal techniques for the waste item: "
    #    f"'{req.class_name}'. Each line should be a short, clear action starting with a verb."
    #)
    prompt_templates = [
    "Suggest 5 eco-friendly ways to dispose of {class_name}.",
    "List exactly 5 sustainable disposal methods for: {class_name}.",
    "What are 5 green techniques to dispose of '{class_name}' responsibly?",
    "Provide 5 clear actions to safely dispose of this waste: {class_name}.",
    "How should one dispose of {class_name}? List 5 short actionable methods."
]
    prompt = random.choice(prompt_templates).format(class_name=req.class_name)
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.9,
            
        }
    }

    response = requests.post(
        f"https://api-inference.huggingface.co/models/{HF_MODEL}",
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        return {"error": "Failed to fetch from Hugging Face API", "details": response.text}
    result = response.json()
    generated_text = result[0]['generated_text'].split(prompt)[-1].strip()
    lines = generated_text.split('\n')
    clean_lines = []
    for line in lines:
        cleaned = line.strip()
        # Remove leading numbering or bullets like "1.", "-", etc.
        if cleaned and (cleaned[0].isdigit() or cleaned[0] in "-•") and ('.' in cleaned[:3]):
            cleaned = cleaned.split('.', 1)[1].strip()
        clean_lines.append(cleaned)

    # Join lines into a paragraph with a space
    final_text = ' '.join(clean_lines)

    return {"disposal_info": final_text}
    
    

    