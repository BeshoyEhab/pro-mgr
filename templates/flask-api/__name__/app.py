"""Flask application for {{name}}."""

from flask import Flask, jsonify


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    @app.route("/")
    def index():
        """Root endpoint."""
        return jsonify({
            "message": "Welcome to {{name}} API!",
            "version": "0.1.0"
        })
    
    @app.route("/health")
    def health():
        """Health check endpoint."""
        return jsonify({"status": "healthy"})
    
    return app


# Create app instance for Flask CLI
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
