import os
import time
import requests

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://vladpoiqw.github.io"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# YANDEX
# =========================

YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.environ.get("YANDEX_FOLDER_ID")


# =========================
# STYLE PROMPTS
# =========================

STYLE_PROMPTS = {

    "studio":
        "professional premium studio product photography, "
        "clean dark neutral background, soft cinematic studio lighting, "
        "realistic shadows, expensive commercial advertising style, "
        "high-end photography, photorealistic",

    "premium":
        "luxury premium commercial product photography, "
        "black elegant background, dramatic cinematic lighting, "
        "beautiful reflections, sophisticated atmosphere, "
        "expensive advertising campaign, photorealistic",

    "interior":
        "beautiful modern interior, premium interior design, "
        "warm atmospheric lighting, stylish furniture and decor, "
        "commercial product photography, photorealistic",

    "lifestyle":
        "modern lifestyle commercial photography, "
        "beautiful realistic environment, natural cinematic lighting, "
        "premium advertising campaign, photorealistic"
}


# =========================
# ROOT
# =========================

@app.get("/")
def root():

    return {
        "status": "ok",
        "message": "AI Photo Studio работает через Yandex"
    }


# =========================
# HEALTH
# =========================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# =========================
# GENERATE
# =========================

@app.post("/generate")
async def generate(
    image: UploadFile = File(...),
    style: str = Form("studio")
):

    # Проверяем Yandex настройки

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


    # Проверяем стиль

    if style not in STYLE_PROMPTS:

        style = "studio"


    # Читаем загруженный файл
    # Пока он нужен только для проверки,
    # полноценное image-to-image подключим следующим этапом.

    try:

        image_data = await image.read()

        if not image_data:

            raise HTTPException(
                status_code=400,
                detail="Файл изображения пустой"
            )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Не удалось прочитать изображение: {str(e)}"
        )


    # =========================
    # PROMPT
    # =========================

    prompt = STYLE_PROMPTS[style]

    prompt += (
        ". Create a high quality commercial product image. "
        "The main subject should look like a premium product. "
        "Composition should be clean and visually attractive."
    )


    # =========================
    # REQUEST TO YANDEX
    # =========================

    headers = {

        "Authorization":
            f"Api-Key {YANDEX_API_KEY}",

        "Content-Type":
            "application/json"
    }


    payload = {

        "modelUri":
            f"art://{YANDEX_FOLDER_ID}/yandex-art/latest",

        "generationOptions": {

            "mimeType":
                "image/jpeg"
        },

        "messages": [

            {

                "weight": 1,

                "text": prompt

            }

        ]

    }


    try:

        response = requests.post(

            "https://llm.api.cloud.yandex.net/"
            "foundationModels/v1/imageGenerationAsync",

            headers=headers,

            json=payload,

            timeout=60
        )


    except requests.RequestException as e:

        raise HTTPException(

            status_code=500,

            detail=
                f"Ошибка соединения с Yandex: {str(e)}"
        )


    # =========================
    # CHECK REQUEST
    # =========================

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

            detail=
                f"Yandex не вернул ID операции: {operation}"
        )


    # =========================
    # WAIT FOR RESULT
    # =========================

    for _ in range(60):

        time.sleep(2)


        try:

            check = requests.get(

                f"https://operation.api.cloud.yandex.net/"
                f"operations/{operation_id}",

                headers={

                    "Authorization":
                        f"Api-Key {YANDEX_API_KEY}"
                },

                timeout=30
            )


        except requests.RequestException as e:

            raise HTTPException(

                status_code=500,

                detail=
                    f"Ошибка проверки операции Yandex: {str(e)}"
            )


        if check.status_code != 200:

            raise HTTPException(

                status_code=check.status_code,

                detail=check.text
            )


        result = check.json()


        # =========================
        # GENERATION COMPLETE
        # =========================

        if result.get("done"):

            if result.get("error"):

                raise HTTPException(

                    status_code=500,

                    detail=str(result["error"])
                )


            yandex_response = result.get(
                "response",
                {}
            )


            image_base64 = yandex_response.get(
                "image"
            )


            if not image_base64:

                raise HTTPException(

                    status_code=500,

                    detail=
                        "Yandex завершил генерацию, "
                        "но изображение не вернул"
                )


            return {

                "status":
                    "success",

                "image_base64":
                    image_base64,

                "mime_type":
                    "image/jpeg",

                "style":
                    style

            }


    # =========================
    # TIMEOUT
    # =========================

    raise HTTPException(

        status_code=504,

        detail=
            "Yandex не завершил генерацию "
            "за 120 секунд"
    )
