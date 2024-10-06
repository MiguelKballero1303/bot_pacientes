from flask import Flask, request, jsonify
import re
from transformers import pipeline
import torch

# Umbral de ingresos en soles
INCOME_THRESHOLD = 2000  

# Cargar el modelo y pipeline de generación de texto
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # Cambia a "cuda" si tienes una GPU
text_generator = pipeline('text-generation', model='datificate/gpt2-small-spanish', device=device, batch_size=1)

def analyze_message(patient_message: str):
    income_match = re.search(r"ingreso.*?(\d+)", patient_message, re.IGNORECASE)
    income = int(income_match.group(1)) if income_match else None

    mental_health_conditions = ["depresión", "ansiedad", "estrés postraumático"]
    mental_health_condition = next((condition for condition in mental_health_conditions if re.search(condition, patient_message, re.IGNORECASE)), None)

    employment_status = "unemployed" if re.search(r"desemplead[oa]", patient_message, re.IGNORECASE) else \
                        "part-time" if re.search(r"medio tiempo|parcial", patient_message, re.IGNORECASE) else None

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

app = Flask(__name__)

@app.route("/bot-response", methods=["POST"])
def bot_response():
    data = request.json
    patient_message = data.get("message", "")

    initial_response = "¡Hola! Soy el asistente de salud mental. ¿Cómo puedo ayudarte hoy? Proporciona más información sobre tu situación."

    if not patient_message.strip():
        return jsonify({"response": initial_response})

    patient_data = analyze_message(patient_message)
    name = patient_data.get("name", "Paciente")
    last_name = patient_data.get("last_name", "")
    income = patient_data.get("income")
    mental_health_condition = patient_data.get("mental_health_condition", "")
    employment_status = patient_data.get("employment_status", "")

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

    try:
        input_prompt = input_prompt[:512]  # Limitar la longitud de entrada
        generated_response = text_generator(input_prompt, max_length=50, num_return_sequences=1, truncation=True)[0]['generated_text'].strip()
        generated_response = generated_response.split(".")[0]  # Limitar la respuesta a una oración
    except Exception as e:
        print(f"Error al generar respuesta: {e}")  # Imprimir el error en la consola para depuración
        return jsonify({"response": "Lo siento, ocurrió un error al generar la respuesta."})

    return jsonify({"response": generated_response})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
