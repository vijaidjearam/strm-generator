# Source-Provider STRM Generator for Jellyfin

This project generates `.strm` files from your **Source-Provider **
and organizes them for **Jellyfin**.\
It runs inside a Docker container, polls the Source-Provider API every hour,
and writes stream URLs into `.strm` files that Jellyfin can index.

------------------------------------------------------------------------

## ✨ Features

-   Fetches media files from your Source-Provider 
-   Starts transcode sessions and retrieves stream URLs
-   Builds `.strm` files in a Jellyfin-friendly structure:
    -   `Movies/Title (Year)/Title (Year).strm`
    -   `TVShows/Title (Year)/Season 01/Title - S01E01.strm`
-   Runs automatically every **1 hour** (configurable)
-   Lightweight containerized service with Docker

------------------------------------------------------------------------

## 🛠 Requirements

-   Docker
-   Docker Compose
-   A valid **Source-Provider API Token**

------------------------------------------------------------------------

## ⚙️ Configuration

The container is configured via environment variables:

  ----------------------------------------------------------------------------
  Variable          Description                             Default
  ----------------- --------------------------------------- ------------------
  `API_TOKEN`       Your Source-Provider API token              (required)

  `OUTPUT_DIR`      Path inside container to store `.strm`  `/jellyfin_strm`

  `POLL_INTERVAL`   Polling interval in seconds             `3600` (1h)
  ----------------------------------------------------------------------------

------------------------------------------------------------------------

## 🚀 Usage

### 1. Clone the repo

``` bash
git clone https://github.com/yourusername/strm-generator.git
cd strm-generator
```

### 2. Create `.env` file

``` env
API_TOKEN=your_api_token_here
```

### 3. Start with Docker Compose

``` bash
docker-compose up -d --build
```

The generated `.strm` files will appear in the `./jellyfin_strm` folder.

------------------------------------------------------------------------

## 🐳 Docker

### Build locally

``` bash
docker build -t yourusername/strm-generator .
```

### Run manually

``` bash
docker run -d   -e API_TOKEN=your_api_token_here   -e OUTPUT_DIR=/jellyfin_strm   -e POLL_INTERVAL=3600   -v $(pwd)/jellyfin_strm:/jellyfin_strm   yourusername/strm-generator
```

------------------------------------------------------------------------

## 🔄 CI/CD with GitHub Actions

This repo includes a GitHub Actions workflow
(`.github/workflows/docker-publish.yml`)\
It automatically **builds and pushes** the Docker image to **Docker
Hub** when changes are pushed to `main`.

### Setup

1.  In your GitHub repo, add **Secrets**:

    -   `DOCKERHUB_USERNAME`
    -   `DOCKERHUB_TOKEN`

2.  Push to `main` branch:

    ``` bash
    git add .
    git commit -m "Initial commit"
    git push origin main
    ```

The workflow will build and publish to Docker Hub at:

    docker pull yourusername/strm-generator:latest

------------------------------------------------------------------------

## 📂 Folder Structure

    Movies/
      └── Title (2023)/
          └── Title (2023).strm
    TVShows/
      └── Show Name (2021)/
          └── Season 01/
              └── Show Name - S01E01.strm
    Others/
      └── filename.strm

------------------------------------------------------------------------



MIT License
