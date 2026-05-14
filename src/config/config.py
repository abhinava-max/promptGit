from rich.text import Text
from misc.console import console


STYLE_TITLE = "bold #c084fc"
STYLE_ACCENT = "bold #818cf8"
STYLE_MUTED = "#94a3b8"
STYLE_DIM = "#64748b"
STYLE_SUCCESS = "bold #22c55e"
STYLE_ERROR = "bold #fb7185"


def print_error(message: str):
    console.print(message, style=STYLE_ERROR)


def print_success(message: str):
    console.print(message, style=STYLE_SUCCESS)


def print_info(message: str):
    console.print(message, style=STYLE_MUTED)


def print_provider_menu(providers):
    console.print("\nSelect LLM Provider:\n", style=STYLE_TITLE)

    for key, value in providers.items():
        line = Text()
        line.append(f"{key}. ", style=STYLE_DIM)
        line.append(value["display"], style=STYLE_ACCENT)
        console.print(line)


def set_Config(
    provider: str = None,
    models: str = None,
    api_key: str = None,
    base_url: str = None,
):
    from pathlib import Path
    import getpass

    ENV_PATH = Path(".env")

    PROVIDERS = {
        "1": {
            "name": "GROQ",
            "display": "Groq",
            "type": "cloud",
            "key_name": "GROQ_API_KEY",
        },
        "2": {
            "name": "OPENAI",
            "display": "OpenAI",
            "type": "cloud",
            "key_name": "OPENAI_API_KEY",
        },
        "3": {
            "name": "ANTHROPIC",
            "display": "Anthropic",
            "type": "cloud",
            "key_name": "ANTHROPIC_API_KEY",
        },
        "4": {
            "name": "GEMINI",
            "display": "Gemini",
            "type": "cloud",
            "key_name": "GEMINI_API_KEY",
        },
        "5": {
            "name": "OLLAMA",
            "display": "Ollama [Local]",
            "type": "local",
            "base_url_name": "OLLAMA_BASE_URL",
        },
    }

    PROVIDER_ALIASES = {
        "groq": "1",
        "openai": "2",
        "anthropic": "3",
        "gemini": "4",
        "ollama": "5",
    }

    def read_env():
        env_data = {}

        if not ENV_PATH.exists():
            return env_data

        with ENV_PATH.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                env_data[key.strip()] = value.strip()

        return env_data

    def write_env(env_data):
        with ENV_PATH.open("w", encoding="utf-8") as file:
            for key, value in env_data.items():
                file.write(f"{key}={value}\n")

    def parse_models(model_string):
        parsed_models = [
            model.strip()
            for model in model_string.split(",")
            if model.strip()
        ]

        if len(parsed_models) == 0:
            raise ValueError("At least one model is required.")

        if len(parsed_models) > 5:
            raise ValueError("Maximum 5 models are allowed.")

        return parsed_models

    def save_provider_config(selected_provider, model_list, api_key_value=None, base_url_value=None):
        env_data = read_env()

        provider_name = selected_provider["name"]
        provider_type = selected_provider["type"]

        env_data["CURRENT_PROVIDER"] = provider_name

        if provider_type == "cloud":
            env_data[selected_provider["key_name"]] = api_key_value

        if provider_type == "local":
            env_data[selected_provider["base_url_name"]] = base_url_value

        for index in range(1, 6):
            env_data[f"{provider_name}_MODEL_{index}"] = ""

        for index, model in enumerate(model_list, start=1):
            env_data[f"{provider_name}_MODEL_{index}"] = model

        write_env(env_data)

    def get_provider_choice(provider_value):
        if provider_value:
            provider_key = provider_value.lower().strip()

            if provider_key in PROVIDERS:
                return PROVIDERS[provider_key]

            if provider_key not in PROVIDER_ALIASES:
                print_error("Invalid provider.")
                print_info("Available providers: groq, openai, anthropic, gemini, ollama")
                return None

            return PROVIDERS[PROVIDER_ALIASES[provider_key]]

        print_provider_menu(PROVIDERS)

        choice = console.input(f"\n[{STYLE_MUTED}]Enter your choice 1-5: [/]").strip()

        if choice not in PROVIDERS:
            print_error("Invalid choice.")
            return None

        return PROVIDERS[choice]

    def prompt_api_key(selected_provider):
        console.print(
            f"Enter {selected_provider['display']} API Key: ",
            style=STYLE_MUTED,
            end="",
        )
        return getpass.getpass("").strip()

    def prompt_base_url():
        entered_base_url = console.input(
            f"[{STYLE_MUTED}]Enter Ollama Base URL "
            "(default: http://localhost:11434): [/]"
        ).strip()

        if not entered_base_url:
            return "http://localhost:11434"

        return entered_base_url

    def prompt_models():
        return console.input(
            f"[{STYLE_MUTED}]Enter up to 5 models, comma-separated: [/]"
        ).strip()

    try:
        selected_provider = get_provider_choice(provider)

        if not selected_provider:
            return

        console.print("\nSelected Provider: ", style=STYLE_MUTED, end="")
        console.print(selected_provider["display"], style=STYLE_ACCENT)

        if selected_provider["type"] == "cloud":
            if not api_key:
                api_key = prompt_api_key(selected_provider)

            if not api_key:
                print_error("API key is required.")
                return

        else:
            if not base_url:
                base_url = prompt_base_url()

        if not models:
            models = prompt_models()

        model_list = parse_models(models)

        if selected_provider["type"] == "cloud":
            save_provider_config(
                selected_provider=selected_provider,
                model_list=model_list,
                api_key_value=api_key,
            )

        else:
            save_provider_config(
                selected_provider=selected_provider,
                model_list=model_list,
                base_url_value=base_url,
            )

        print_success(f"\n{selected_provider['display']} configured successfully.")
        console.print("Current provider set to ", style=STYLE_MUTED, end="")
        console.print(f"{selected_provider['name']}.", style=STYLE_ACCENT)

    except ValueError as error:
        print_error(str(error))


def reset_config():
    from pathlib import Path

    ENV_PATH = Path(".env")

    if ENV_PATH.exists():
        ENV_PATH.unlink()

    print_success("Configuration reset successfully.")