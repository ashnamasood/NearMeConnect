# Use official Python image
FROM python:3.12

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /code

# Install dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the whole project
COPY . /code/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
