# Use the official Python image from Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt from the root directory (outside the app directory)
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the app's code into the container
COPY . /app/

# Expose port 5000 (Flask default)
EXPOSE 5000

# Set environment variables (e.g., Flask app entry)
ENV FLASK_APP=app.py

# Command to run the Flask app
CMD ["flask", "run", "--host=0.0.0.0"]
