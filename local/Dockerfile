# Use the official lightweight image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ../app /app

# Copy the secrets file (if provided)
ARG SECRETS_FILE=../local/secrets.toml
COPY ${SECRETS_FILE} ./secrets.toml

# Expose the port Streamlit runs on
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "main.py"]

