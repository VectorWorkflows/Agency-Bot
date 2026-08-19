FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /bot

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project into the container
COPY . .

# Run the app using Uvicorn directly, exposed to the Docker network
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]