FROM djsegal/city-surfaces:latest

RUN apt-get update && apt-get install libgtk2.0-dev -y && rm -rf /var/lib/apt/lists/*
