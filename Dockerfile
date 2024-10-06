# Usa una imagen base de Python
FROM python:3.9

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de requisitos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de tu código
COPY . .

# Expone el puerto que usará tu aplicación
EXPOSE 5000

# Comando para ejecutar tu aplicación Flask
CMD ["python", "patient_discount_bot.py"]
