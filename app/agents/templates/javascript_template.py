from typing import Dict, Any, List
from .base_template import BaseTemplate

class JavaScriptTemplate(BaseTemplate):
    def get_language_name(self) -> str:
        return "JavaScript"
    
    def get_file_extensions(self) -> List[str]:
        return ['.js', '.ts', '.json']
    
    def get_dockerfile_template(self) -> str:
        return """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]"""
    
    def get_prerequisites(self) -> str:
        return "Node.js 18+ and npm"
    
    def get_local_run_instructions(self, service_name: str) -> str:
        return """```
# Install dependencies
npm install

# Run the application
npm start

# Or for development
npm run dev
```"""
    
    def generate_main_files(self, service_name: str) -> List[Dict[str, str]]:
        service_name_lower = service_name.lower()
        return [
            {
                "path": f"{service_name}/index.js",
                "content": f"""const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get('/health', (req, res) => {{
    res.json({{ status: 'healthy', service: '{service_name}' }});
}});

app.get('/', (req, res) => {{
    res.json({{ message: 'Welcome to {service_name}' }});
}});

app.listen(PORT, () => {{
    console.log(`{service_name} running on port ${{PORT}}`);
}});

module.exports = app;"""
            },
            {
                "path": f"{service_name}/package.json",
                "content": f"""{{
  "name": "{service_name_lower}",
  "version": "1.0.0",
  "description": "{service_name} microservice",
  "main": "index.js",
  "scripts": {{
    "start": "node index.js",
    "dev": "nodemon index.js",
    "test": "jest"
  }},
  "dependencies": {{
    "express": "^4.18.2"
  }},
  "devDependencies": {{
    "nodemon": "^3.0.1",
    "jest": "^29.0.0"
  }},
  "keywords": ["microservice", "express", "nodejs"],
  "author": "",
  "license": "MIT"
}}"""
            },
            {
                "path": f"{service_name}/.env.example",
                "content": f"""PORT=3000
NODE_ENV=development
SERVICE_NAME={service_name}"""
            }
        ]
