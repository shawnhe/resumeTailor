# OpenAI Resume Tailoring with Docker

Use the repository's [Dockerfile](Dockerfile) to run the `--agent openai` pipeline.
The image includes Node.js 24, Python 3, Git, CA certificates, the OpenAI Python
SDK, resume conversion/PDF dependencies, and the Codex CLI. It installs Python
packages globally, so a container virtual environment is unnecessary.

The pipeline calls the OpenAI API directly. The installed Codex CLI is optional
and is not invoked by `--agent openai`; this flow requires an API key.

## 1. Prepare your host workspace

Install Docker and start its engine. Run the host commands below in Bash
(Linux/macOS, or WSL with Docker integration on Windows).
Arrange your files like this:

```text
workspace/
├── resumeTailor/
│   ├── Dockerfile
│   └── bin/
├── resume-comprehensive.md
└── linkedin_cookies.txt
```

Put your comprehensive Markdown resume next to the repository. If you have a
PDF or DOCX instead, place it there. Use the conditional conversion step below
before running the pipeline.

## 2. Add the LinkedIn cookies file

The linkedcookies file must be named **`linkedin_cookies.txt`**. The fetcher reads
`../linkedin_cookies.txt` relative to the current working directory. With the
container layout below, that is `/app/linkedin_cookies.txt`, one directory above
`/app/resumeTailor`.

1. Sign in to your own LinkedIn account in your browser.
2. Open browser developer tools. In Chrome/Edge, open **Application → Storage →
   Cookies → https://www.linkedin.com** (Firefox: **Storage → Cookies**).
3. Find the cookie named `li_at` and copy its value.
4. Create `linkedin_cookies.txt` next to the repo using a local text editor. Add
   one line in this exact format, replacing the placeholder with the cookie value:

   ```text
   li_at=YOUR_LINKEDIN_SESSION_COOKIE_VALUE
   ```

Use plain text without quotes, a `Cookie:` prefix, or JSON/Netscape cookie export
format. Keep this session credential private and outside Git; do not put it in
the Dockerfile or image. On Linux/macOS you can restrict file access with
`chmod 600 ../linkedin_cookies.txt` from the repo directory.

LinkedIn fetching needs this cookie; other job sites do not. If you omit it or
LinkedIn rejects it, the pipeline can prompt you to paste the job description.
Refresh the value when your session expires.

## 3. Build and start the container

Run on the **host**, from your repository:

```bash
cd /path/to/workspace/resumeTailor

docker build -t resumetailor-openai .

docker run -d --name resumetailor-openai \
  --mount "type=bind,source=$(cd .. && pwd),target=/app" \
  --workdir /app/resumeTailor \
  resumetailor-openai

docker exec -it resumetailor-openai bash
```

The Dockerfile does not copy your repository into the image. The bind mount
makes the host workspace available at `/app`, including the resume and cookie
file. Changes and generated outputs under `/app` persist on the host. The
container stays running in the background; no ports need to be published.

## 4. Configure and run OpenAI inside the container

Run these commands **inside the container shell**:

```bash
cd /app/resumeTailor

# Select the image's system Python even if the mounted repo has a host .venv.
# The pipeline checks $VIRTUAL_ENV/bin/python3 first; /usr/bin/python3 is installed.
export VIRTUAL_ENV=/usr

# Read the key without displaying it or saving its literal value in shell history.
read -rsp 'OpenAI API key: ' OPENAI_API_KEY
printf '\n'
export OPENAI_API_KEY

# Example model used by this repo; choose a compatible model your project can access.
export OPENAI_MODEL=gpt-4o

bash bin/tailor_resume_generic.sh \
  'https://www.linkedin.com/jobs/view/1234567/' \
  --base-resume /app/resume-comprehensive.md \
  --agent openai \
  --api-key "$OPENAI_API_KEY" \
  --model "$OPENAI_MODEL"
```

Create your key in the [OpenAI Platform](https://platform.openai.com/api-keys).
OpenAI documents environment-based key setup in its
[developer quickstart](https://developers.openai.com/api/docs/quickstart).
The current Bash wrapper still requires `--api-key` and `--model` explicitly;
exporting the variables alone is insufficient. The expanded key is passed as a
process argument, so use this on a trusted machine/container.

The wrapper uses Chat Completions. Select a model compatible with its request
parameters; this guide does not change the model integration. Cost and rate
limits depend on your model, project, and token usage.

**Conversion is only needed if your base resume is PDF or DOCX.** Skip this
step if you already have `/app/resume-comprehensive.md`; the main script handles
the remaining tailoring process. The current script expects Markdown and does
not automatically convert PDF/DOCX input.

If you only have a PDF or DOCX, run this command **before the tailoring command
above**, review the generated Markdown, and pass its `.md` path to `--base-resume`:

```bash
python3 bin/convert_resume_to_md.py /app/resume-comprehensive.pdf
# Produces /app/resume-comprehensive.md; .docx input is also supported.
```

Run from `/app/resumeTailor` so the relative cookie path resolves correctly.
Keep the interactive terminal (`-it`) for manual JD pasting and score prompts.
The pipeline may skip a weak match or ask for confirmation; add `--force` to
bypass the match score gate if desired. Review generated files in
`/app/resumeTailor/companies/<Company>/`, also available in the host repo's
`companies/<Company>/` directory.

## 5. Return to the container

Exit the shell with `exit`. On the host:

```bash
# Reopen a shell while the container is running.
docker exec -it resumetailor-openai bash

# Stop it when finished.
docker stop resumetailor-openai

# Start it again later, then reopen a shell.
docker start resumetailor-openai
docker exec -it resumetailor-openai bash
```

Repeat the environment/key setup in each new shell. After Dockerfile changes,
rebuild the image and recreate the container to use the new dependencies.

## Troubleshooting

| Problem | What to check |
|---------|---------------|
| Repo or resume missing | Check the host mount source and use `/app/...` paths inside the container, not host paths or `~/...`. |
| LinkedIn authentication blocked | Confirm `pwd` is `/app/resumeTailor`, and `test -f ../linkedin_cookies.txt` succeeds. Check the `li_at=` format and refresh the cookie, or paste the JD when prompted (Ctrl+D to finish). |
| Missing modules or incompatible host `.venv` | Set `VIRTUAL_ENV=/usr` as above to select the image's Python. Rebuild/recreate if the image is outdated. |
| API key/model required | Pass both `--api-key "$OPENAI_API_KEY"` and `--model "$OPENAI_MODEL"`. |
| API authentication or quota error | Check the key, project access, and API billing in the OpenAI Platform. |
| Model unavailable or rate limited | Check your project's model access and limits; choose a compatible accessible model or retry after the limit resets. |
| Container name already in use | Use `docker start` / `docker exec` for the existing container instead of running another with the same name. |

For a local Python installation without Docker, see the
[README](README.md#-quick-start). The same `--agent openai` flags and parent-directory
cookie layout apply.
