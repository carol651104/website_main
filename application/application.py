
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

    # Original loading-page code:
    #
    # response = make_response(render_template("loading.html"))
    # response.headers["Cache-Control"] = "public, max-age=3"
    # return response

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
                    api_response = (
                        client.chat.completions.create(
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
                    )

                    # Safely obtain the generated response
                    generated_content = (
                        api_response
                        .choices[0]
                        .message
                        .content
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
