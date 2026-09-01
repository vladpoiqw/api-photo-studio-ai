import os
import base64

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from openai import OpenAI

app = FastAPI()

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

    prompts = {
        "studio": """
        Transform this product photo into a professional commercial studio photograph.
        Keep the product itself recognizable and preserve its shape, colors and important details.
        Place it on a clean premium studio background with professional product lighting.
        High-end e-commerce photography.
        """,

        "premium": """
        Transform this product photo into a luxurious premium advertising photograph.
        Preserve the exact product identity, shape and important details.
        Use dramatic but elegant lighting, sophisticated dark premium background,
        realistic reflections and high-end commercial photography.
        """,

        "interior": """
        Place the product naturally into a beautiful modern interior.
        Preserve the exact product appearance, shape and colors.
        Make the scene realistic, clean and professionally photographed.
        """,

        "lifestyle": """
        Turn this product photo into a realistic lifestyle advertising photograph.
        Preserve the product identity and important details.
        Create an attractive modern commercial scene suitable for social media advertising.
        """
    }

    prompt = prompts.get(style, prompts["studio"])

    try:

        result = client.images.edit(
            model="gpt-image-2",
            image=image_bytes,
            prompt=prompt
        )

        image_base64 = result.data[0].b64_json

        image_result = base64.b64decode(image_base64)

       return {
    "status": "success",
    "message": "Изображение успешно создано",
    "image_base64": image_base64
}

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
