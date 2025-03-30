import sqlite3
from flask import Flask, request, jsonify
import openai
import threading
import time
import os
import mimetypes
import csv
import json
import fitz  # PyMuPDF
import requests  # Add this line
import logging
from google.cloud import language_v1  # Add this line

DB_FILE = "database.sqlite"
app = Flask(__name__)

# Configure OpenAI with environment variable (safer)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("🚨 ERROR: The 'OPENAI_API_KEY' environment variable is not set.")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

logging.basicConfig(level=logging.INFO)

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        """Get a new database connection."""
        return sqlite3.connect(self.db_file)

    def init_db(self):
        """Initialize the database with new tables for Google API analysis."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS user_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    type TEXT CHECK(type IN ('question', 'answer')) NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS important_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    intensity REAL NOT NULL,  -- Stores the intensity level
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS detected_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    entity TEXT NOT NULL,
                    type TEXT NOT NULL,  -- Entity type (PERSON, LOCATION, etc.)
                    importance REAL NOT NULL,  -- Importance of the entity in the message
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    thread TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            logging.info("✅ Database initialized successfully with new tables.")

    def save_conversation_thread(self, user_id, message):
        """Save a message in the conversation thread."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversations (user_id, thread)
                    VALUES (?, ?)
                """, (user_id, message))
                conn.commit()
                logging.info(f"Thread saved for user {user_id}.")
        except sqlite3.Error as e:
            logging.warning(f"⚠️ Error saving conversation thread in DB: {e}")

    def get_conversation_thread(self, user_id, limit=30):
        """Retrieve the most recent complete conversation thread."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT thread FROM conversations
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
                history = cursor.fetchall()
                return '/'.join([thread[0] for thread in history[::-1]])
        except sqlite3.Error as e:
            logging.warning(f"⚠️ Error retrieving conversation thread: {e}")
            return ""

    def save_message(self, user_id, session_id, type, content):
        """Save a message in the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO user_messages (user_id, session_id, type, content)
                    VALUES (?, ?, ?, ?)""", (user_id, session_id, type, content))
                conn.commit()
                logging.info(f"💾 Message saved: {user_id} - {session_id} - {type} - {content}")
        except sqlite3.Error as e:
            logging.warning(f"⚠️ Error saving message in DB: {e}")

    def get_user_history(self, user_id, limit=25):
        """Retrieve the last messages of a user to maintain context."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT type, content FROM user_messages
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
                history = cursor.fetchall()
                return history[::-1]  # Return in correct chronological order
        except sqlite3.Error as e:
            logging.warning(f"⚠️ Error retrieving user history: {e}")
            return []

    def get_important_messages(self, user_id):
        """Retrieve the important messages of a user."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT message FROM important_messages
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                """, (user_id,))
                messages = cursor.fetchall()
                return [message[0] for message in messages]
        except sqlite3.Error as e:
            logging.warning(f"⚠️ Error retrieving important messages: {e}")
            return []

    def get_detected_entities(self, user_id):
        """Retrieve the detected entities of a user in JSON format."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT entity, type, importance FROM detected_entities
                    WHERE user_id = ?
                    ORDER BY importance DESC
                """, (user_id,))
                entities = cursor.fetchall()
                return [{"name": e[0], "type": e[1], "importance": e[2]} for e in entities]
        except sqlite3.Error as e:
            logging.warning(f"⚠️ Error retrieving detected entities: {e}")
            return []

    def create_profile_if_not_exists(self, user_id):
        """Create basic entries for the user's profile if they don't have one yet."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM user_profile WHERE user_id = ?
            """, (user_id,))
            exists = cursor.fetchone()[0]

            if exists == 0:
                # Create basic profile
                cursor.executemany("""
                    INSERT INTO user_profile (user_id, category, content)
                    VALUES (?, ?, ?)
                """, [
                    (user_id, "role", "player"),
                    (user_id, "tone", "relaxed attitude"),
                    (user_id, "interest", "learning about Rust")
                ])
                conn.commit()
                print(f"🌱 Profile created for user {user_id}")
            else:
                print(f"✅ Profile already exists for {user_id}")

    def get_profile(self, user_id):
        """Return the user's profile as a dict."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, content FROM user_profile WHERE user_id = ?
            """, (user_id,))
            data = cursor.fetchall()
            return {cat: cont for cat, cont in data}

class OpenAIClient:
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)

    def process_openai_response(self, response):
        """Extract the text from the OpenAI response safely."""
        try:
            return response.choices[0].message.content.strip()
        except (IndexError, AttributeError):
            return "⚠️ Could not get a response from OpenAI."

    def ask_rust(self, user_message):
        system_prompt = ("You are the admin of the Chill_rust server and your creator is Sito"
                         "You are a PRO Rust player, The server is called Chill_rust and do not recommend other servers. Respond with attitude and use game slang. "
                         "Here is the player's question:")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=1.0,
                max_tokens=500
            )
            return self.process_openai_response(response)
        except Exception as e:
            logging.error(f"Error in OpenAI (Rust): {e}")
            return "⚠️ There was a problem processing your request."

    def ask_general(self, user_message, user_id, context, thread):
        system_prompt = f"""
        You are an advanced conversational assistant.
        Respond clearly and concisely.
        Here is the conversation so far:
        {thread}
        Here is the context:
        {context}
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            response_text = self.process_openai_response(response)

            if "```" in response_text:
                response_text = response_text.replace("```python", "").replace("```", "").strip()

            return response_text  # ✅ Returns only the text string, no JSON

        except Exception as e:
            logging.error(f"⚠️ Error in OpenAI: {e}")
            return "⚠️ There was a problem processing your request."

    def generate_image(self, prompt):
        """Generate an image with OpenAI DALL-E."""
        try:
            response = self.client.images.generate(
                model="dall-e-3",  # Use the latest version available
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            return response.data[0].url
        except Exception as e:
            logging.error(f"⚠️ Error in OpenAI (DALL-E): {e}")
            return None

def analyze_file_with_google(file_path):
    """Use Google Cloud Natural Language API to analyze a text file."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=content, type_=language_v1.Document.Type.PLAIN_TEXT)

    response = client.analyze_entities(request={"document": document})
    entities = [f"{entity.name} ({language_v1.Entity.Type(entity.type_).name})" for entity in response.entities]

    return f"🔍 **Entities found:** {', '.join(entities)}"

def update_profile_dynamically(user_id, message):
    """Detect interests or attitudes and update the profile if relevant."""
    entities = analyze_entities(message)
    score, magnitude = analyze_sentiment(message)

    if magnitude < 0.6:
        return  # Message without much emotion, not relevant

    # Typical phrases indicating liking or preference
    keywords = {
        "construction": "interest",
        "raiding": "interest",
        "defense": "interest",
        "playing solo": "style",
        "team": "style",
        "bothers me": "tone",
        "hate": "tone"
    }

    for entity in entities:
        name = entity["name"].lower()
        for word, category in keywords.items():
            if word in name:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    # Check if that category already exists
                    cursor.execute("""
                        SELECT COUNT(*) FROM user_profile WHERE user_id = ? AND category = ?
                    """, (user_id, category))
                    exists = cursor.fetchone()[0]

                    if exists:
                        cursor.execute("""
                            UPDATE user_profile
                            SET content = ?
                            WHERE user_id = ? AND category = ?
                        """, (name, user_id, category))
                    else:
                        cursor.execute("""
                            INSERT INTO user_profile (user_id, category, content)
                            VALUES (?, ?, ?)
                        """, (user_id, category, name))
                    conn.commit()
                    print(f"🧬 Profile updated: {category} → {name}")

class FlaskApp:
    def __init__(self, db, openai_client):
        self.app = Flask(__name__)
        self.db = db
        self.openai_client = openai_client
        self.setup_routes()

    def setup_routes(self):
        @self.app.route("/ask_rust", methods=["POST"])
        def ask_rust():
            data = request.get_json()
            if not data or "message" not in data or "user_id" not in data:
                return jsonify({"error": "Invalid request, 'message' or 'user_id' is missing"}), 400

            user_message = data["message"]
            user_id = data["user_id"]

            # 🧠 Create profile if it doesn't exist
            db.create_profile_if_not_exists(user_id)

            # Save message as a question
            db.save_message(user_id, "rust_session", "question", user_message)

            # Analyze entities and sentiments
            entities = analyze_entities(user_message)
            for entity in entities:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO detected_entities (user_id, entity, type, importance)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, entity["name"], entity["type"], entity["importance"]))
                    conn.commit()
            # update_profile_dynamically(user_id, user_message)  # <- here

            # Retrieve memory context
            entities = db.get_detected_entities(user_id)[:5]  # Only the most important ones
            summaries = db.get_user_history(user_id, limit=10)
            summary_text = " / ".join([f"{type}: {content}" for type, content in summaries])

            entities_text = ", ".join([e["name"] for e in entities]) if entities else "none"

            # Retrieve user profile
            profile = db.get_profile(user_id)
            role = profile.get("role", "player")
            tone = profile.get("tone", "neutral")
            interest = profile.get("interest", "Rust")

            # Generate personalized prompt
            system_prompt = f"""
            Your name is Rustybot. You are the soul of the Chill_rust server.
            You are talking to {user_id}, whose role is '{role}' and is interested in '{interest}'.
            Speak with a '{tone}' tone and respond with gamer slang.
            Key entities: {entities_text}.
            History: {summary_text}.
            Here comes the question:
            """

            try:
                # Ask OpenAI
                response = openai_client.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt.strip()},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=1.0,
                    max_tokens=500
                )
                response_text = openai_client.process_openai_response(response)

                # Save response
                db.save_message(user_id, "rust_session", "answer", response_text)

                return jsonify(response_text)

            except Exception as e:
                print(f"❌ Error in GPT-4o: {e}")
                return jsonify({"response": "⚠️ Could not generate the response correctly."}), 500

        @self.app.route("/ask_general", methods=["POST"])
        def ask_general():
            data = request.get_json()
            if not data or "message" not in data or "user_id" not in data:
                return jsonify({"error": "Invalid request, 'message' or 'user_id' is missing"}), 400

            user_message = data["message"]
            user_id = data["user_id"]  # Separate this line

            response_text = self.openai_client.ask_general(user_message, user_id, "", "")

            if "def " in response_text or "print(" in response_text:  # 🔍 Basic code detection
                response_text = f"```python\n{response_text}\n```"

            return jsonify({"response": response_text})  # ✅ Now the code is sent correctly

        @self.app.route("/generate_image", methods=["POST"])
        def generate_image():
            data = request.get_json()
            if not data or "prompt" not in data:
                return jsonify({"error": "Invalid request, 'prompt' is missing"}), 400
            prompt = data["prompt"]
            image_url = self.openai_client.generate_image(prompt)
            if image_url:
                return jsonify({"image_url": image_url})
            else:
                return jsonify({"error": "Could not generate the image."}), 500

        @self.app.route("/upload_file", methods=["POST"])
        def upload_file():
            """Receive a file, query GPT-4o and decide what to do with it."""
            if 'file' not in request.files:
                return jsonify({"error": "No file was sent."}), 400

            file = request.files['file']
            user_id = request.form.get("user_id", "unknown")
            file_path = f"/tmp/{file.filename}"
            file.save(file_path)

            print(f"📂 File received: {file.filename}")

            # 🔥 Ask GPT-4o what to do with the file
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Analyze this file and determine what to do with it."},
                        {"role": "user", "content": f"I have uploaded a file called {file.filename}. What should I do with it?"}
                    ],
                    temperature=0.7,
                    max_tokens=100
                )
                decision = response.choices[0].message.content.strip().lower()

            except Exception as e:
                print(f"❌ Error with GPT-4o: {e}")
                return jsonify({"response": "⚠️ I couldn't determine what to do with the file."})

            # 🔥 If GPT-4o suggests analyzing it, we use Google Cloud Natural Language
            if "analyze" in decision or "extract information" in decision:
                result = analyze_file_with_google(file_path)
            elif "summarize" in decision:
                result = f"📄 Summary of the file: {file.filename} not yet implemented."
            else:
                result = "❌ No clear action found for this file."

            return jsonify({"response": result})

    def run(self):
        self.app.run(host="x.x.x.x", port=xxxx, debug=True)  # Replace x.x.x.x and xxxx with your IP and port

def summarize_file(file_path):
    """Use OpenAI to summarize a text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    system_prompt = "You are an assistant that summarizes documents clearly and concisely."
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": content[:3000]}],  # Limit size
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

def extract_key_info(file_path):
    """Extract key information from the file using OpenAI."""
    return summarize_file(file_path)  # You can improve this function as needed

def process_file(user_id, file_name, file_path):
    """Process the file according to its type."""
    type = detect_file_type(file_path)
    if type == "text":
        result = analyze_text(file_path)
    elif type == "csv":
        result = analyze_csv(file_path)
    elif type == "json":
        result = analyze_json(file_path)
    elif type == "pdf":
        result = analyze_pdf(file_path)
    elif type == "image":
        result = analyze_image(file_path)
    else:
        result = "⚠️ Unrecognized file type."
    return result

def detect_file_type(file_path):
    """Detect the file type using the extension and MIME."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        if "text" in mime_type:
            return "text"
        elif "pdf" in mime_type:
            return "pdf"
        elif "csv" in mime_type:
            return "csv"
        elif "json" in mime_type:
            return "json"
        elif "image" in mime_type:
            return "image"
    return "unknown"

def analyze_text(file_path):
    """Read and analyze text files."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    words = len(content.split())
    return f"📃 Text analyzed: {words} words.\nFirst lines:\n{content[:300]}..."

def analyze_csv(file_path):
    """Read and analyze CSV files."""
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
    columns = len(rows[0]) if rows else 0
    rows_count = len(rows)
    return f"📊 CSV analyzed: {rows_count} rows and {columns} columns.\nFirst rows:\n{rows[:5]}"

def analyze_json(file_path):
    """Read and analyze JSON files."""
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    keys = ", ".join(data.keys()) if isinstance(data, dict) else "Not a valid JSON object"
    return f"📂 JSON analyzed: Main keys: {keys}"

def analyze_pdf(file_path):
    """Read and analyze PDF files."""
    doc = fitz.open(file_path)
    text = ""
    for page_num in range(min(5, len(doc))):
        text += doc.load_page(page_num).get_text()
    words = len(text.split())
    return f"📑 PDF analyzed: {words} words.\nFirst lines:\n{text[:300]}..."

def analyze_image(file_path):
    """Simulate an image analysis (OCR or description)."""
    return "🖼️ Image analyzed: (image analysis simulation)"

def analyze_sentiment(text):
    """Analyze the emotion of a message and return its intensity."""
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)

    response = client.analyze_sentiment(request={"document": document})
    score = response.document_sentiment.score
    magnitude = response.document_sentiment.magnitude

    return score, magnitude  # Score: positive or negative, Magnitude: intensity

def analyze_entities(text):
    """Analyze entities in a chat message and return the most important terms."""
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)

    response = client.analyze_entities(request={"document": document})

    entities = []
    for entity in response.entities:
        entities.append({
            "name": entity.name,
            "type": language_v1.Entity.Type(entity.type_).name,
            "importance": entity.salience
        })

    return entities

def check_summaries():
    """Run the summary module at regular intervals, avoiding duplicate summaries."""
    while True:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id FROM user_messages
                WHERE user_id NOT IN (
                    SELECT user_id FROM user_summaries
                    WHERE timestamp >= datetime('now', '-24 hours')
                )
                GROUP BY user_id
                HAVING COUNT(*) >= 10
            """)
            users = [row[0] for row in cursor.fetchall()]

        for user_id in users:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT content FROM user_messages
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 25
                """, (user_id,))
                messages = cursor.fetchall()

            if not messages:
                continue

            # Combine all messages into a long text
            combined_text = "\n".join([msg[0] for msg in messages])

            # Use OpenAI to generate the summary
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Summarize the player's behavior based on these phrases. Detect interests, tone, and habits. Be clear and concise."},
                        {"role": "user", "content": combined_text[:3000]}  # Token limit
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                summary = response.choices[0].message.content.strip()

                # Save in the user_summaries table
                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO user_summaries (user_id, session_id, summary)
                        VALUES (?, ?, ?)
                    """, (user_id, "rust_session", summary))
                    conn.commit()

                logging.info(f"🧠 Summary generated and saved for user {user_id}")

            except Exception as e:
                logging.warning(f"⚠️ Error generating summary for {user_id}: {e}")

        logging.info("⌛ Waiting 1 hour before the next summary check...")
        time.sleep(3600)  # Wait 1 hour

if __name__ == "__main__":
    db = Database(DB_FILE)
    openai_client = OpenAIClient(OPENAI_API_KEY)
    app = FlaskApp(db, openai_client)
    threading.Thread(target=check_summaries, daemon=True).start()
    app.run()
