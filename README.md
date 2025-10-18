# Whackathon Hackathon Project

We decided to go with the Brendan Howard prompt.

The key words in the prompt were "information accuracy" for "making decisions".

Our idea is to create a browser extension that analyses news headlines and social media news feeds to determine their accuracy by giving each article a rating and then assigning 'Gen Z friendly' badges to each article.

## Project Structure

The project is broken down into two components:

1. A Chrome Extension that interacts with web pages to extract news headlines and display accuracy ratings.
2. An Analysis Server that processes the extracted headlines and determines their accuracy using various algorithms and data

### Chrome Extension

To run the chrome extension, run the following commands in your terminal:

```bash
cd chrome-extension
npm install
npm run dev
```

Every time you make a change the dev server will update and reload the extension automatically.

### Analysis Server

1. Install the Pylance extension for VSCode for better Python support.
2. Then, click at the bottom right corner of VSCode and select the Python interpreter and create a new virtual environment.
3. Create a new terminal and run the following command to install the required packages:

```bash
source .venv/bin/activate  # On Windows use `venv\Scripts\activate`
cd analysis-server
pip install -r requirements.txt
python3 server.py # Just `python` on windows
```

The server will start running on `http://localhost:8000`.
