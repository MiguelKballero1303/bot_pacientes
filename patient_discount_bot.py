from flask import Flask, request, jsonify
import re
from transformers import pipeline

# Definir el umbral y criterios para calificar para el descuento
INCOME_THRESHOLD = 2000  # Umbral de ingresos en soles

# Inicializar un pipeline de generación de texto de Hugging Face con un modelo más eficiente
text_generator = pipeline('text-generation', model='distilgpt2', device=-1)  # Usa CPU

# Función para analizar el mensaje y extraer datos clave
def analyze_message(patient_message: str):
    income_match = re.search(r"ingreso.*?(\d+)", patient_message, re.IGNORECASE)
    income = int(income_match.group(1)) if income_match else None

    mental_health_conditions = ["depresión", "ansiedad", "estrés postraumático"]
    mental_health_condition = next((condition for condition in mental_health_conditions if re.search(condition, patient_message, re.IGNORECASE)), None)

    employment_status = None
    if re.search(r"desemplead[oa]", patient_message, re.IGNORECASE):
        employment_status = "unemployed"
    elif re.search(r"medio tiempo|parcial", patient_message, re.IGNORECASE):
        employment_status = "part-time"

    name_match = re.search(r"soy ([A-Za-z ]+)", patient_message, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else "Paciente"

    last_name_match = re.search(r"apellido ([A-Za-z ]+)", patient_message, re.IGNORECASE)
    last_name = last_name_match.group(1).strip() if last_name_match else ""

    dni_match = re.search(r"dni (\d+)", patient_message, re.IGNORECASE)
    dni = dni_match.group(1).strip() if dni_match else ""

    celular_match = re.search(r"celular (\d+)", patient_message, re.IGNORECASE)
    celular = celular_match.group(1).strip() if celular_match else ""

    correo_match = re.search(r"correo ([\w\.-]+@[\w\.-]+)", patient_message, re.IGNORECASE)
    correo = correo_match.group(1).strip() if correo_match else ""

    return {
        "name": name,
        "last_name": last_name,
        "dni": dni,
        "celular": celular,
        "correo": correo,
        "income": income,
        "mental_health_condition": mental_health_condition,
        "employment_status": employment_status,
    }

# Inicializar Flask
app = Flask(__name__)

@app.route("/bot-response", methods=["POST"])
def bot_response():
    # Obtener el mensaje del paciente desde el request
    data = request.json
    patient_message = data.get("message", "")

    # Saludo inicial
    initial_response = "¡Hola! Soy el asistente de salud mental. ¿Cómo puedo ayudarte hoy? Por favor, proporciona información sobre tu situación."

    # Si el mensaje está vacío, retorna el saludo inicial
    if not patient_message.strip():
        return jsonify({"response": initial_response})

    # Analizar el mensaje
    patient_data = analyze_message(patient_message)
    name = patient_data.get("name", "Paciente")
    last_name = patient_data.get("last_name", "")
    income = patient_data.get("income")
    mental_health_condition = patient_data.get("mental_health_condition", "")
    employment_status = patient_data.get("employment_status", "")

    # Generar respuesta personalizada según la información del paciente
    if income is None:
        input_prompt = f"{name}, no pudimos determinar tus ingresos. Proporciona más información sobre tus ingresos."
    else:
        qualifies = (income < INCOME_THRESHOLD or
                     mental_health_condition in ["depresión", "ansiedad", "estrés postraumático"] or
                     employment_status in ["unemployed", "part-time"])

        if qualifies:
            input_prompt = f"{name} {last_name}, calificas para un 90% de descuento en sesiones psicológicas remotas."
        else:
            input_prompt = f"{name} {last_name}, no calificas para el descuento. Por favor, contáctanos para más detalles."

    # Usar el modelo de lenguaje para generar una respuesta
    generated_response = text_generator(input_prompt, max_length=50, num_return_sequences=1, truncation=True)[0]['generated_text'].strip()
    
    # Asegurarse de que la respuesta no contenga texto adicional no deseado
    generated_response = generated_response.split(".")[0]  # Tomar solo el primer fragmento

    # Devolver la respuesta generada
    return jsonify({"response": generated_response})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)  # Asegúrate de que esté accesible desde cualquier IP
