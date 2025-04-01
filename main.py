import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from io import BytesIO
import yolov5
import numpy as np
import cv2
from PIL import Image
import shutil
from fastapi.middleware.cors import CORSMiddleware




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
#model = yolov5.load('keremberke/yolov5m-garbage')

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

    # Draw bounding boxes and prepare results
    for pred in predictions:
        x1, y1, x2, y2, conf, cls = pred
        label = f"{model.names[int(cls)]} {conf:.2f}"

        # Draw rectangle
        cv2.rectangle(img_cv, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(img_cv, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Save the processed image
    output_image_path = os.path.join(UPLOAD_DIR, f"processed_{file.filename}")
    cv2.imwrite(output_image_path, img_cv)

    # Convert predictions to the desired format (Table format)
    prediction_data = []
    for pred in predictions:
        class_name = model.names[int(pred[5])]
        prediction_data.append({
            "class": class_name,
            "recyclable": "Yes" if class_name in ["plastic", "paper", "glass", "cardboard"] else "No",
            "dry_wet": "Dry" if class_name != "e-waste" else "Wet",
            "disposal_info": "Recycle at designated centers" if class_name in ["plastic", "paper", "glass", "cardboard"] else "Handle with care"
        })

    return {"image_url": f"/image/{os.path.basename(output_image_path)}", "predictions": prediction_data}

@app.get("/image/{filename}")
async def get_image(filename: str):
    return FileResponse(os.path.join(UPLOAD_DIR, filename))