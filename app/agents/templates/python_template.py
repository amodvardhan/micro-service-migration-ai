from typing import Dict, Any, List
from .base_template import BaseTemplate

class PythonTemplate(BaseTemplate):
    def get_language_name(self) -> str:
        return "Python"
    
    def get_file_extensions(self) -> List[str]:
        return ['.py']
    
    def get_dockerfile_template(self) -> str:
        return """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]"""
    
    def get_prerequisites(self) -> str:
        return "Python 3.11+ and pip"
    
    def get_local_run_instructions(self, service_name: str) -> str:
        return """```
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```"""
    
    def generate_main_files(self, service_name: str) -> List[Dict[str, str]]:
        return [
            {
                "path": f"{service_name}/main.py",
                "content": f"""from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({{"status": "healthy", "service": "{service_name}"}})

@app.route('/')
def index():
    return jsonify({{"message": "Welcome to {service_name}"}})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)"""
            },
            {
                "path": f"{service_name}/requirements.txt",
                "content": """Flask==2.3.3
gunicorn==21.2.0
requests==2.31.0"""
            },
            {
                "path": f"{service_name}/config.py",
                "content": f"""import os

class Config:
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    PORT = int(os.environ.get('PORT', 8000))
    HOST = os.environ.get('HOST', '0.0.0.0')
    SERVICE_NAME = "{service_name}"
"""
            },
            {
                "path": f"{service_name}/wsgi.py",
                "content": """from main import app

if __name__ == "__main__":
    app.run()"""
            }
        ]
