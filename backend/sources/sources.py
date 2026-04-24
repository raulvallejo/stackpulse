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
    {
        "name": "Resend",
        "changelog_url": None,
        "github_repo": "resend/resend-python",
        "rss_url": None,
        "why_interested": (
            "Email delivery API I use in production for some of my agents like StackPulse. SDK changes, "
            "rate limit updates, and new features directly affect my agent email delivery pipeline."
        ),
    },
    {
        "name": "Mem0",
        "changelog_url": None,
        "github_repo": "mem0ai/mem0",
        "rss_url": None,
        "why_interested": (
            "Agent memory layer I'm planning to integrate. New memory patterns, SDK updates, and API "
            "changes directly affect how my agents persist and retrieve context across sessions."
        ),
    },
    {
        "name": "Supabase",
        "changelog_url": None,
        "github_repo": "supabase/supabase",
        "rss_url": None,
        "why_interested": (
            "Database and auth platform I'm using for some of my agents (eg StackPulse). SDK updates, "
            "auth changes, and new features affect my multi-user architecture."
        ),
    },
    {
        "name": "Make",
        "changelog_url": "https://help.make.com/release-notes",
        "github_repo": None,
        "rss_url": None,
        "why_interested": (
            "Automation platform with AI Agents and MCP servers. New agent capabilities, scenario API "
            "changes, and MCP updates affect how I build and integrate automation workflows."
        ),
    },
    {
        "name": "Typeform",
        "changelog_url": "https://help.typeform.com/hc/en-us/articles/29035269414036-Changelog",
        "github_repo": "Typeform/js-api-client",
        "rss_url": None,
        "why_interested": (
            "Form and survey platform I use for data collection in agent workflows (specially as UI entry "
            "point in some of my built solutions). API changes, webhook updates, and new integrations "
            "affect how data flows into my pipelines."
        ),
    },
    {
        "name": "Miro",
        "changelog_url": "https://developers.miro.com/changelog",
        "github_repo": None,
        "rss_url": None,
        "why_interested": (
            "Collaborative whiteboard platform with REST API and MCP server. New developer tools and MCP "
            "updates affect how AI agents interact with visual collaboration workflows. Also everything "
            "related to API and SDK."
        ),
    },
    {
        "name": "Celonis",
        "changelog_url": "https://developer.celonis.com/changelog/",
        "github_repo": None,
        "rss_url": None,
        "why_interested": (
            "Process mining platform I work with daily. API changes, new MCP server capabilities, and "
            "agentic features directly affect my developer platform work."
        ),
    },
]


def get_sources():
    return _SOURCES
