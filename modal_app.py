import modal

app = modal.App("astrology-chatbot-mm")

# Define the container image with all necessary dependencies
image = (
    modal.Image.debian_slim()
    .pip_install("Flask", "fpdf2", "gspread", "google-auth")
    .add_local_dir("static", remote_path="/root/static")
    .add_local_dir("templates", remote_path="/root/templates")
    .add_local_dir("fonts", remote_path="/root/fonts")
    .add_local_python_source("app")
    .add_local_python_source("mahabote_engine")
    .add_local_python_source("myanmar_calendar")
    .add_local_python_source("pdf_generator")
    .add_local_python_source("sheets_sync")
    .add_local_file("credentials.json", remote_path="/root/credentials.json")
)

volume = modal.Volume.from_name("astrology-bookings-vol", create_if_missing=True)

@app.function(image=image, volumes={"/data": volume}, concurrency_limit=1)
@modal.wsgi_app()
def wsgi_app():
    import sys
    sys.path.append("/root")
    from app import app as flask_app
    return flask_app
