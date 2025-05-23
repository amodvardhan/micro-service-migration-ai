from typing import Dict, Any, List
from .base_template import BaseTemplate

class GoTemplate(BaseTemplate):
    def get_language_name(self) -> str:
        return "Go"
    
    def get_file_extensions(self) -> List[str]:
        return ['.go', '.mod']
    
    def get_dockerfile_template(self) -> str:
        return """FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o main .

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/main .
EXPOSE 8080
CMD ["./main"]"""
    
    def get_prerequisites(self) -> str:
        return "Go 1.21+ compiler"
    
    def get_local_run_instructions(self, service_name: str) -> str:
        service_name_lower = service_name.lower()
        return f"""```
# Download dependencies
go mod tidy

# Run the application
go run main.go

# Or build and run
go build -o {service_name_lower}
./{service_name_lower}
```"""
    
    def generate_main_files(self, service_name: str) -> List[Dict[str, str]]:
        service_name_lower = service_name.lower()
        return [
            {
                "path": f"{service_name}/main.go",
                "content": f"""package main

import (
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"
)

type Response struct {{
    Message string `json:"message"`
    Service string `json:"service"`
    Status  string `json:"status,omitempty"`
}}

func healthHandler(w http.ResponseWriter, r *http.Request) {{
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(Response{{
        Status:  "healthy",
        Service: "{service_name}",
    }})
}}

func indexHandler(w http.ResponseWriter, r *http.Request) {{
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(Response{{
        Message: "Welcome to {service_name}",
        Service: "{service_name}",
    }})
}}

func main() {{
    port := os.Getenv("PORT")
    if port == "" {{
        port = "8080"
    }}

    http.HandleFunc("/health", healthHandler)
    http.HandleFunc("/", indexHandler)
    
    fmt.Printf("{service_name} running on port %s\\n", port)
    log.Fatal(http.ListenAndServe(":"+port, nil))
}}"""
            },
            {
                "path": f"{service_name}/go.mod",
                "content": f"module {service_name_lower}\n\ngo 1.21\n\nrequire ()"
            },
            {
                "path": f"{service_name}/go.sum",
                "content": "# Go modules checksum file"
            }
        ]
