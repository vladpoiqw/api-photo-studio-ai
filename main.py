import os
import time
import requests

from fastapi import FastAPI, HTTPException
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
        "message": "AI Photo Studio работает через Yandex"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/test-yandex")
def test_yandex():

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
                "weight": 1,
                "text": "A professional premium studio photograph of a modern smartphone on a clean dark background, realistic commercial product photography"
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
                detail=f"Yandex не вернул ID операции: {operation}"
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

                if result.get("error"):
                    raise HTTPException(
                        status_code=500,
                        detail=str(result["error"])
                    )

                return {
                    "status": "success",
                    "yandex_response": result
                }

        raise HTTPException(
            status_code=504,
            detail="Yandex не завершил генерацию за 60 секунд"
        )

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
