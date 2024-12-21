import pyodbc
from flask import Flask, request, jsonify
from flask_cors import CORS  # Importa CORS
from flask import Flask, send_file
import pandas as pd
from flask import Response
from reportlab.pdfgen import canvas
import io
app = Flask(__name__ ,template_folder='C:\\Users\\uguaj\\Desktop\\Fepi')
CORS(app) 

# Configuración de conexión con SQL Server
SERVER = 'LAPTOP-UVKCPH83'
DATABASE = 'Concesionaria'
USERNAME = 'Ulises'
PASSWORD = 'ulises1234'
DRIVER = 'ODBC Driver 17 for SQL Server'

def get_db_connection():
    """Establece la conexión a SQL Server."""
    conn = pyodbc.connect(
        f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"
    )
    return conn

def convierteBinario(imagen_file):
    """Convierte una imagen cargada en binario."""
    try:
        return imagen_file.read()
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None

@app.route("/registro_auto", methods=["POST"])
def registrar_auto():
    """Registra un auto en la base de datos."""
    try:
        # Captura de datos del formulario
        marca = request.form.get('marca')
        modelo = request.form.get('modelo')
        ano = request.form.get('ano')
        color = request.form.get('color')
        kilometraje = request.form.get('kilometraje')
        estado = request.form.get('estado')
        precio = request.form.get('precio')
        vin = request.form.get('vin')
        observaciones = request.form.get('observaciones')

        # Captura de las imágenes
        imagenes = request.files.getlist('imagenes')
        imagen_binaria = convierteBinario(imagenes[0]) if imagenes else None

        # Inserta los datos en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO vehiculos (marca, modelo, año, color, kilometraje, estado_inicial, precio, Numero_de_seie, observaciones, imagen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (marca, modelo, ano, color, kilometraje, estado, precio, vin, observaciones, imagen_binaria))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Auto registrado exitosamente"})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route("/inventario")
def inventario():
    """Obtiene los datos de los autos de la base de datos en formato JSON."""
    try:
        # Conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consulta de los autos en el inventario, incluyendo el Numero_de_serie (VIN)
        query = "SELECT Numero_de_seie, marca, modelo, año, kilometraje, estado_inicial, precio, fecha_entrada FROM vehiculos"
        cursor.execute(query)

        # Obtención de los resultados
        autos = cursor.fetchall()

        # Formatear los datos a un formato adecuado para JSON
        autos_data = []
        for auto in autos:
            fecha_entrada = auto[7]  # fecha_entrada es el séptimo campo (índice 7)

            # Verificamos si fecha_entrada es None
            if fecha_entrada:
                fecha_entrada = fecha_entrada.strftime("%Y-%m-%d")  # Formato de fecha
            else:
                fecha_entrada = "N/A"  # Valor por defecto si la fecha es None

            autos_data.append({
                'vin': auto[0],  # Ahora incluimos Numero_de_serie como vin
                'marca': auto[1],
                'modelo': auto[2],
                'ano': auto[3],
                'kilometraje': auto[4],
                'estado_inicial': auto[5],
                'precio': auto[6],
                'fecha_entrada': fecha_entrada  # Usamos el valor procesado de fecha_entrada
            })

        cursor.close()
        conn.close()

        return jsonify(autos_data)  # Devolver los datos como JSON

    except Exception as e:
        print(f"Error al obtener datos de la base de datos: {e}")
        return jsonify({"error": "Error al obtener los datos"}), 500
    

@app.route("/registro_venta", methods=["POST"])
def registrar_venta():
    """Registra una venta en la base de datos."""
    try:
        # Captura de datos del formulario
        nombre_comprador = request.form.get('nombre-comprador')
        telefono_comprador = request.form.get('telefono-comprador')
        correo_comprador = request.form.get('correo-comprador')
        forma_pago = request.form.get('forma-pago')
        enganche = request.form.get('enganche')
        plazo_financiamiento = request.form.get('plazo-financiamiento')
        tasa_interes = request.form.get('tasa-interes')
        fecha_venta = request.form.get('fecha-venta')
        precio_venta = request.form.get('precio-venta')
        observaciones = request.form.get('observaciones')

        # Verificar si el enganche, plazo y tasa de interés son vacíos y asignar valores por defecto si es necesario
        enganche = float(enganche) if enganche else 0.0
        plazo_financiamiento = int(plazo_financiamiento) if plazo_financiamiento else 0
        tasa_interes = float(tasa_interes) if tasa_interes else 0.0

        # Conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Consulta para insertar los datos en la tabla de ventas
        query = """
            INSERT INTO Ventas (nombre_comprador, telefono_comprador, correo_comprador, forma_pago, enganche, 
                                plazo_financiamiento, tasa_interes, fecha_venta, precio_venta, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Ejecutar la consulta con los valores del formulario
        cursor.execute(query, (nombre_comprador, telefono_comprador, correo_comprador, forma_pago, enganche, 
                               plazo_financiamiento, tasa_interes, fecha_venta, precio_venta, observaciones))

        # Confirmar los cambios en la base de datos
        conn.commit()
        cursor.close()
        conn.close()

        # Respuesta de éxito
        return jsonify({"status": "success", "message": "Venta registrada exitosamente"})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Ruta para exportar a Excel
@app.route('/exportar_excel', methods=['GET'])
def exportar_excel():
    try:
        # Conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query para obtener datos del inventario
        consulta = "SELECT * FROM vehiculos"  # Ajusta el nombre de la tabla
        datos = pd.read_sql(consulta, conn)
        
        # Crear archivo Excel
        nombre_archivo = "inventario.xlsx"
        datos.to_excel(nombre_archivo, index=False)

        # Retornar el archivo al cliente
        return send_file(nombre_archivo, as_attachment=True)

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        cursor.close()
        conn.close()
    

@app.route('/descargar_pdf', methods=['GET'])
def descargar_pdf():
    # Crear un archivo PDF en blanco en memoria
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    
    # Añadir contenido básico al PDF (opcional)
    pdf.drawString(100, 750, "Este es un PDF generado dinámicamente.")
    pdf.save()

    buffer.seek(0)

    # Retornar el PDF al cliente
    return Response(
        buffer,
        mimetype='application/pdf',
        headers={"Content-Disposition": "attachment;filename=archivo.pdf"}
    )



if __name__ == '__main__':
    app.run(debug=True)