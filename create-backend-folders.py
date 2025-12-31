import os

BASE_DIR = "backend"

STRUCTURE = {
    "app": {
        "main.py": "",
        "api": {
            "__init__.py": "",
            "consult.py": ""
        },
        "agents": {
            "__init__.py": "",
            "doctor_little": {
                "__init__.py": "",
                "agent.py": "",
                "state.py": "",
                "prompts.py": "",
                "tools.py": "",
                "workflow.py": ""
            },
            "registry.py": ""
        },
        "mcp": {
            "__init__.py": "",
            "server.py": "",
            "tools.py": ""
        },
        "coral": {
            "__init__.py": "",
            "coral_agent.toml": "",
            "integration.py": ""
        },
        "services": {
            "whisper.py": "",
            "vision.py": "",
            "evidence.py": ""
        },
        "schemas": {
            "consultation.py": ""
        },
        "utils": {
            "logging.py": "",
            "security.py": ""
        }
    },
    "requirements.txt": "",
    "Dockerfile": "",
    ".env": "",
    "run.sh": ""
}

def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)

        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not os.path.exists(path):
                with open(path, "w") as f:
                    f.write(content)

def main():
    print("🚀 Creating Doctor Little Backend Structure...")
    create_structure(".", {BASE_DIR: STRUCTURE})
    print("✅ Backend structure created successfully!")

if __name__ == "__main__":
    main()
