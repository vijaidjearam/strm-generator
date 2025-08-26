FROM python:3.11-slim

# Install dependencies
RUN pip install requests guessit

# Copy script
WORKDIR /app
COPY strm-geneartor-for-jellyfin.py /app/app.py

# Set environment defaults
ENV API_TOKEN=""
ENV OUTPUT_DIR="/jellyfin_strm"
ENV POLL_INTERVAL=3600

# Run
CMD ["python", "app.py"]

