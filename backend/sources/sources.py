_SOURCES = [
    {
        "name": "Anthropic",
        "changelog_url": "https://docs.anthropic.com/en/release-notes/api",
        "github_repo": None,
        "rss_url": None,
        "why_interested": (
            "Core LLM provider. Breaking changes to the API, new models, pricing changes, "
            "and deprecations directly affect agent reliability and cost."
        ),
    },
    {
        "name": "Groq",
        "changelog_url": None,
        "github_repo": "groq/groq-python",
        "rss_url": None,
        "why_interested": (
            "Primary LLM inference provider. SDK changes, new model availability, and rate limit "
            "changes affect agent performance."
        ),
    },
    {
        "name": "OPIK",
        "changelog_url": None,
        "github_repo": "comet-ml/opik",
        "rss_url": None,
        "why_interested": (
            "Olity platform. SDK updates, new eval features, and API changes affect how we "
            "instrument and monitor agents."
        ),
    },
    {
        "name": "LangChain",
        "changelog_url": None,
        "github_repo": None,
        "rss_url": "https://docs.langchain.com/changelog.xml",
        "why_interested": (
            "Core agent framework dependency. Breaking changes and new features directly affect "
            "agent architecture."
        ),
    },
    {
        "name": "LangGraph",
        "changelog_url": None,
        "github_repo": "langchain-ai/langgraph",
        "rss_url": None,
        "why_interested": (
            "Orchestration framework for multi-agent workflows. New patterns, breaking changes, "
            "and new node types affect how we build agent graphs."
        ),
    },
    {
        "name": "Pinecone",
        "changelog_url": "https://docs.pinecone.io/release-notes",
        "github_repo": "pinecone-io/pinecone-python-client",
        "rss_url": None,
        "why_interested": (
            "Vector store for RAG and memory. API changes, new index features, and pricing changes "
            "affect agent knowledge retrieval."
        ),
    },
    {
        "name": "Tavily",
        "changelog_url": None,
        "github_repo": "tavily-ai/tavily-python",
        "rss_url": None,
        "why_interested": (
            "Search API for agent web research. SDK changes and new search capabilities affect "
            "agent research quality."
        ),
    },
    {
        "name": "MCP Protocol",
        "changelog_url": None,
        "github_repo": "modelcontextprotocol/python-sdk",
        "rss_url": None,
        "why_interested": (
            "Standard protocol for agent-to-tool communication. Spec updates and new transport "
            "options affect  compatibility."
        ),
    },
    {
        "name": "Lingo.dev",
        "changelog_url": "https://lingo.dev/en/changelog",
        "github_repo": "lingodotdev/lingo.dev",
        "rss_url": None,
        "why_interested": (
            "AI-powered localization toolkit. New LLM integrations, CLI changes, MCP updates, and "
            "API changes affect developers building multilingual AI applications."
        ),
    },
]


def get_sources():
    return _SOURCES
