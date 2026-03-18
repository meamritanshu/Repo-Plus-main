"""RepoPulse — Entry point."""

from app import create_app
import config.settings as settings

app = create_app()

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
