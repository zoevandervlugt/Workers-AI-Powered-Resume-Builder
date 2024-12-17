# Python Workers AI Starter Kit

## Viewing
Copy your secrets file and add your credentials.

Get your credentials at dash.cloudflare.com, AI > Use REST API, Create a Workers AI API Token

To view the Resume-Builder in your brower, copy and paste these commands into your terminal after .
```
cd python
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
python -m venv venv
source ./venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```


## More resources

- [Workers AI Documentation](https://developers.cloudflare.com/workers-ai/)
- [Streamlit Examples](https://github.com/craigsdennis/image-model-streamlit-workers-ai)
