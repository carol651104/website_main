# Sets up the routes for all the pages

import os

from flask import Flask, render_template, request, make_response
from flask_caching import Cache
from openai import OpenAI

from config import TEMPLATES_PATH, TEXT_PATH
from application.helpers import *


app = Flask(__name__, template_folder=TEMPLATES_PATH)
app.jinja_env.filters["is_active"] = is_active
app.jinja_env.filters["get_language_image"] = get_language_image

app.config["CACHE_TYPE"] = "simple"
app.config["CACHE_DEFAULT_TIMEOUT"] = 3600
cache = Cache(app)


@app.route("/")
def loading():
    """Renders the 'Loading' page of the website."""

    #response = make_response(render_template("loading.html"))
    #response.headers["Cache-Control"] = "public, max-age=3"

    #return response
    return render_template("home.html")


@app.route("/home")
@cache.cached()
def home():
    """Renders the 'Home' page of the website."""

    return render_template("home.html")


@app.route("/about")
@cache.cached()
def about():
    """Renders the 'About Me' page of the website."""

    content = read_description(f"{TEXT_PATH}/about.txt")

    return render_template("about.html", content=content)


@app.route("/skills")
@cache.cached()
def skills():
    """Renders the 'Skills' page of the website."""

    skills = get_skills(f"{TEXT_PATH}/skills.json")

    return render_template("skills.html", skills=skills)


@app.route("/portfolio")
@cache.cached()
def portfolio():
    """Renders the 'Portfolio' page of the website."""

    repos = get_repositories()

    return render_template("portfolio.html", repos=repos)


@app.route("/contact", methods=["GET", "POST"])
@cache.cached()
def contact():
    """Renders the 'Contact' page of the website."""

    # User reached route via POST
    if request.method == "POST":
        return render_template("result.html")

    # User reached route via GET
    return render_template("contact.html")


@app.route("/result")
@cache.cached()
def result():
    """Renders the 'Result' page of the website."""

    return render_template("result.html")

@app.route("/ai-assistant", methods=["GET", "POST"])
def ai_assistant():
    """Renders the OpenAI text assistant page."""

    generated_text = ""
    error_message = ""
    prompt = ""

    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()

        if not prompt:
            error_message = "請先輸入問題或文字內容。"

        else:
            api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                error_message = (
                    "伺服器尚未設定 OPENAI_API_KEY，"
                    "請至 Render Environment 設定。"
                )

            else:
                try:
                    client = OpenAI(api_key=api_key)

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "你是一位友善且專業的 AI 助理。"
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

                    generated_text = (
                        response.choices[0]
                        .message.content
                        .strip()
                    )

                except Exception as error:
                    app.logger.exception(
                        "OpenAI assistant request failed"
                    )

                    error_message = (
                        f"AI 文字生成失敗：{error}"
                    )

    return render_template(
        "ai_assistant.html",
        prompt=prompt,
        response=generated_text,
        error=error_message,
    )
