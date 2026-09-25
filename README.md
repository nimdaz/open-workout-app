# Open Workout App - OWA
A simple self-hosted webapp to track your gym workouts.  

Define **exercises** and log **activities** on them.  
Activities on a single day are considered to be part of a **workout**.  

## Tech stack

- **Backend:** Python, [Flask](https://flask.palletsprojects.com/) Routing, logic, and general "glue" between components.  
- **Data:** [SQLAlchemy](https://www.sqlalchemy.org/) ORM over a SQLite file.
- **Templates:** [Jinja2](https://jinja.palletsprojects.com/), server-rendered.
- **Frontend:** [Pico CSS](https://picocss.com/) for styling and
  [htmx](https://htmx.org/) for the dynamic bits (exercise search, inline
  comment saving) — no build step, no JavaScript framework, no bundler.
- **Charts:** a small hand-rolled inline SVG generator (`app/charts.py`), no
  charting library.


## Installation

### Docker compose

```yml
services:
  open-workout-app:
    image: ghcr.io/nimdaz/open-workout-app:latest
    container_name: open-workout-app
    ports:
      - "5000:5000"
    volumes:
      - ./data:/code/data
    restart: unless-stopped
```

### Build & Docker

Using `docker-compose`:

```bash
git clone https://github.com/nimdaz/open-workout-app.git
cd open-workout-app
docker compose up -d
```

The app will be available at `http://localhost:5000`. Data is stored in
`./data` on the host, so it survives container restarts and rebuilds.

Without compose:

```bash
docker build -t open-workout-app .
docker run -d -p 5000:5000 -v "$(pwd)/data:/code/data" open-workout-app
```

### Running locally with a virtual environment

Requires Python 3.10+.

```bash
git clone https://github.com/nimdaz/open-workout-app.git
cd open-workout-app
python -m venv .venv
source .venv/bin/activate    # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Then open `http://localhost:5000`. By default the SQLite database is created
at `app/data/app.db`; set the `DATA_DIR` environment variable to change that.

> The built-in server (`python run.py`) is a development server. If you're
> exposing this beyond your own machine or home network, put it behind a
> proper WSGI server (e.g. gunicorn) and a reverse proxy.

## Disclaimer on usage of AI
### Phase 1 - Up to version **0.1.7**
Up to commit [0c4bdeb](https://github.com/nimdaz/open-workout-app/tree/0c4bdeb5bf047376b40115ab8bb2f5d9d0fe63e7).  
This was almost fully created by AI (Claude Sonnet 5 - free account). Descriptions of the datamodel, technology stack and pages where explicitely promped, but no code nor text was manually written. This had two goals:
1.  Experience using a LLM to solidify an idea I have.
2.  Create something I can easily understand and built upon manually.  

For that reason I went with mostly the same technology stack as [nimdaz/bookmarks-manager](https://github.com/nimdaz/bookmarks-manager).

### Phase 2 - Version 0.1.8 up to current
Some manual changes, some provided by AI. AI is used more as "Explain and show me what I should where and why, in order to achieve X".  

## License

[MIT](LICENSE) — use it, modify it, share it.
