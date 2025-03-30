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
import requests  # Agregar esta línea
import logging
from google.cloud import language_v1  # Agregar esta línea

DB_FILE = "database.sqlite"
app = Flask(__name__)

# Configurar OpenAI con variable de entorno (más seguro)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("🚨 ERROR: La variable de entorno 'OPENAI_API_KEY' no está configurada.")
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
        """Inicializa la base de datos con nuevas tablas para análisis de Google API."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS mensajes_usuario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id TEXT NOT NULL,
                    sesion_id TEXT NOT NULL,
                    tipo TEXT CHECK(tipo IN ('pregunta', 'respuesta')) NOT NULL,
                    contenido TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS mensajes_importantes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id TEXT NOT NULL,
                    mensaje TEXT NOT NULL,
                    intensidad REAL NOT NULL,  -- Guarda el nivel de intensidad
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS entidades_detectadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id TEXT NOT NULL,
                    entidad TEXT NOT NULL,
                    tipo TEXT NOT NULL,  -- Tipo de entidad (PERSON, LOCATION, etc.)
                    importancia REAL NOT NULL,  -- Importancia de la entidad en el mensaje
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS resumenes_usuario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id TEXT NOT NULL,
                    sesion_id TEXT NOT NULL,
                    resumen TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS perfil_usuario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    contenido TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS conversaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id TEXT NOT NULL,
                    hilo TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            logging.info("✅ Base de datos inicializada correctamente con nuevas tablas.")

    def guardar_hilo_conversacion(self, usuario_id, mensaje):
        """Guarda un mensaje en el hilo de la conversación."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversaciones (usuario_id, hilo)
                    VALUES (?, ?)
                """, (usuario_id, mensaje))
                conn.commit()
                logging.info(f"Hilo guardado para usuario {usuario_id}.")
        except sqlite3.Error as e:
            logging.warning(f"⚠️ Error al guardar hilo de conversación en DB: {e}")

    def obtener_hilo_conversacion(self, usuario_id, limite=30):
        """Recuerda el hilo completo de la conversación más reciente."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT hilo FROM conversaciones
                    WHERE usuario_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (usuario_id, limite))
                historial = cursor.fetchall()
                return '/'.join([hilo[0] for hilo in historial[::-1]])
        except sqlite3.Error as e:
            logging.warning(f"⚠️ Error al obtener hilo de conversación: {e}")
            return ""

    def guardar_mensaje(self, usuario_id, sesion_id, tipo, contenido):
        """Guarda un mensaje en la base de datos."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO mensajes_usuario (usuario_id, sesion_id, tipo, contenido)
                    VALUES (?, ?, ?, ?)""", (usuario_id, sesion_id, tipo, contenido))
                conn.commit()
                logging.info(f"💾 Mensaje guardado: {usuario_id} - {sesion_id} - {tipo} - {contenido}")
        except sqlite3.Error as e:
            logging.warning(f"⚠️ Error al guardar mensaje en DB: {e}")

    def obtener_historial_usuario(self, usuario_id, limite=25):
        """Recupera los últimos mensajes de un usuario para mantener el contexto."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT tipo, contenido FROM mensajes_usuario
                    WHERE usuario_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (usuario_id, limite))
                historial = cursor.fetchall()
                return historial[::-1]  # Devolver en orden cronológico correcto
        except sqlite3.Error as e:
            logging.warning(f"⚠️ Error al obtener historial de usuario: {e}")
            return []

    def obtener_mensajes_importantes(self, usuario_id):
        """Recupera los mensajes importantes de un usuario."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT mensaje FROM mensajes_importantes
                    WHERE usuario_id = ?
                    ORDER BY timestamp DESC
                """, (usuario_id,))
                mensajes = cursor.fetchall()
                return [mensaje[0] for mensaje in mensajes]
        except sqlite3.Error as e:
            logging.warning(f"⚠️ Error al obtener mensajes importantes: {e}")
            return []

    def obtener_entidades_detectadas(self, usuario_id):
        """Recupera las entidades detectadas de un usuario en formato JSON."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT entidad, tipo, importancia FROM entidades_detectadas
                    WHERE usuario_id = ?
                    ORDER BY importancia DESC
                """, (usuario_id,))
                entidades = cursor.fetchall()
                return [{"nombre": e[0], "tipo": e[1], "importancia": e[2]} for e in entidades]
        except sqlite3.Error as e:
            logging.warning(f"⚠️ Error al obtener entidades detectadas: {e}")
            return []

    def crear_perfil_si_no_existe(self, user_id):
        """Crea entradas básicas para el perfil del usuario si aún no tiene."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM perfil_usuario WHERE usuario_id = ?
            """, (user_id,))
            existe = cursor.fetchone()[0]

            if existe == 0:
                # Crear perfil básico
                cursor.executemany("""
                    INSERT INTO perfil_usuario (usuario_id, categoria, contenido)
                    VALUES (?, ?, ?)
                """, [
                    (user_id, "rol", "jugador"),
                    (user_id, "tono", "actitud relajada"),
                    (user_id, "interes", "aprender sobre Rust")
                ])
                conn.commit()
                print(f"🌱 Perfil creado para el usuario {user_id}")
            else:
                print(f"✅ Perfil ya existe para {user_id}")

    def obtener_perfil(self, user_id):
        """Devuelve el perfil del usuario como dict."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT categoria, contenido FROM perfil_usuario WHERE usuario_id = ?
            """, (user_id,))
            datos = cursor.fetchall()
            return {cat: cont for cat, cont in datos}

class OpenAIClient:
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)

    def procesar_respuesta_openai(self, response):
        """Extrae el texto de la respuesta de OpenAI de forma segura."""
        try:
            return response.choices[0].message.content.strip()
        except (IndexError, AttributeError):
            return "⚠️ No se pudo obtener respuesta de OpenAI."

    def ask_rust(self, user_message):
        system_prompt = ("Tu eres el admin del server Chill_rust y tu creador es Sito"
                         "Eres un jugador PRO de Rust, El server se llama Chill_rust y no recomiendes otros servers. Responde con actitud y usa jerga del juego. "
                         "Aquí está la pregunta del jugador:")
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
            return self.procesar_respuesta_openai(response)
        except Exception as e:
            logging.error(f"Error en OpenAI (Rust): {e}")
            return "⚠️ Hubo un problema al procesar tu solicitud."

    def ask_general(self, user_message, user_id, contexto, hilo):
        system_prompt = f"""
        Eres un asistente conversacional avanzado.
        Responde de manera clara y concisa.
        Aquí está la conversación hasta ahora:
        {hilo}
        Aquí está el contexto:
        {contexto}
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
            response_text = self.procesar_respuesta_openai(response)

            if "```" in response_text:
                response_text = response_text.replace("```python", "").replace("```", "").strip()

            return response_text  # ✅ Returns only the text string, no JSON

        except Exception as e:
            logging.error(f"⚠️ Error en OpenAI: {e}")
            return "⚠️ Hubo un problema al procesar tu solicitud."

    def generar_imagen(self, prompt):
        """Genera una imagen con OpenAI DALL-E."""
        try:
            response = self.client.images.generate(
                model="dall-e-3",  # Usa la última versión disponible
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            return response.data[0].url
        except Exception as e:
            logging.error(f"⚠️ Error en OpenAI (DALL-E): {e}")
            return None

def analizar_archivo_con_google(file_path):
    """Usa Google Cloud Natural Language API para analizar un archivo de texto."""
    with open(file_path, "r", encoding="utf-8") as file:
        contenido = file.read()

    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=contenido, type_=language_v1.Document.Type.PLAIN_TEXT)

    response = client.analyze_entities(request={"document": document})
    entidades = [f"{entity.name} ({language_v1.Entity.Type(entity.type_).name})" for entity in response.entities]

    return f"🔍 **Entidades encontradas:** {', '.join(entidades)}"

def actualizar_perfil_dinamicamente(user_id, mensaje):
    """Detecta intereses o actitudes y actualiza el perfil si es relevante."""
    entidades = analizar_entidades(mensaje)
    score, magnitude = analizar_sentimiento(mensaje)

    if magnitude < 0.6:
        return  # Mensaje sin mucha emoción, no es relevante

    # Frases típicas que indican gusto o preferencia
    palabras_clave = {
        "construcción": "interes",
        "raideo": "interes",
        "defensa": "interes",
        "jugar solo": "estilo",
        "equipo": "estilo",
        "me molesta": "tono",
        "odio": "tono"
    }

    for entidad in entidades:
        nombre = entidad["nombre"].lower()
        for palabra, categoria in palabras_clave.items():
            if palabra in nombre:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    # Verificar si ya existe esa categoría
                    cursor.execute("""
                        SELECT COUNT(*) FROM perfil_usuario WHERE usuario_id = ? AND categoria = ?
                    """, (user_id, categoria))
                    existe = cursor.fetchone()[0]

                    if existe:
                        cursor.execute("""
                            UPDATE perfil_usuario
                            SET contenido = ?
                            WHERE usuario_id = ? AND categoria = ?
                        """, (nombre, user_id, categoria))
                    else:
                        cursor.execute("""
                            INSERT INTO perfil_usuario (usuario_id, categoria, contenido)
                            VALUES (?, ?, ?)
                        """, (user_id, categoria, nombre))
                    conn.commit()
                    print(f"🧬 Perfil actualizado: {categoria} → {nombre}")

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
                return jsonify({"error": "Solicitud inválida, falta 'message' o 'user_id'"}), 400

            user_message = data["message"]
            user_id = data["user_id"]

            # 🧠 Crear perfil si aún no existe
            db.crear_perfil_si_no_existe(user_id)

            # Guardar mensaje como pregunta
            db.guardar_mensaje(user_id, "sesion_rust", "pregunta", user_message)

            # Analizar entidades y sentimientos
            entidades = analizar_entidades(user_message)
            for entidad in entidades:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO entidades_detectadas (usuario_id, entidad, tipo, importancia)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, entidad["nombre"], entidad["tipo"], entidad["importancia"]))
                    conn.commit()
            # actualizar_perfil_dinamicamente(user_id, user_message)  # <- aquí

            # Obtener contexto de memoria
            entidades = db.obtener_entidades_detectadas(user_id)[:5]  # Solo las más importantes
            resumenes = db.obtener_historial_usuario(user_id, limite=10)
            resumen_texto = " / ".join([f"{tipo}: {contenido}" for tipo, contenido in resumenes])

            entidades_texto = ", ".join([e["nombre"] for e in entidades]) if entidades else "ninguna"

            # Obtener perfil del usuario
            perfil = db.obtener_perfil(user_id)
            rol = perfil.get("rol", "jugador")
            tono = perfil.get("tono", "neutral")
            interes = perfil.get("interes", "Rust")

            # Generar prompt personalizado
            system_prompt = f"""
            Tu nombre es Rustybot. Eres el alma del servidor Chill_rust.
            Estás hablando con {user_id}, cuyo rol es '{rol}' y le interesa '{interes}'.
            Habla con un tono '{tono}' y responde con jerga gamer.
            Entidades clave: {entidades_texto}.
            Historial: {resumen_texto}.
            Aquí viene la pregunta:
            """

            try:
                # Preguntar a OpenAI
                response = openai_client.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt.strip()},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=1.0,
                    max_tokens=500
                )
                respuesta_texto = openai_client.procesar_respuesta_openai(response)

                # Guardar respuesta
                db.guardar_mensaje(user_id, "sesion_rust", "respuesta", respuesta_texto)

                return jsonify(respuesta_texto)

            except Exception as e:
                print(f"❌ Error en GPT-4o: {e}")
                return jsonify({"respuesta": "⚠️ No se pudo generar la respuesta correctamente."}), 500

        @self.app.route("/ask_general", methods=["POST"])
        def ask_general():
            data = request.get_json()
            if not data or "message" not in data or "user_id" not in data:
                return jsonify({"error": "Solicitud inválida, falta 'message' o 'user_id'"}), 400

            user_message = data["message"]
            user_id = data["user_id"]  # Separate this line

            respuesta_texto = self.openai_client.ask_general(user_message, user_id, "", "")

            if "def " in respuesta_texto or "print(" in respuesta_texto:  # 🔍 Detección básica de código
                respuesta_texto = f"```python\n{respuesta_texto}\n```"

            return jsonify({"response": respuesta_texto})  # ✅ Ahora el código se envía correctamente

        @self.app.route("/generate_image", methods=["POST"])
        def generate_image():
            data = request.get_json()
            if not data or "prompt" not in data:
                return jsonify({"error": "Solicitud inválida, falta 'prompt'"}), 400
            prompt = data["prompt"]
            image_url = self.openai_client.generar_imagen(prompt)
            if image_url:
                return jsonify({"image_url": image_url})
            else:
                return jsonify({"error": "No se pudo generar la imagen."}), 500

        @self.app.route("/upload_file", methods=["POST"])
        def upload_file():
            """Recibe un archivo, consulta a GPT-4o y decide qué hacer con él."""
            if 'file' not in request.files:
                return jsonify({"error": "No se envió ningún archivo."}), 400

            file = request.files['file']
            user_id = request.form.get("user_id", "desconocido")
            file_path = f"/tmp/{file.filename}"
            file.save(file_path)

            print(f"📂 Archivo recibido: {file.filename}")

            # 🔥 Preguntar a GPT-4o qué hacer con el archivo
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Analiza este archivo y determina qué hacer con él."},
                        {"role": "user", "content": f"He subido un archivo llamado {file.filename}. ¿Qué debería hacer con él?"}
                    ],
                    temperature=0.7,
                    max_tokens=100
                )
                decision = response.choices[0].message.content.strip().lower()

            except Exception as e:
                print(f"❌ Error con GPT-4o: {e}")
                return jsonify({"respuesta": "⚠️ No pude determinar qué hacer con el archivo."})

            # 🔥 Si GPT-4o sugiere analizarlo, usamos Google Cloud Natural Language
            if "analizar" in decision or "extraer información" in decision:
                resultado = analizar_archivo_con_google(file_path)
            elif "resumir" in decision:
                resultado = f"📄 Resumen del archivo: {file.filename} aún no implementado."
            else:
                resultado = "❌ No se encontró una acción clara para este archivo."

            return jsonify({"respuesta": resultado})

    def run(self):
        self.app.run(host="x.x.x.x", port=xxxx, debug=False) # ← Reemplaza con tu IP y puerto reales en producción

def resumir_archivo(file_path):
    """Usa OpenAI para resumir un archivo de texto."""
    with open(file_path, 'r', encoding='utf-8') as file:
        contenido = file.read()
    system_prompt = "Eres un asistente que resume documentos de forma clara y concisa."
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": contenido[:3000]}],  # Limitar tamaño
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

def extraer_info_clave(file_path):
    """Extrae información clave del archivo usando OpenAI."""
    return resumir_archivo(file_path)  # Puedes mejorar esta función según el caso

def procesar_archivo(usuario_id, archivo_nombre, archivo_ruta):
    """Procesa el archivo según su tipo."""
    tipo = detectar_tipo_archivo(archivo_ruta)
    if tipo == "texto":
        resultado = analizar_texto(archivo_ruta)
    elif tipo == "csv":
        resultado = analizar_csv(archivo_ruta)
    elif tipo == "json":
        resultado = analizar_json(archivo_ruta)
    elif tipo == "pdf":
        resultado = analizar_pdf(archivo_ruta)
    elif tipo == "imagen":
        resultado = analizar_imagen(archivo_ruta)
    else:
        resultado = "⚠️ Tipo de archivo no reconocido."
    return resultado

def detectar_tipo_archivo(file_path):
    """Detecta el tipo de archivo usando la extensión y MIME."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        if "text" in mime_type:
            return "texto"
        elif "pdf" in mime_type:
            return "pdf"
        elif "csv" in mime_type:
            return "csv"
        elif "json" in mime_type:
            return "json"
        elif "image" in mime_type:
            return "imagen"
    return "desconocido"

def analizar_texto(file_path):
    """Lee y analiza archivos de texto."""
    with open(file_path, 'r', encoding='utf-8') as file:
        contenido = file.read()
    palabras = len(contenido.split())
    return f"📃 Texto analizado: {palabras} palabras.\nPrimeras líneas:\n{contenido[:300]}..."

def analizar_csv(file_path):
    """Lee y analiza archivos CSV."""
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        filas = list(reader)
    columnas = len(filas[0]) if filas else 0
    filas_count = len(filas)
    return f"📊 CSV analizado: {filas_count} filas y {columnas} columnas.\nPrimeras filas:\n{filas[:5]}"

def analizar_json(file_path):
    """Lee y analiza archivos JSON."""
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    keys = ", ".join(data.keys()) if isinstance(data, dict) else "No es un objeto JSON válido"
    return f"📂 JSON analizado: Claves principales: {keys}"

def analizar_pdf(file_path):
    """Lee y analiza archivos PDF."""
    doc = fitz.open(file_path)
    texto = ""
    for page_num in range(min(5, len(doc))):
        texto += doc.load_page(page_num).get_text()
    palabras = len(texto.split())
    return f"📑 PDF analizado: {palabras} palabras.\nPrimeras líneas:\n{texto[:300]}..."

def analizar_imagen(file_path):
    """Simula un análisis de imagen (OCR o descripción)."""
    return "🖼️ Imagen analizada: (simulación de análisis de imagen)"

def analizar_sentimiento(texto):
    """Analiza la emoción de un mensaje y devuelve su intensidad."""
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=texto, type_=language_v1.Document.Type.PLAIN_TEXT)

    response = client.analyze_sentiment(request={"document": document})
    score = response.document_sentiment.score
    magnitude = response.document_sentiment.magnitude

    return score, magnitude  # Score: positivo o negativo, Magnitude: intensidad

def analizar_entidades(texto):
    """Analiza entidades en un mensaje de chat y devuelve los términos más importantes."""
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=texto, type_=language_v1.Document.Type.PLAIN_TEXT)

    response = client.analyze_entities(request={"document": document})

    entidades = []
    for entity in response.entities:
        entidades.append({
            "nombre": entity.name,
            "tipo": language_v1.Entity.Type(entity.type_).name,
            "importancia": entity.salience
        })

    return entidades

def verificar_resumenes():
    """Ejecuta el módulo de resúmenes en intervalos regulares, evitando resúmenes duplicados."""
    while True:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT usuario_id FROM mensajes_usuario
                WHERE usuario_id NOT IN (
                    SELECT usuario_id FROM resumenes_usuario
                    WHERE timestamp >= datetime('now', '-24 hours')
                )
                GROUP BY usuario_id
                HAVING COUNT(*) >= 10
            """)
            usuarios = [row[0] for row in cursor.fetchall()]

        for usuario_id in usuarios:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT contenido FROM mensajes_usuario
                    WHERE usuario_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 25
                """, (usuario_id,))
                mensajes = cursor.fetchall()

            if not mensajes:
                continue

            # Combinar todos los mensajes en un texto largo
            texto_unido = "\n".join([msg[0] for msg in mensajes])

            # Usar OpenAI para generar el resumen
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Resume el comportamiento del jugador con base en estas frases. Detecta intereses, tono, y hábitos. Sé claro y conciso."},
                        {"role": "user", "content": texto_unido[:3000]}  # Límite de tokens
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                resumen = response.choices[0].message.content.strip()

                # Guardar en la tabla resumenes_usuario
                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO resumenes_usuario (usuario_id, sesion_id, resumen)
                        VALUES (?, ?, ?)
                    """, (usuario_id, "sesion_rust", resumen))
                    conn.commit()

                logging.info(f"🧠 Resumen generado y guardado para usuario {usuario_id}")

            except Exception as e:
                logging.warning(f"⚠️ Error al generar resumen para {usuario_id}: {e}")

        logging.info("⌛ Esperando 1 hora antes de la próxima revisión de resúmenes...")
        time.sleep(3600)  # Espera 1 hora

if __name__ == "__main__":
    db = Database(DB_FILE)
    openai_client = OpenAIClient(OPENAI_API_KEY)
    app = FlaskApp(db, openai_client)
    threading.Thread(target=verificar_resumenes, daemon=True).start()
    app.run()
