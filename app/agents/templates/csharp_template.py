from typing import Dict, Any, List
from .base_template import BaseTemplate

class CSharpTemplate(BaseTemplate):
    def get_language_name(self) -> str:
        return "C#"
    
    def get_file_extensions(self) -> List[str]:
        return ['.cs', '.csproj', '.sln']
    
    def get_dockerfile_template(self) -> str:
        return """FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY . .
EXPOSE 80
ENTRYPOINT ["dotnet", "{service_name}.dll"]"""
    
    def get_prerequisites(self) -> str:
        return ".NET 8.0 SDK or later"
    
    def get_local_run_instructions(self, service_name: str) -> str:
        return """```
# Restore dependencies
dotnet restore

# Run the application
dotnet run
```"""
    
    def generate_main_files(self, service_name: str) -> List[Dict[str, str]]:
        return [
            {
                "path": f"{service_name}/Program.cs",
                "content": f"""using Microsoft.AspNetCore;

namespace {service_name}
{{
    public class Program
    {{
        public static void Main(string[] args)
        {{
            CreateWebHostBuilder(args).Build().Run();
        }}

        public static IWebHostBuilder CreateWebHostBuilder(string[] args) =>
            WebHost.CreateDefaultBuilder(args)
                .UseStartup<Startup>();
    }}
}}"""
            },
            {
                "path": f"{service_name}/Startup.cs",
                "content": f"""using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace {service_name}
{{
    public class Startup
    {{
        public void ConfigureServices(IServiceCollection services)
        {{
            services.AddControllers();
            services.AddHealthChecks();
        }}

        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {{
            if (env.IsDevelopment())
            {{
                app.UseDeveloperExceptionPage();
            }}

            app.UseRouting();
            app.UseEndpoints(endpoints =>
            {{
                endpoints.MapControllers();
                endpoints.MapHealthChecks("/health");
            }});
        }}
    }}
}}"""
            },
            {
                "path": f"{service_name}/{service_name}.csproj",
                "content": f"""<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <AssemblyName>{service_name}</AssemblyName>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.App" />
  </ItemGroup>
</Project>"""
            },
            {
                "path": f"{service_name}/Controllers/HealthController.cs",
                "content": f"""using Microsoft.AspNetCore.Mvc;

namespace {service_name}.Controllers
{{
    [ApiController]
    [Route("api/[controller]")]
    public class HealthController : ControllerBase
    {{
        [HttpGet]
        public IActionResult Get()
        {{
            return Ok(new {{ status = "healthy", service = "{service_name}" }});
        }}
    }}
}}"""
            },
            {
                "path": f"{service_name}/appsettings.json",
                "content": """{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*"
}"""
            }
        ]
