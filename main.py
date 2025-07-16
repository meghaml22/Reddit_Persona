import praw
import os
from dotenv import load_dotenv
import google.generativeai as genai
from tqdm import tqdm
import json
import io
from PIL import Image, ImageDraw, ImageFont # You'll need to install Pillow: pip install Pillow

# Load environment variables
load_dotenv()

# --- Configuration ---
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET = os.getenv("REDDIT_SECRET")
REDDIT_USER_AGENT = "RedditPersonaScraper/0.3 by GeminiAgent"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Debug print to ensure credentials are loaded
print(f"[DEBUG] Reddit Client ID: {'Loaded' if REDDIT_CLIENT_ID else 'Missing'}")
print(f"[DEBUG] Gemini API Key: {'Loaded' if GEMINI_API_KEY else 'Missing'}")

# Configure Reddit API (PRAW)
try:
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    print("[DEBUG] Reddit API configured successfully.")
except Exception as e:
    print(f"[ERROR] Failed to configure Reddit API: {e}")
    exit()

# Configure Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Using gemini-1.5-pro for its large context window and strong reasoning capabilities
    model = genai.GenerativeModel("gemini-1.5-pro")
    print("[DEBUG] Gemini API configured successfully.")
except Exception as e:
    print(f"[ERROR] Failed to configure Gemini API: {e}")
    exit()

# --- Data Extraction Functions ---
def extract_username(profile_url):
    """Extracts the username from a Reddit profile URL."""
    return profile_url.rstrip("/").split("/")[-1]

def scrape_user_data(username, limit=30): # Increased limit for more data
    """Scrapes posts and comments for a given Reddit username."""
    user = reddit.redditor(username)
    posts, comments = [], []

    try:
        print(f"Fetching up to {limit} posts for {username}...")
        for post in tqdm(user.submissions.new(limit=limit), desc="Fetching Posts"):
            if post.selftext or post.title: # Ensure there's some content
                posts.append({
                    "title": post.title,
                    "body": post.selftext,
                    "url": f"https://reddit.com{post.permalink}" # Use permalink for direct citation
                })

        print(f"Fetching up to {limit} comments for {username}...")
        for comment in tqdm(user.comments.new(limit=limit), desc="Fetching Comments"):
            if comment.body: # Ensure comment has body text
                comments.append({
                    "body": comment.body,
                    "url": f"https://reddit.com{comment.permalink}" # Use permalink for direct citation
                })
        print(f"[✓] Scraped {len(posts)} posts and {len(comments)} comments.")
    except Exception as e:
        print(f"[ERROR] Error fetching data for {username}: {e}")
        print("Please ensure the username is correct and not deleted/suspended.")

    return posts, comments

# --- Persona Generation with LLM ---
def build_prompt(posts, comments):
    """
    Constructs a detailed prompt for the Gemini model, requesting JSON output
    with specific persona attributes including likings and frustrations,
    with citations.
    """
    text_data = "### USER'S REDDIT ACTIVITY DATA:\n\n"
    if not posts and not comments:
        text_data += "No public posts or comments found for this user."

    for i, post in enumerate(posts):
        text_data += f"--- POST {i+1} ---\nTitle: {post['title']}\nContent: {post['body']}\nURL: {post['url']}\n\n"
    for i, comment in enumerate(comments):
        text_data += f"--- COMMENT {i+1} ---\nBody: {comment['body']}\nURL: {comment['url']}\n\n"

    instructions = """
    You are an expert UX researcher tasked with creating a detailed user persona based on the provided Reddit user activity data.
    Your output MUST be a **valid JSON object**.

    Infer the following attributes for the user. If an attribute cannot be confidently inferred, set its value to "N/A".
    For list items (motivations, behavior_habits, frustrations, likings, goals_needs), provide a concise string describing the observation
    and, if possible, the specific Reddit URL from the provided data that supports this inference.

    JSON Structure Requirements:
    {
      "persona_name": "Fictional Name (e.g., Alex S.)",
      "estimated_age": "Age Range (e.g., 25-35)",
      "occupation": "Inferred Occupation (e.g., Software Developer, Student)",
      "status": "Inferred Relationship Status (e.g., Single, Married)",
      "likely_location": "Inferred General Location (e.g., North America, Urban Area)",
      "archetype": "User Archetype (e.g., The Explorer, The Analyst, The Giver)",
      "mbti_personality": "MBTI-style Personality (e.g., INTJ, ESFP) or descriptive traits (e.g., Introverted, Analytical)",
      "motivations": [
        {"item": "Motivation 1 description", "citation_url": "URL if available"},
        {"item": "Motivation 2 description", "citation_url": "URL if available"}
      ],
      "behavior_habits": [
        {"item": "Behavior/Habit 1 description", "citation_url": "URL if available"}
      ],
      "frustrations": [
        {"item": "Frustration 1 description (e.g., 'Dislikes unclear instructions')", "citation_url": "URL if available"}
      ],
      "likings": [
        {"item": "Liking 1 description (e.g., 'Enjoys discussing complex sci-fi plots')", "citation_url": "URL if available"}
      ],
      "goals_needs": [
        {"item": "Goal/Need 1 description", "citation_url": "URL if available"}
      ]
    }

    Ensure all keys are present, even if their values are "N/A" or empty lists.
    Be precise and concise in your descriptions.
    """
    return instructions + "\n\n" + text_data

def generate_persona_with_gemini(prompt):
    """Sends the prompt to Gemini and returns the raw text response."""
    try:
        print("Generating persona with Gemini...")
        response = model.generate_content(prompt)
        # Access response.text and clean up potential markdown code blocks
        persona_raw_text = response.text.strip()
        if persona_raw_text.startswith("```json"):
            persona_raw_text = persona_raw_text[7:]
        if persona_raw_text.endswith("```"):
            persona_raw_text = persona_raw_text[:-3]
        print("[✓] Persona generation complete.")
        return persona_raw_text
    except Exception as e:
        print(f"[ERROR] Error generating content with Gemini: {e}")
        return None

def parse_persona_data_from_json(json_string):
    """Parses the JSON string output from Gemini into a Python dictionary."""
    try:
        # Some models might output extra text around JSON, try to find the actual JSON
        start_brace = json_string.find('{')
        end_brace = json_string.rfind('}')
        if start_brace != -1 and end_brace != -1:
            json_string = json_string[start_brace : end_brace + 1]

        persona_data = json.loads(json_string)
        print("[✓] Persona data parsed from JSON successfully.")
        return persona_data
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON from Gemini response: {e}")
        print("Raw Gemini response (partial):", json_string[:500]) # Print first 500 chars for debug
        return None
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred during JSON parsing: {e}")
        return None

# --- Image Generation ---
def generate_persona_image(persona_data, filename="user_persona_card.png"):
    """
    Generates a user persona card as an image using Pillow.
    
    """
    if not persona_data:
        print("[ERROR] No persona data to generate an image.")
        return

    # Image dimensions and colors
    width, height = 800, 1200 # Adjusted height for more content
    background_color = (250, 250, 250) # Very light grey
    text_color = (50, 50, 50)
    header_color = (30, 30, 30)
    section_title_color = (70, 70, 70)
    accent_color = (100, 150, 255) # A nice blue for accents

    img = Image.new('RGB', (width, height), color=background_color)
    d = ImageDraw.Draw(img)

    # Load fonts (try common system fonts or provide paths)
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 40)
        font_name = ImageFont.truetype("arialbd.ttf", 32)
        font_header = ImageFont.truetype("arialbd.ttf", 22)
        font_body = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 12)
    except IOError:
        print("Warning: Could not load Arial fonts. Using default PIL fonts. "
              "For better aesthetics, ensure 'arial.ttf' and 'arialbd.ttf' are accessible "
              "or specify correct paths.")
        font_title = ImageFont.load_default()
        font_name = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # --- Drawing elements ---
    y_offset = 40
    x_margin = 60
    content_width = width - (2 * x_margin)

    # Main Title
    d.text((x_margin, y_offset), "User Persona Card", fill=header_color, font=font_title)
    y_offset += 60

    # Persona Name
    d.text((x_margin, y_offset), persona_data.get('persona_name', 'N/A'), fill=accent_color, font=font_name)
    y_offset += 40

    # Basic Info Section
    d.text((x_margin, y_offset), "Basic Information:", fill=section_title_color, font=font_header)
    y_offset += 30
    info_items = [
        f"Age: {persona_data.get('estimated_age', 'N/A')}",
        f"Occupation: {persona_data.get('occupation', 'N/A')}",
        f"Status: {persona_data.get('status', 'N/A')}",
        f"Location: {persona_data.get('likely_location', 'N/A')}",
        f"Archetype: {persona_data.get('archetype', 'N/A')}",
        f"Personality: {persona_data.get('mbti_personality', 'N/A')}"
    ]
    for item in info_items:
        d.text((x_margin + 10, y_offset), item, fill=text_color, font=font_body)
        y_offset += 25
    y_offset += 20

    # Helper to draw bulleted sections with text wrapping
    def draw_bullet_section(drawer, x, y, title, items, header_font, body_font, text_color, max_width):
        drawer.text((x, y), title, fill=section_title_color, font=header_font)
        y += 25
        if not items:
            drawer.text((x + 10, y), "• No specific data inferred.", fill=(150,150,150), font=body_font)
            y += 25
        else:
            for item_data in items:
                item_text = item_data.get('item', 'N/A')
                citation = item_data.get('citation_url', '')

                # Text wrapping logic
                wrapped_lines = []
                words = item_text.split(' ')
                current_line = ""
                for word in words:
                    test_line = f"{current_line} {word}".strip()
                    bbox = drawer.textbbox((0,0), test_line, font=body_font)
                    text_width = bbox[2] - bbox[0]
                    if text_width < max_width - 20: # Account for bullet point
                        current_line = test_line
                    else:
                        wrapped_lines.append(current_line)
                        current_line = word
                wrapped_lines.append(current_line)

                for i, line in enumerate(wrapped_lines):
                    prefix = "• " if i == 0 else "  " # Only bullet first line
                    drawer.text((x + 10, y), f"{prefix}{line}", fill=text_color, font=body_font)
                    y += 20 # Line height

                if citation:
                    drawer.text((x + 25, y), f"(Source: {citation.split('/')[-1]})", fill=(100,100,100), font=font_small)
                    y += 18
        y += 20 # Space after section
        return y

    # Behavioral Features Section
    y_offset = draw_bullet_section(d, x_margin, y_offset, "Frustrations:", persona_data.get('frustrations', []), font_header, font_body, text_color, content_width)
    y_offset = draw_bullet_section(d, x_margin, y_offset, "Likings:", persona_data.get('likings', []), font_header, font_body, text_color, content_width)
    y_offset = draw_bullet_section(d, x_margin, y_offset, "Motivations:", persona_data.get('motivations', []), font_header, font_body, text_color, content_width)
    y_offset = draw_bullet_section(d, x_margin, y_offset, "Behavior & Habits:", persona_data.get('behavior_habits', []), font_header, font_body, text_color, content_width)
    y_offset = draw_bullet_section(d, x_margin, y_offset, "Goals & Needs:", persona_data.get('goals_needs', []), font_header, font_body, text_color, content_width)


    # Save the image
    try:
        img.save(filename)
        print(f"[✓] Persona card image saved to {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to save image: {e}")

# --- Main Execution Flow ---
def main():
    profile_url = input("Enter Reddit profile URL (e.g., https://www.reddit.com/user/spez): ")
    if not profile_url:
        print("No URL entered. Exiting.")
        return

    username = extract_username(profile_url)
    print(f"\n--- Starting Persona Generation for: {username} ---")

    posts, comments = scrape_user_data(username)

    if not posts and not comments:
        print("[INFO] No public posts or comments found. Cannot generate a persona.")
        return

    prompt = build_prompt(posts, comments)
    persona_raw_text = generate_persona_with_gemini(prompt)

    if persona_raw_text:
        # Save raw Gemini output for debugging
        raw_output_filename = f"{username}_persona_raw.txt"
        with open(raw_output_filename, "w", encoding="utf-8") as f:
            f.write(persona_raw_text)
        print(f"[✓] Raw Gemini output saved to {raw_output_filename}")

        persona_data = parse_persona_data_from_json(persona_raw_text)

        if persona_data:
            image_filename = f"{username}_persona_card.png"
            generate_persona_image(persona_data, image_filename)
        else:
            print("[ERROR] Could not generate persona image due to parsing failure.")
    else:
        print("[ERROR] Persona generation failed. No raw text output received.")

    print(f"\n--- Persona Generation for {username} Complete ---")

if __name__ == "__main__":
    main()