# Use an official Python runtime as the base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the app dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask app code to the working directory
COPY . .

# Set the environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Expose the Flask app port
EXPOSE 5000

# Run the Flask app
CMD ["flask", "run"]
