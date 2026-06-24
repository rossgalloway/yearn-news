# Yearn News

## Get Pilled

[**The Blue Pill**](https://news.yearn.fi/)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/rossgalloway/yearn-news.git
   cd yearn-news
   ```

2. **Set up virtual environment**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Install all dependencies
   uv sync
   ```

   > Note: This project uses [uv](https://github.com/astral-sh/uv) for faster dependency installation. If you don't have uv installed, you can install it with `pip install uv` or follow the [installation instructions](https://github.com/astral-sh/uv#installation).

4. **Environment setup**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration

   # Load environment variables into your shell session
   export $(grep -v '^#' .env | xargs)
   ```

## Usage

Run:
```shell
uv run python src/generate.py
```

Generated output:

- `output.md` - Markdown source for archival/editing
- `output-x-article.html` - rich-text browser view with a copy button for X Articles
- `output-x-article-fragment.html` - body-only HTML for paste automation
- `output-x-article.txt` - Markdown-free plain text fallback
- `output-yearn-glance-banner.svg` - 600x120 Yearn at a Glance banner for X Articles
- `output-yearn-glance-banner-review.html` - browser review page for the generated banner

## Code Style

Format and lint code with ruff:
```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Fix fixable lint issues
uv run ruff check --fix .
```

Type checking with mypy:
```bash
uv run python -m mypy src tests
```
