# job-ads-generator

Streamlit page that writes job ads with OpenAI for the network's consultants (France and Italia tabs), deployed on Streamlit Cloud: https://mistertemp-job-ads-generator.streamlit.app

## Run locally

```sh
pipenv install --dev
pipenv run streamlit run main.py
```

The app reads its secrets from `.streamlit/secrets.toml` (gitignored), with the same keys as the Streamlit Cloud secrets (the app's ⋮ › Settings › Secrets):

```toml
api_key = "sk-..."                  # OpenAI API key
# openai_model = "gpt-6-luna"       # optional, default gpt-6-luna
# openai_reasoning_effort = "none"  # optional, default none

[beta]                              # the shared login, username "mistertemp"
name = "..."
email = "..."
password = "$2b$12$..."             # bcrypt hash

[cookie]
name = "..."
key = "..."
expiry_days = 30
```

## Tests

```sh
pipenv run pytest
```

The tests run the page with `streamlit.testing.v1.AppTest`, a test login and a stubbed OpenAI stream: no API call, no real secret.

## Updates

- **Agency advantages:** `advantages.json`, per country, brand and contract type, pre-ticked in the form. Some lines carry a year (the savings rate, the loyalty bonus): update them when the offer changes.
- **SMIC:** `SMIC_HOURLY_GROSS` in `main.py`, value and start date, at each revaluation. A French hourly pay below it is refused.
- **Model:** when OpenAI announces the shutdown of the model in use (https://developers.openai.com/api/docs/deprecations), set `openai_model` (and `openai_reasoning_effort` if the new model needs another value) in the Streamlit Cloud secrets: no commit needed.

## Deploy

A push to the branch Streamlit Cloud deploys (the app's ⋮ › Settings) redeploys the app. Streamlit Cloud installs the `Pipfile`'s pinned versions.
