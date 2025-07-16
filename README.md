# Reddit Persona Generator 🎭

Generate insightful user personas from Reddit public activity using AI!

This Python script leverages the **Reddit API (PRAW)** to scrape a user's public posts and comments and then utilizes **Google's Gemini API** to analyze this data, infer behavioral features like frustrations and likings, and present them as a visually appealing persona card image.

## ✨ Features

* **Reddit Data Scraping**: Fetches public submissions and comments for any specified Reddit user.
* **AI-Powered Persona Generation**: Utilizes Google's Gemini 1.5 Pro to synthesize scraped data into detailed user persona attributes.
* **Comprehensive Persona Fields**: Generates attributes like fictional name, age, occupation, status, location, archetype, MBTI-style personality, motivations, behaviors, **frustrations**, **likings**, and goals/needs.
* **JSON Output**: Gemini's output is structured as a robust JSON object for easy parsing.
* **Visual Persona Card**: Creates a professional-looking PNG image of the persona card using `Pillow`, making the insights easily digestible.
* **Environment Variable Management**: Securely handles API keys using `.env` files.
* **Progress Indicators**: Uses `tqdm` to show progress during data scraping.

## 🚀 Getting Started

Follow these steps to get your Reddit Persona Generator up and running.

### Prerequisites

Before you begin, ensure you have:

* **Python 3.8+** installed.
* A **Reddit Account** to create a Reddit API app.
* A **Google Cloud Project** with access to the Gemini API.

### 1. Set Up API Credentials

This project requires API keys from Reddit and Google Gemini.

#### a. Reddit API (PRAW) Setup

1.  **Log in to Reddit**: Go to [https://www.reddit.com/prefs/apps/](https://www.reddit.com/prefs/apps/).
2.  **Create a New App**: Scroll to the bottom and click "are you a developer? create an app...".
3.  **App Details**:
    * **Name**: Choose a descriptive name (e.g., `RedditPersonaGenApp`).
    * **Type**: Select `script`. **This is crucial.**
    * **Description**: (Optional) Add a brief description.
    * **`redirect uri`**: Enter `http://localhost:8080`. This is a placeholder and doesn't need to be live.
4.  **Create App**: Click "create app".
5.  **Get Credentials**:
    * Your **Client ID** is the string below "personal use script" at the top left of your new app's box.
    * Your **Client Secret** is the "secret" string.
    

#### b. Google Gemini API Setup

1.  **Enable Gemini API**: Go to the Google AI Studio Quickstart: [https://ai.google.dev/docs/gemini_api_quickstart](https://ai.google.dev/docs/gemini_api_quickstart).
2.  **Create API Key**: Follow the instructions to create a new API key for the Gemini API. Ensure you are using a project where the "Generative Language API" is enabled.
    

### 2. Configure Environment Variables

Create a file named `.env` in the root directory of your project (where `main.py` is located) and add your credentials:

```ini
REDDIT_CLIENT_ID="YOUR_REDDIT_CLIENT_ID"
REDDIT_SECRET="YOUR_REDDIT_SECRET"
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
