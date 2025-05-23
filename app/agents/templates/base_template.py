from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseTemplate(ABC):
    """Base class for all language templates"""
    
    @abstractmethod
    def get_language_name(self) -> str:
        """Return the language name"""
        pass
    
    @abstractmethod
    def get_dockerfile_template(self) -> str:
        """Return Dockerfile template for this language"""
        pass
    
    @abstractmethod
    def generate_main_files(self, service_name: str) -> List[Dict[str, str]]:
        """Generate main application files"""
        pass
    
    @abstractmethod
    def get_prerequisites(self) -> str:
        """Get language prerequisites"""
        pass
    
    @abstractmethod
    def get_local_run_instructions(self, service_name: str) -> str:
        """Get local development instructions"""
        pass
    
    def get_file_extensions(self) -> List[str]:
        """Return file extensions for this language"""
        return []
    
    def get_test_instructions(self) -> str:
        """Get testing instructions for the language"""
        return "# Add language-specific test instructions"
    
    def generate_readme(self, service_boundary: Dict[str, Any]) -> str:
        """Generate README file (common for all languages)"""
        service_name = service_boundary.get("name", "UnknownService")
        service_name_lower = service_name.lower()
        language = self.get_language_name()
        
        readme_content = f"""# {service_name}

## Overview
This microservice handles the following responsibilities:

"""
        # Add responsibilities
        for responsibility in service_boundary.get('responsibilities', []):
            readme_content += f"- {responsibility}\n"
        
        readme_content += f"""
## Technology Stack
- **Language**: {language}
- **Entities**: {', '.join(service_boundary.get('entities', []))}
- **APIs**: {', '.join(service_boundary.get('apis', []))}

## Getting Started

### Prerequisites
- Docker installed on your system
- {self.get_prerequisites()}

### Running the Service
## Build the Docker image
docker build -t {service_name_lower}
## Run the container
docker run -p 8080:8080 {service_name_lower}
## Or run in development mode
docker run -p 8080:8080 -e ENV=development {service_name_lower}

### Running Locally (without Docker)
{self.get_local_run_instructions(service_name)}

## API Documentation
This service exposes the following endpoints:
"""
        
        # Add API endpoints
        for api in service_boundary.get('apis', []):
            readme_content += f"- {api}\n"
        
        readme_content += """
## Health Check
- **GET** `/health` - Returns service health status

## Configuration
- **Port**: 8080 (default)
- **Environment**: Set ENV=development for development mode

## Testing
"""
        readme_content += self.get_test_instructions()
        
        readme_content += """

## Deployment
This service is containerized and ready for deployment to:
- Docker Swarm
- Kubernetes
- Cloud platforms (AWS, GCP, Azure)

## Environment Variables
- `PORT`: Service port (default: 8080)
- `ENV`: Environment mode (development/production)
- `LOG_LEVEL`: Logging level (debug/info/warn/error)

## Logs
Check application logs:
docker logs <container_id>

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License
This project is licensed under the MIT License.
"""
        
        return readme_content
    
    def get_gitignore_content(self) -> str:
        """Get .gitignore content for the language"""
        return """# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory
coverage/
*.lcov

# Dependency directories
node_modules/
jspm_packages/

# Environment variables
.env
.env.test
.env.production
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Java
*.class
*.jar
*.war
*.ear
*.zip
*.tar.gz
*.rar
target/
.gradle/
build/

# C#
bin/
obj/
*.exe
*.dll
*.pdb
*.user
*.suo
*.userprefs
packages/

# Go
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.out
vendor/
"""
    
    def get_docker_compose_content(self, service_name: str) -> str:
        """Get docker-compose.yml content for local development"""
        service_name_lower = service_name.lower()
        return f"""version: '3.8'

services:
  {service_name_lower}:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ENV=development
      - LOG_LEVEL=debug
      - PORT=8080
    volumes:
      - .:/app
    restart: unless-stopped
    networks:
      - {service_name_lower}_network

networks:
  {service_name_lower}_network:
    driver: bridge
"""
    
    def create_service_files(self, service_boundary: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create complete service file structure"""
        service_name = service_boundary.get("name", "UnknownService")
        
        files = []
        
        # Add README
        files.append({
            "path": f"{service_name}/README.md",
            "content": self.generate_readme(service_boundary)
        })
        
        # Add language-specific files
        main_files = self.generate_main_files(service_name)
        files.extend(main_files)
        
        # Add Dockerfile
        files.append({
            "path": f"{service_name}/Dockerfile",
            "content": self.get_dockerfile_template().format(service_name=service_name)
        })
        
        # Add .gitignore
        files.append({
            "path": f"{service_name}/.gitignore",
            "content": self.get_gitignore_content()
        })
        
        # Add docker-compose for local development
        files.append({
            "path": f"{service_name}/docker-compose.yml",
            "content": self.get_docker_compose_content(service_name)
        })
        
        return files
