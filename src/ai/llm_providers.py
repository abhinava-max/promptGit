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

    try:
        if provider:
            provider_key = provider.lower().strip()

            if provider_key not in PROVIDER_ALIASES:
                print("Invalid provider.")
                print("Available providers: groq, openai, anthropic, gemini, ollama")
                return

            selected_provider = PROVIDERS[PROVIDER_ALIASES[provider_key]]

            if not models:
                print("Models are required. Pass models comma-separated.")
                return

            model_list = parse_models(models)

            if selected_provider["type"] == "cloud":
                if not api_key:
                    print(f"API key is required for {selected_provider['display']}.")
                    return

                save_provider_config(
                    selected_provider=selected_provider,
                    model_list=model_list,
                    api_key_value=api_key,
                )

            else:
                if not base_url:
                    base_url = "http://localhost:11434"

                save_provider_config(
                    selected_provider=selected_provider,
                    model_list=model_list,
                    base_url_value=base_url,
                )

            print(f"{selected_provider['display']} configured successfully.")
            print(f"Current provider set to {selected_provider['name']}.")
            return

        print("\nSelect LLM Provider:\n")

        for key, value in PROVIDERS.items():
            print(f"{key}. {value['display']}")

        choice = input("\nEnter your choice 1-5: ").strip()

        if choice not in PROVIDERS:
            print("Invalid choice.")
            return

        selected_provider = PROVIDERS[choice]

        print(f"\nSelected Provider: {selected_provider['display']}")

        if selected_provider["type"] == "cloud":
            api_key = getpass.getpass(
                f"Enter {selected_provider['display']} API Key: "
            ).strip()

            if not api_key:
                print("API key is required.")
                return

        else:
            base_url = input(
                "Enter Ollama Base URL [default: http://localhost:11434]: "
            ).strip()

            if not base_url:
                base_url = "http://localhost:11434"

        models = input(
            "Enter up to 5 models, comma-separated: "
        ).strip()

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

        print(f"\n{selected_provider['display']} configured successfully.")
        print(f"Current provider set to {selected_provider['name']}.")

    except ValueError as error:
        print(error)