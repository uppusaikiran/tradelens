# TradeLens Deployment Guide

This guide provides detailed instructions for deploying TradeLens in various environments.

## Deployment Options

- [Local Deployment](#local-deployment) - For personal use
- [Docker Deployment](#docker-deployment) - For containerized deployment
- [Cloud Deployment](#cloud-deployment) - For production environments

## Local Deployment

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)

### Steps

1. **Clone or download the repository**

   ```bash
   git clone https://github.com/yourusername/tradelens.git
   cd tradelens
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the root directory with the following content:

   ```
   PERPLEXITY_API_KEY=your_perplexity_api_key
   OPENAI_API_KEY=your_openai_api_key (optional)
   ```

5. **Initialize the database**

   ```bash
   python init_db.py
   ```

6. **Run the application**

   ```bash
   ./run_server.sh
   # Or manually:
   # python app.py
   ```

7. **Access the application**

   Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

## Docker Deployment

### Prerequisites

- Docker
- Docker Compose (optional, for multi-container deployments)

### Steps

1. **Create a Dockerfile in the project root**

   ```dockerfile
   FROM python:3.10-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   ENV FLASK_APP=app.py
   
   EXPOSE 5000
   
   CMD ["python", "app.py"]
   ```

2. **Create a .dockerignore file**

   ```
   venv/
   __pycache__/
   *.pyc
   *.pyo
   *.pyd
   .git/
   .env
   app.log
   stock_transactions.db
   ```

3. **Build the Docker image**

   ```bash
   docker build -t tradelens:latest .
   ```

4. **Run the Docker container**

   ```bash
   docker run -d -p 5000:5000 \
     -e PERPLEXITY_API_KEY=your_perplexity_api_key \
     --name tradelens-app \
     tradelens:latest
   ```

5. **Access the application**

   Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

### Using Docker Compose

1. **Create a docker-compose.yml file**

   ```yaml
   version: '3'
   
   services:
     web:
       build: .
       ports:
         - "5000:5000"
       volumes:
         - ./stock_transactions.db:/app/stock_transactions.db
         - ./app.log:/app/app.log
       env_file:
         - .env
       restart: unless-stopped
   ```

2. **Run with Docker Compose**

   ```bash
   docker-compose up -d
   ```

## Cloud Deployment

### Prerequisites

- An account with a cloud provider (AWS, GCP, Azure, etc.)
- Basic knowledge of cloud services
- Domain name (optional, for public access)

### AWS Elastic Beanstalk Deployment

1. **Set up the Elastic Beanstalk CLI**

   ```bash
   pip install awsebcli
   ```

2. **Initialize an Elastic Beanstalk application**

   ```bash
   eb init
   ```
   
   Follow the prompts to configure your application.

3. **Create a Procfile**

   ```
   web: gunicorn app:app
   ```

4. **Add Gunicorn to requirements.txt**

   ```
   gunicorn==20.1.0
   ```

5. **Create a .ebignore file**

   ```
   venv/
   __pycache__/
   *.pyc
   *.pyo
   *.pyd
   .git/
   .env
   app.log
   stock_transactions.db
   ```

6. **Create an environment and deploy**

   ```bash
   eb create
   ```

7. **Configure environment variables**

   In the Elastic Beanstalk console, add environment variables:
   - PERPLEXITY_API_KEY
   - OPENAI_API_KEY (optional)

8. **Access the application**

   The Elastic Beanstalk URL will be displayed after deployment.

### Heroku Deployment

1. **Install the Heroku CLI**

   ```bash
   # macOS
   brew install heroku/brew/heroku
   
   # Ubuntu
   sudo snap install heroku --classic
   
   # Windows: Download installer from Heroku website
   ```

2. **Login to Heroku**

   ```bash
   heroku login
   ```

3. **Create a Heroku app**

   ```bash
   heroku create tradelens-app
   ```

4. **Create a Procfile**

   ```
   web: gunicorn app:app
   ```

5. **Add Gunicorn to requirements.txt**

   ```
   gunicorn==20.1.0
   ```

6. **Set environment variables**

   ```bash
   heroku config:set PERPLEXITY_API_KEY=your_perplexity_api_key
   heroku config:set OPENAI_API_KEY=your_openai_api_key  # Optional
   ```

7. **Deploy to Heroku**

   ```bash
   git push heroku main
   ```

8. **Set up Heroku PostgreSQL (optional)**

   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

   You'll need to modify the application to use the PostgreSQL database instead of SQLite.

9. **Access the application**

   ```bash
   heroku open
   ```

## Production Considerations

### Database

- In production, consider using a more robust database like PostgreSQL instead of SQLite.
- Set up proper backup mechanisms.

### Security

- Use HTTPS for all production deployments.
- Keep API keys secure and never commit them to version control.
- Set up proper authentication if needed.

### Monitoring

- Implement logging to monitor application performance and errors.
- Consider setting up monitoring tools like New Relic or Datadog.

### Scaling

- For high traffic, consider:
  - Using a load balancer
  - Setting up multiple instances
  - Implementing caching mechanisms (Redis, Memcached)

## Troubleshooting

### Common Issues

1. **API rate limiting**: If you encounter rate limits from Perplexity or other APIs, implement caching or reduce request frequency.
2. **Database connectivity**: Ensure proper database connection settings, especially in cloud environments.
3. **Memory issues**: For large datasets, optimize memory usage or upgrade your hosting plan.

### Support

If you encounter issues with deployment, check:
- The application logs
- The server logs
- The cloud provider's documentation

For persistent issues, open an issue on the GitHub repository. 