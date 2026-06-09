# Sets up the routes for all the pages

import os

from flask import Flask, render_template, request
from flask_caching import Cache
from openai import OpenAI

from config import TEMPLATES_PATH, TEXT_PATH
from application.helpers import *


# Create the Flask application
app = Flask(
    __name__,
    template_folder=TEMPLATES_PATH,
)

# Register custom Jinja filters
app.jinja_env.filters["is_active"] = is_active
app.jinja_env.filters["get_language_image"] = get_language_image


# Configure Flask cache
app.config["CACHE_TYPE"] = "simple"
app.config["CACHE_DEFAULT_TIMEOUT"] = 3600

cache = Cache(app)


@app.route("/")
def loading():
    """
    Renders the homepage.

    The original loading page is temporarily disabled.
    """

    return render_template("home.html")


@app.route("/home")
@cache.cached()
def home():
    """Renders the Home page."""

    return render_template("home.html")


@app.route("/about")
@cache.cached()
def about():
    """Renders the About Me page."""

    content = read_description(
        f"{TEXT_PATH}/about.txt"
    )

    return render_template(
        "about.html",
        content=content,
    )


@app.route("/skills")
@cache.cached()
def skills():
    """Renders the Skills page."""

    skills_data = get_skills(
        f"{TEXT_PATH}/skills.json"
    )

    return render_template(
        "skills.html",
        skills=skills_data,
    )


@app.route("/portfolio")
@cache.cached()
def portfolio():
    """Renders the Portfolio page."""

    repos = get_repositories()

    return render_template(
        "portfolio.html",
        repos=repos,
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Renders and processes the Contact page."""

    if request.method == "POST":
        return render_template("result.html")

    return render_template("contact.html")


@app.route("/result")
@cache.cached()
def result():
    """Renders the Result page."""

    return render_template("result.html")


@app.route("/ai-assistant", methods=["GET", "POST"])
def ai_assistant():
    """
    Renders the AI Assistant page and processes
    requests sent to the OpenAI API.
    """

    prompt = ""
    generated_text = ""
    error_message = ""

    if request.method == "POST":
        prompt = request.form.get(
            "prompt",
            "",
        ).strip()

        # Validate the user input
        if not prompt:
            error_message = "請先輸入問題或文字內容。"

        else:
            # Read the API key from Render Environment
            api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                app.logger.error(
                    "OPENAI_API_KEY is not configured."
                )

                error_message = (
                    "伺服器尚未設定 OpenAI API Key，"
                    "請至 Render 的 Environment 頁面設定。"
                )

            else:
                try:
                    # Create the OpenAI client
                    client = OpenAI(
                        api_key=api_key
                    )

                    # Send the user's prompt to OpenAI
                    api_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "你是一位友善、專業且可靠的 "
                                    "AI 助理。"
                                    "請清楚且有條理地回答使用者的問題。"
                                    "除非使用者要求其他語言，"
                                    "否則請使用繁體中文回答。"
                                ),
                            },
                            {
                                "role": "user",
                                "content": prompt,
                            },
                        ],
                        temperature=0.5,
                    )

                    # Safely obtain the generated response
                    generated_content = (
                        api_response.choices[0]
                        .message.content
                    )

                    if generated_content:
                        generated_text = (
                            generated_content.strip()
                        )
                    else:
                        error_message = (
                            "AI 沒有產生回覆，"
                            "請重新輸入問題後再試一次。"
                        )

                except Exception:
                    # Log the detailed error in Render Logs,
                    # but do not expose sensitive details
                    # on the website.
                    app.logger.exception(
                        "OpenAI Assistant request failed."
                    )

                    error_message = (
                        "AI 文字生成失敗。"
                        "請稍後再試，或至 Render Logs "
                        "查看詳細錯誤訊息。"
                    )

    return render_template(
        "ai_assistant.html",
        prompt=prompt,
        response=generated_text,
        error=error_message,
    )


@app.route("/image-generator", methods=["GET", "POST"])
def image_generator():
    """
    Renders the Image Generator page and processes
    image generation requests through the OpenAI API.
    """

    prompt = ""
    selected_size = "1024x1024"
    image_url = ""
    error_message = ""

    if request.method == "POST":
        prompt = request.form.get(
            "prompt",
            "",
        ).strip()

        selected_size = request.form.get(
            "size",
            "1024x1024",
        ).strip()

        allowed_sizes = {
            "1024x1024",
            "1536x1024",
            "1024x1536",
        }

        if not prompt:
            error_message = "請先輸入圖片描述。"

        elif selected_size not in allowed_sizes:
            error_message = "請選擇有效的圖片尺寸。"

        else:
            api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                app.logger.error(
                    "OPENAI_API_KEY is not configured."
                )

                error_message = (
                    "伺服器尚未設定 OpenAI API Key，"
                    "請至 Render 的 Environment 頁面設定。"
                )

            else:
                try:
                    client = OpenAI(
                        api_key=api_key
                    )

                    image_response = client.images.generate(
                        model="gpt-image-1",
                        prompt=prompt,
                        n=1,
                        size=selected_size,
                        quality="medium",
                    )

                    image_base64 = (
                        image_response.data[0].b64_json
                    )

                    if image_base64:
                        image_url = (
                            "data:image/png;base64,"
                            f"{image_base64}"
                        )
                    else:
                        error_message = (
                            "圖片生成完成，但沒有取得圖片資料，"
                            "請重新嘗試。"
                        )

                except Exception:
                    app.logger.exception(
                        "OpenAI image generation failed."
                    )

                    error_message = (
                        "AI 圖片生成失敗。"
                        "請稍後再試，或至 Render Logs "
                        "查看詳細錯誤訊息。"
                    )

    return render_template(
        "image_generator.html",
        prompt=prompt,
        selected_size=selected_size,
        image_url=image_url,
        error=error_message,
    )
