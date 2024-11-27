# Use an official base image with Python 3.6 and uwsgi/nginx for Flask
FROM tiangolo/uwsgi-nginx-flask:python3.6

# Set the working directory inside the container
WORKDIR /app

# Install dependencies in a single RUN command to reduce the number of layers
RUN pip install --no-cache-dir \
    redis \
    opencensus \
    opencensus-ext-azure \
    opencensus-ext-flask \
    opencensus-ext-logging \
    flask

# Copy the content of the current directory to the /app of the container
ADD . /app

# Expose the port the app runs on
EXPOSE 5000

# Command to run your Flask app (make sure `main.py` is your entry point)
CMD ["python", "main.py"]
