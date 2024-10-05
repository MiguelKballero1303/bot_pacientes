from flask import Flask, request, jsonify
import re
from transformers import pipeline

# Umbral de ingresos en soles
INCOME_THRESHOLD = 2000  

# Inicializar el pipeline de generación de texto de Hugging Face con un modelo eficiente
text_generator = pipeline('text-generation', model='distilgpt2', device=-1, batch_size=1)

def analyze_message(patient_message: str):
    # Usar expresiones regulares para extraer datos
    income_match = re.search(r"ingreso.*?(\d+)", patient_message, re.IGNORECASE)
    income = int(income_match.group(1)) if income_match else None

    mental_health_condition = next((condition for condition in ["depresión", "ansiedad", "estrés postraumático"] 
                                     if re.search(condition, patient_message, re.IGNORECASE)), None)

    employment_status = "unemployed" if re.search(r"desemplead[oa]", patient_message, re.IGNORECASE) else \
                        "part-time" if re.search(r"medio tiempo|parcial", patient_message, re.IGNORECASE) else None

    # Utilizando métodos simples para capturar información
    name = (re.search(r"soy ([A-Za-z ]+)", patient_message, re.IGNORECASE) or ["Paciente"])[1]
    last_name = (re.search(r"apellido ([A-Za-z ]+)", patient_message, re.IGNORECASE) or [""])[1]
    dni = (re.search(r"dni (\d+)", patient_message, re.IGNORECASE) or [""])[1]
    celular = (re.search(r"celular (\d+)", patient_message, re.IGNORECASE) or [""])[1]
    correo = (re.search(r"correo ([\w\.-]+@[\w\.-]+)", patient_message, re.IGNORECASE) or [""])[1]

    return {
        "name": name.strip(),
        "last_name": last_name.strip(),
        "dni": dni.strip(),
        "celular": celular.strip(),
        "correo": correo.strip(),
        "income": income,
        "mental_health_condition": mental_health_condition,
        "employment_status": employment_status,
    }

app = Flask(__name__)

@app.route("/bot-response", methods=["POST"])
def bot_response():
    data = request.json
    patient_message = data.get("message", "").strip()

    initial_response = "¡Hola! Soy el asistente de salud mental. ¿Cómo puedo ayudarte hoy?"

    if not patient_message:
        return jsonify({"response": initial_response})

    patient_data = analyze_message(patient_message)
    name = patient_data.get("name", "Paciente")
    last_name = patient_data.get("last_name", "")
    income = patient_data.get("income")
    mental_health_condition = patient_data.get("mental_health_condition", "")
    employment_status = patient_data.get("employment_status", "")

    # Calcular la calificación para el descuento
    qualifies = (
        income is not None and 
        (income < INCOME_THRESHOLD or
         mental_health_condition in ["depresión", "ansiedad", "estrés postraumático"] or
         employment_status in ["unemployed", "part-time"])
    )

    input_prompt = f"{name} {last_name}, " + (
        "calificas para un 90% de descuento en sesiones psicológicas remotas." 
        if qualifies else 
        "no calificas para el descuento. Por favor, contáctanos para más detalles."
    )

    try:
        input_prompt = input_prompt[:512]
        generated_response = text_generator(input_prompt, max_length=50, num_return_sequences=1, truncation=True)[0]['generated_text'].strip()
        generated_response = generated_response.split(".")[0]
    except Exception:
        return jsonify({"response": "Lo siento, ocurrió un error al generar la respuesta."})

    return jsonify({"response": generated_response})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
