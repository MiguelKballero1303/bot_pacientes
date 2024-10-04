from flask import Flask, request, jsonify
import re

# Definir el umbral y criterios para calificar para el descuento
INCOME_THRESHOLD = 2000  # Umbral de ingresos en soles

# Función para analizar el mensaje y extraer datos clave
def analyze_message(patient_message: str):
    income_match = re.search(r"ingreso.*?(\d+)", patient_message, re.IGNORECASE)
    income = int(income_match.group(1)) if income_match else None

    mental_health_conditions = ["depresión", "ansiedad", "estrés postraumático"]
    mental_health_condition = None
    for condition in mental_health_conditions:
        if re.search(condition, patient_message, re.IGNORECASE):
            mental_health_condition = condition
            break

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

    if re.search(r"\b(hola|buenos días|buenas tardes|buenas noches)\b", patient_message, re.IGNORECASE):
        return jsonify({
            "response": "Buenos días estimado(a) paciente, te saludo MiguelonBot. Coméntame más a detalle tu situación económica y social."
        })

    # Analizar el mensaje
    patient_data = analyze_message(patient_message)
    name = patient_data.get("name", "Paciente")
    last_name = patient_data.get("last_name", "")
    income = patient_data.get("income")
    mental_health_condition = patient_data.get("mental_health_condition", "")
    employment_status = patient_data.get("employment_status", "")

    if income is None:
        return jsonify({"response": f"{name}, no pudimos determinar tus ingresos. Por favor, proporciona más información."})

    qualifies = False
    if income < INCOME_THRESHOLD:
        qualifies = True
    if mental_health_condition in ["depresión", "ansiedad", "estrés postraumático"]:
        qualifies = True
    if employment_status in ["unemployed", "part-time"]:
        qualifies = True

    if qualifies:
        response_text = f"{name} {last_name}, calificas para un 90% de descuento en sesiones psicológicas remotas."
    else:
        response_text = f"{name} {last_name}, no calificas para el descuento."

    return jsonify({"response": response_text})

if __name__ == "__main__":
    app.run(debug=True)
