from flask import Flask, request, jsonify
from flask_cors import CORS 
import re
from transformers import pipeline
import torch

INCOME_THRESHOLD = 2000

device = "cuda" if torch.cuda.is_available() else "cpu"
text_generator = pipeline('text-generation', model='datificate/gpt2-small-spanish', device=device)

def analyze_message_with_gpt(patient_message: str):
    prompt = f"Extrae la siguiente información de este mensaje: '{patient_message}'"
    response = text_generator(prompt, max_length=150, num_return_sequences=1, truncation=True)[0]['generated_text']
    print("Respuesta generada por el modelo:", response)
    return response

def extract_patient_data(patient_message: str):
    name_match = re.search(r"(Hola soy|Mi nombre es|Yo soy|Soy)\s*([A-Za-z áéíóúü]+)", patient_message, re.IGNORECASE)
    last_name_match = re.search(r"apellido es ([A-Za-z áéíóúü]+)", patient_message, re.IGNORECASE)
    dni_match = re.search(r"DNI:\s*(\d+)", patient_message, re.IGNORECASE)
    celular_match = re.search(r"celular:\s*(\d+)", patient_message, re.IGNORECASE)
    correo_match = re.search(r"correo:\s*([\w\.-]+@[\w\.-]+)", patient_message, re.IGNORECASE)
    income_match = re.search(r"ingreso de (\d+)", patient_message, re.IGNORECASE)
    employment_status_match = re.search(r"estoy (desempleado|trabajando a tiempo parcial)", patient_message, re.IGNORECASE)

    return {
        "name": name_match.group(2).strip() if name_match else "",
        "last_name": last_name_match.group(1).strip() if last_name_match else "",
        "dni": dni_match.group(1).strip() if dni_match else "",
        "celular": celular_match.group(1).strip() if celular_match else "",
        "correo": correo_match.group(1).strip() if correo_match else "",
        "income": int(income_match.group(1)) if income_match else None,
        "employment_status": employment_status_match.group(1).strip() if employment_status_match else None,
        "mental_health_condition": None
    }

app = Flask(__name__)
CORS(app)

@app.route("/bot-response", methods=["POST"])
def bot_response():
    data = request.json
    patient_message = data.get("message", "")

    initial_response = "¡Hola! Soy el asistente de salud mental. ¿Cómo puedo ayudarte hoy?"

    if not patient_message.strip():
        return jsonify({"response": initial_response})

    patient_data = extract_patient_data(patient_message)

    if not patient_data["name"]:
        gpt_response = analyze_message_with_gpt(patient_message)
        patient_data = extract_patient_data(gpt_response)

    print("Datos extraídos:", patient_data)

    name = patient_data["name"]
    income = patient_data.get("income")

    input_prompt = ""
    qualifies = False

    if income is None:
        input_prompt = f"{name}, no pudimos determinar tus ingresos. Proporciona más información sobre tus ingresos."
    else:
        qualifies = income <= INCOME_THRESHOLD

        if qualifies:
            input_prompt = f"{name}, calificas para un 90% de descuento en sesiones psicológicas remotas."
        else:
            input_prompt = f"{name}, no calificas para el descuento. Por favor, contáctanos para más detalles."

    print("Prompt de entrada:", input_prompt)

    response_data = {"patient_response": input_prompt}

    if income is not None and qualifies:
        response_data["registration_data"] = patient_data

    return jsonify(response_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
