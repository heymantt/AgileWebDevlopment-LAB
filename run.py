import os

from app import create_app


config_name = os.getenv("FLASK_CONFIG", "development")
app = create_app(config_name)


if __name__ == "__main__":
    # Run with debug enabled for development
    app.run(debug=True)