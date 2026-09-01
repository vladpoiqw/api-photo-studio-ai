import os
import base64
import time
import requests

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://vladpoiqw.github.io"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.environ.get("YANDEX_FOLDER_ID")


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "AI Photo Studio API работает через Yandex"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/generate")
async def generate(
    image: UploadFile = File(...),
    style: str = Form("studio")
):

    if not YANDEX_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="YANDEX_API_KEY не настроен"
        )

    if not YANDEX_FOLDER_ID:
        raise HTTPException(
            status_code=500,
            detail="YANDEX_FOLDER_ID не настроен"
        )

    prompts = {
        "studio": """
Create a professional commercial product photograph.
Clean premium studio background, soft professional lighting,
high-end e-commerce photography.
""",

        "premium": """
Create a luxurious premium product advertising photograph.
Elegant dramatic lighting, sophisticated premium background,
high-end commercial photography.
""",

        "interior": """
Create a realistic modern interior scene featuring the described product.
Clean, stylish, premium interior photography.
""",

        "lifestyle": """
Create a realistic lifestyle advertising photograph.
Modern attractive environment, professional commercial photography.
"""
    }

    prompt = prompts.get(style, prompts["studio"])

    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "modelUri": f"art://{YANDEX_FOLDER_ID}/yandex-art/latest",
        "generationOptions": {
            "mimeType": "image/jpeg"
        },
        "messages": [
            {
                "weight": "1",
                "text": prompt
            }
        ]
    }

    try:

        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGeneration",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text
            )

        operation = response.json()

        operation_id = operation.get("id")

        if not operation_id:
            raise HTTPException(
                status_code=500,
                detail=f"Yandex не вернул operation ID: {operation}"
            )

        for _ in range(30):

            time.sleep(2)

            check = requests.get(
                f"https://operation.api.cloud.yandex.net/operations/{operation_id}",
                headers={
                    "Authorization": f"Api-Key {YANDEX_API_KEY}"
                },
                timeout=30
            )

            if check.status_code != 200:
                raise HTTPException(
                    status_code=check.status_code,
                    detail=check.text
                )

            result = check.json()

            if result.get("done"):

                if "error" in result:
                    raise HTTPException(
                        status_code=500,
                        detail=result["error"]
                    )

                response_data = result.get("response", {})

                image_data = response_data.get("image")

                if not image_data:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Yandex не вернул изображение: {result}"
                    )

                return {
                    "status": "success",
                    "image_base64": image_data
                }

        raise HTTPException(
            status_code=504,
            detail="Yandex не завершил генерацию за отведённое время"
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
