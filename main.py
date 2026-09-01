import os
import base64

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://vladpoiqw.github.io"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "AI Photo Studio API работает"
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

    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY не настроен"
        )

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Файл пустой"
        )

    content_type = image.content_type

    if content_type not in [
        "image/jpeg",
        "image/png",
        "image/webp"
    ]:

        filename = (image.filename or "").lower()

        if filename.endswith(".png"):
            content_type = "image/png"
        elif filename.endswith(".webp"):
            content_type = "image/webp"
        else:
            content_type = "image/jpeg"

    prompts = {
        "studio": """
Transform this product photo into a professional commercial studio photograph.
Keep the product recognizable and preserve its exact shape, colors and important details.
Place it on a clean premium studio background with professional product lighting.
High-end e-commerce photography.
""",

        "premium": """
Transform this product photo into a luxurious premium advertising photograph.
Preserve the exact product identity, shape, colors and important details.
Use elegant dramatic lighting and a sophisticated premium background.
High-end commercial photography.
""",

        "interior": """
Place the product naturally into a beautiful modern interior.
Preserve the exact product appearance, shape and colors.
Make the scene realistic, clean and professionally photographed.
""",

        "lifestyle": """
Turn this product photo into a realistic lifestyle advertising photograph.
Preserve the product identity and important details.
Create an attractive modern commercial scene suitable for advertising.
"""
    }

    prompt = prompts.get(style, prompts["studio"])

    try:

        result = client.images.edit(
            model="gpt-image-2",
            image=(
                image.filename or "product.jpg",
                image_bytes,
                content_type
            ),
            prompt=prompt
        )

        image_base64 = result.data[0].b64_json

        return {
            "status": "success",
            "image_base64": image_base64
        }

    except Exception as e:

        print("OPENAI ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
