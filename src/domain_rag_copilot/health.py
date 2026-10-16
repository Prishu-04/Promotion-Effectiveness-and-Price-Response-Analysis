import sys
from domain_rag_copilot import __version__
# providers that need an api key to work
NEEDS_KEY = ["openai", "anthropic"]


def show_provider(label, provider, model, api_key):
    if provider == "unset":
        print(f"{label}: not set yet (fine for stage 1)")
        return
    print(f"{label}: {provider}, model '{model or 'not set'}'")
    if not model:
        print(f"  note: {label} model is empty")
    if provider in NEEDS_KEY and not api_key:
        print(f"  note: {label} api key is empty")

def run_health_check(settings):
    """Print a short status report. Returns True if nothing is broken."""
    healthy = True
    print(f"domain_rag_copilot version {__version__}")

    version = sys.version_info
    print(f"python version: {version.major}.{version.minor}.{version.micro}")
    if (version.major, version.minor) < (3, 11):
        print("  problem: python 3.11 or newer is needed")
        healthy = False

    print(f"log level: {settings.log_level}")
    show_provider("llm", settings.llm_provider, settings.llm_model, settings.llm_api_key)
    show_provider("embedding", settings.embedding_provider,
                  settings.embedding_model, settings.embedding_api_key)

    print("status: ok" if healthy else "status: problem found")
    return healthy