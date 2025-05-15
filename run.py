import os
from datetime import datetime

from flask import request, g
from flask_cors import CORS
from flask_wtf import CSRFProtect

from app import create_app, AUTHENTICATED_ROLE
from app.language import words
from flasgger import Swagger

app = create_app()
app.config["SECRET_KEY"] = os.getenv('SECRET')
CORS(app, origins=[os.getenv('CORS_WEB')])
csrf = CSRFProtect(app)
csrf.init_app(app)
swagger = Swagger(app)


@app.template_filter('datetime_format')
def datetime_format(value):
    """Converts milliseconds timestamp to a readable date format."""
    return datetime.utcfromtimestamp(value / 1000).strftime('%Y-%m-%d %H:%M:%S')


@app.context_processor
def inject_primary_color():
    """Inject primary_color from cookies into all templates."""
    print(f"Words data: {words.get(request.cookies.get('lang', 'en'), words.get('en'))}")
    return {
        "_primary_color": request.cookies.get('primary_color', '#000000'),
        "_username": request.cookies.get('username', None),
        "AUTHENTICATED_ROLE": AUTHENTICATED_ROLE,
        "_words": words.get(request.cookies.get('lang', 'en'), words.get('en')),
        "_host": os.getenv('HOST'),
        "_nonce": f'{g.nonce}'
    }


@app.before_request
def generate_nonce():
    if not hasattr(g, "nonce"):
        g.nonce = os.urandom(16).hex()


@app.after_request
def add_security_headers(response):
    if not app.debug:
        response.headers["X-Frame-Options"] = "DENY"
        response.headers['Content-Security-Policy'] = f"default-src 'self'; " \
                                                      f"style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com;" \
                                                      f"style-src 'nonce-{g.get('nonce', None)}';" \
                                                      f"script-src 'self' 'nonce-{g.get('nonce', None)}' https://cdn.jsdelivr.net;" \
                                                      f"font-src 'self' https://cdnjs.cloudflare.com data:;" \
                                                      f"img-src 'self' https://cdnjs.cloudflare.com data: https://*.patreonusercontent.com/;" \
                                                      f"frame-ancestors 'self' https://cdnjs.cloudflare.com;" \
                                                      f"form-action 'self';"
    return response


if __name__ == "__main__":
    host = os.getenv('HOST_IP', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    ssl_crt = os.getenv('SSL_CRT_FILE', '').strip()
    ssl_key = os.getenv('SSL_KEY_FILE', '').strip()

    if ssl_crt and ssl_key:  # Use SSL only if both files are provided
        context = (ssl_crt, ssl_key)
    else:
        context = None  # Run without SSL

    app.run(host=host, port=port, ssl_context=context, debug=os.getenv('IS_DEBUG', 0))
