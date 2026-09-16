# Deploy to Streamlit Community Cloud

This folder is the complete deployment source. No API keys or secrets are required.

1. Sign in at https://share.streamlit.io/ with your GitHub account and complete any account setup yourself.
2. Create a GitHub repository, for example `pipe-loading-dashboard`. Upload the contents of this folder to its root, including `.streamlit/config.toml`. Do not upload the ZIP file itself or a virtual environment.
3. In Streamlit, choose **Create app**, then **Yup, I have an app**.
4. Select your repository and branch. Set the main file path to **app.py**.
5. In advanced settings, choose **Python 3.12** to match the tested local environment. No secrets are needed.
6. Choose an available app address and deploy. Test the default carbon steel / NPS 4 / SCH 40 / 12 m case: 146 pieces and approximately 28.16 metric tons with the supplied assumptions.

Deployment has not been completed until Streamlit reports success and the public app loads. Check app visibility before sharing the URL. Repository visibility and app visibility are separate settings.

Files required at the repository root: `app.py`, `model.py`, `pipe_data.json`, `requirements.txt`. Include `.streamlit/config.toml` for the theme. README, tests, launcher and this guide are optional supporting files.

Reference: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
