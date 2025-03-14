from functools import wraps
from flask import jsonify, session, request, redirect, url_for
import inspect


def RequiredParams():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            sig = inspect.signature(f)
            params = sig.parameters

            # Extract parameters from request (GET or POST)
            request_data = request.args if request.method == 'GET' else request.form

            # Check for missing parameters
            missing_params = []
            extracted_params = {}

            for param_name, param in params.items():
                # Skip params that are passed as *args or **kwargs
                if param.kind in [inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD]:
                    continue

                # Check if the parameter is in the request
                if param_name not in request_data:
                    if param.default == inspect.Parameter.empty:
                        # If it's a required parameter (no default), add it to missing list
                        missing_params.append(param_name)
                    continue

                # Get the parameter's type and value from the request
                try:
                    value = request_data.get(param_name)
                    if param.annotation != inspect.Parameter.empty:
                        # Try to cast the value to the specified type
                        value = param.annotation(value)
                except (ValueError, TypeError) as e:
                    return jsonify({"error": f"Invalid value for parameter '{param_name}': {str(e)}"}), 400

                extracted_params[param_name] = value

            # If there are missing required parameters, return an error
            if missing_params:
                return jsonify({"error": f"Missing required parameters: {', '.join(missing_params)}"}), 400

            # Call the decorated function with additional params
            return f(*args, **kwargs, **extracted_params)

        return decorated_function

    return decorator
