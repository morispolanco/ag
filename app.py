import streamlit as st
import pandas as pd
import requests
import json
import datetime
import io
import os

st.set_page_config(
    page_title="Ecosistema de agentes inteligentes",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados para crear una UI premium, limpia y adaptativa
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; }
    .stAlert p { margin-bottom: 0; }
    .agent-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 12px;
        background-color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .dark .agent-card {
        background-color: #1e293b;
        border-color: #334155;
    }
    .chat-bubble {
        padding: 14px 20px;
        border-radius: 12px;
        margin-bottom: 12px;
        max-width: 80%;
        line-height: 1.6;
        font-size: 15px;
    }
    .user-bubble { 
        background-color: #e0f2fe; 
        color: #0369a1;
        margin-left: auto; 
        border-bottom-right-radius: 2px;
        border-right: 4px solid #0284c7;
    }
    .agent-bubble { 
        background-color: #f1f5f9; 
        color: #1e293b;
        margin-right: auto; 
        border-bottom-left-radius: 2px;
        border-left: 4px solid #10b981;
    }
    .metric-container {
        background: #ffffff;
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: center;
    }
    .dark .metric-container {
        background: #0f172a;
        border-color: #1e293b;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CONSTANTES Y PLANTILLAS DE DATOS
# ==========================================
DB_FILE = "db.json"

PLANTILLAS_CSV = {
    "inventario": (
        "ID_Producto,Producto,Categoria,Cantidad,Costo_Unitario,Precio_Venta,Rotacion,Stock_Minimo\n"
        "FERR001,Rotomartillo Industrial DeWalt 20V Max,Herramientas Eléctricas,35,189.90,279.99,Alta,8\n"
        "FERR002,Pintura Impermeabilizante Corona Ultra 5 Galones,Pinturas,85,65.00,110.00,Alta,15\n"
        "FERR003,Cemento Portland Gris ASTM C-150 (Saco 50kg),Construcción,1200,6.20,8.50,Alta,200\n"
        "FERR004,Juego Llaves de Impacto Stanley FatMax 24 pzs,Herramientas Manuales,25,45.00,79.99,Media,6\n"
        "FERR005,Tubo Cobre Tipo M 1/2 pulgada x 6m,Fontanería,300,14.50,22.00,Media,50\n"
        "FERR006,Caja Clavos de Acero Corrugado 3pulg (20kg),Fijaciones,40,28.00,45.00,Baja,10\n"
        "FERR007,Planta de Soldar Inverter Lincoln Electric 250A,Maquinaria,12,380.00,599.00,Media,3\n"
        "FERR008,Varilla de Acero Grado 40 3/8pulg x 6m,Construcción,2500,2.90,4.25,Alta,500\n"
        "FERR009,Generador Eléctrico Trifásico Honda 6500W,Maquinaria,6,850.00,1350.00,Baja,2\n"
        "FERR010,Cerradura Digital Inteligente Yale Real Living,Cerrajería,45,115.00,189.00,Alta,10\n"
        "FERR011,Escalera de Aluminio Extensible Tipo IA 28 pies,Equipamiento,15,145.00,229.00,Media,4\n"
        "FERR012,Lámina de Zinc Acanalada Calibre 26 3.66m,Construcción,800,11.20,16.50,Alta,150\n"
        "FERR013,Cable Eléctrico Cobre THHN 10 AWG (Rollo 100m),Electricidad,60,55.00,89.00,Alta,12\n"
        "FERR014,Compresor de Aire Evans 3HP 100L,Maquinaria,8,290.00,450.00,Media,3\n"
        "FERR015,Casco de Seguridad de Fibra de Vidrio MSA,Seguridad Industrial,150,12.50,22.00,Alta,30"
    ),
    "caja": (
        "Fecha,Concepto,Categoria,Ingreso,Egreso,Saldo_Acumulado,Metodo_Pago\n"
        "2026-06-10,Saldo inicial operativo en Bancos,Apertura,45000.00,0.00,45000.00,Transferencia\n"
        "2026-06-11,Despacho materiales pesados Constructora del Norte,Ventas,18500.00,0.00,63500.00,Transferencia\n"
        "2026-06-12,Pago flete y fletamiento logístico cementera,Logística,0.00,1250.00,62250.00,Cheque\n"
        "2026-06-13,Compra inventario herramientas DeWalt y Stanley,Inventario,0.00,8500.00,53750.00,Transferencia\n"
        "2026-06-14,Venta mostrador flotilla de taladros industriales,Ventas,3250.00,0.00,57000.00,Tarjeta\n"
        "2026-06-14,Gasto de campaña publicitaria temporada de lluvias,Mercadeo,0.00,850.00,56150.00,Tarjeta\n"
        "2026-06-15,Cobro factura crédito Corporación Inmobiliaria Beta,Ventas,14200.00,0.00,70350.00,Transferencia\n"
        "2026-06-15,Pago importación de soldadoras Lincoln Electric,Inventario,0.00,4560.00,65790.00,Transferencia\n"
        "2026-06-16,Adquisición de equipo de seguridad industrial MSA,Inventario,0.00,1875.00,63915.00,Transferencia\n"
        "2026-06-16,Nómina quincenal personal operativo y asesores,Planilla,0.00,6500.00,57415.00,Transferencia\n"
        "2026-06-17,Pago de servicios generales (Luz trifásica - Internet),Servicios,0.00,480.00,56935.00,Debito\n"
        "2026-06-17,Ventas del día canal mostrador minorista,Ventas,4890.00,0.00,61825.00,Efectivo"
    ),
    "mercadeo": (
        "ID_Campana,Campana,Canal,Presupuesto_Asignado,Gasto_Actual,Leads_Generados,Conversiones,Estado\n"
        "CAMP001,Temporada sin Filtraciones (Impermeabilizantes),Meta Ads,1200.00,980.00,850,115,Activa\n"
        "CAMP002,Descuento Mayorista para Contratistas,Email Marketing,300.00,240.00,420,85,Activa\n"
        "CAMP003,Expo-Herramientas Stanley FatMax,Google Ads,600.00,600.00,340,48,Completada\n"
        "CAMP004,Seguridad Industrial Primero (MSA),TikTok Ads,500.00,250.00,290,22,Activa\n"
        "CAMP005,Maquinaria Lincoln Electric Profesional,Google Ads,1500.00,1100.00,480,35,Activa\n"
        "CAMP006,Descuento Estructural Acero y Cemento,WhatsApp Business,150.00,120.00,950,142,Activa\n"
        "CAMP007,Pinturas Exterior de Alto Tránsito,Meta Ads,800.00,800.00,410,54,Completada"
    ),
    "impuestos": (
        "Periodo,Impuesto,Base_Imponible,Tasa,Monto_Determinado,Estado_Pago,Fecha_Vencimiento\n"
        "2026-05,IVA General Mensual Ferretería Grande,145000.00,0.12,17400.00,Presentado,2026-06-30\n"
        "2026-05,Retenciones ISR de Clientes Constructores,55000.00,0.05,2750.00,Presentado,2026-06-28\n"
        "2026-05,Impuesto Sobre la Renta (ISR) Corporativo,120000.00,0.07,8400.00,Pendiente,2026-07-15\n"
        "2026-06,Provisión Mensual IVA Estimado,65000.00,0.12,7800.00,Pendiente,2026-07-31\n"
        "2026-06,ISR Retenciones por Planilla Laboral,28000.00,0.05,1400.00,Pendiente,2026-07-10\n"
        "2026-05,Impuesto de Operación y Licencia Comercial,45000.00,0.015,675.00,Presentado,2026-06-30"
    )
}

BLANCO_INVENTARIO = "ID_Producto,Producto,Categoria,Cantidad,Costo_Unitario,Precio_Venta,Rotacion,Stock_Minimo\n"
BLANCO_CAJA = "Fecha,Concepto,Categoria,Ingreso,Egreso,Saldo_Acumulado,Metodo_Pago\n"
BLANCO_MERCADEO = "ID_Campana,Campana,Canal,Presupuesto_Asignado,Gasto_Actual,Leads_Generados,Conversiones,Estado\n"
BLANCO_IMPUESTOS = "Periodo,Impuesto,Base_Imponible,Tasa,Monto_Determinado,Estado_Pago,Fecha_Vencimiento\n"

# ==========================================
# MANEJO DE BASE DE DATOS (JSON PERSISTENTE)
# ==========================================
def cargar_db():
    default_demo_data = {
        "password": "demo123",
        "autorizado": True,
        "rol": "usuario",
        "config_empresa": {
            "nombre": "Ferretería Industrial El Tornillo Gigante, S.A.",
            "tipo": "Ferretería Industrial, Mayorista y Materiales de Construcción Pesada",
            "direccion": "Calzada Aguilar Batres 34-10, Zona 11, Ciudad de Guatemala",
            "nit": "9876543-2",
            "metas": "Maximizar la rotación de materiales pesados (cemento, varilla de acero), optimizar el inventario de herramientas de alto valor (soldadoras Lincoln, rotomartillos DeWalt) y proyectar el flujo de caja para cumplir con las obligaciones tributarias de gran escala.",
            "moneda": "Q"
        },
        "datos_empresa": {
            "inventario": pd.read_csv(io.StringIO(PLANTILLAS_CSV["inventario"])).to_dict(orient="records"),
            "caja": pd.read_csv(io.StringIO(PLANTILLAS_CSV["caja"])).to_dict(orient="records"),
            "mercadeo": pd.read_csv(io.StringIO(PLANTILLAS_CSV["mercadeo"])).to_dict(orient="records"),
            "impuestos": pd.read_csv(io.StringIO(PLANTILLAS_CSV["impuestos"])).to_dict(orient="records")
        },
        "tareas": [
            {"id": 1, "agente": "Financiero", "descripcion": "Validar liquidez en Bancos para cubrir la importación de soldadoras Lincoln Electric.", "estado": "Pendiente", "fecha": "2026-06-14"},
            {"id": 2, "agente": "Inventario", "descripcion": "Supervisar stock de Cemento Portland ASTM C-150 (sugerir reorden si baja de 200 sacos).", "estado": "Pendiente", "fecha": "2026-06-14"},
            {"id": 3, "agente": "Impuestos", "descripcion": "Liquidar el ISR Corporativo de Mayo antes del vencimiento oficial del 15 de julio.", "estado": "Pendiente", "fecha": "2026-06-14"},
            {"id": 4, "agente": "Mercadeo", "descripcion": "Monitorear la efectividad y leads de la campaña de Impermeabilizantes en Meta Ads.", "estado": "Pendiente", "fecha": "2026-06-14"}
        ],
        "historial_chat": [
            {"rol": "Director General", "mensaje": "Saludos del Director General de Ferretería Industrial El Tornillo Gigante, S.A. He verificado nuestro pizarrón central y poseo visibilidad completa de nuestro inventario mayorista, balances de flujo en bancos, obligaciones impositivas y presupuestos publicitarios. ¿Qué estrategias operativas coordinaremos el día de hoy?"}
        ]
    }

    if not os.path.exists(DB_FILE):
        db = {
            "usuarios": {
                "admin@empresa.com": {
                    "password": "admin123",
                    "autorizado": True,
                    "rol": "admin"
                },
                "demo@ferreteria.com": default_demo_data
            }
        }
        guardar_db(db)
        return db
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            db = json.load(f)
        
        if "demo@ferreteria.com" in db["usuarios"]:
            demo_user = db["usuarios"]["demo@ferreteria.com"]
            if len(demo_user.get("datos_empresa", {}).get("inventario", [])) < 10:
                demo_user["config_empresa"] = default_demo_data["config_empresa"]
                demo_user["datos_empresa"] = default_demo_data["datos_empresa"]
                demo_user["tareas"] = default_demo_data["tareas"]
                demo_user["historial_chat"] = default_demo_data["historial_chat"]
                guardar_db(db)
        else:
            db["usuarios"]["demo@ferreteria.com"] = default_demo_data
            guardar_db(db)
            
        return db
    except Exception:
        return {"usuarios": {}}

def guardar_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
    except Exception as e:
        st.error(f"Fallo al guardar en base de datos: {str(e)}")

def guardar_datos_usuario_actual():
    if st.session_state.get("logged_in") and st.session_state.get("rol_actual") != "admin":
        db = cargar_db()
        email = st.session_state.usuario_actual
        if email in db["usuarios"]:
            db["usuarios"][email]["config_empresa"] = st.session_state.config_empresa
            db["usuarios"][email]["datos_empresa"] = {
                k: v.to_dict(orient="records") if isinstance(v, pd.DataFrame) else v
                for k, v in st.session_state.datos_empresa.items()
            }
            db["usuarios"][email]["tareas"] = st.session_state.tareas
            db["usuarios"][email]["historial_chat"] = st.session_state.historial_chat
            guardar_db(db)

# ==========================================
# CONTROL DE SESIONES E INICIO DE SESIÓN
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.usuario_actual = ""
    st.session_state.rol_actual = ""

db_actual = cargar_db()

if not st.session_state.logged_in:
    st.title("🏢 Ecosistema de agentes inteligentes")
    st.subheader("Control corporativo multi-agente con IA")
    
    col_log1, col_log2, col_log3 = st.columns([1, 1.5, 1])
    with col_log2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.form("form_inicio_sesion", clear_on_submit=False):
            st.markdown("### 🔐 Acceso autorizado")
            correo_ingresado = st.text_input("Correo electrónico:", placeholder="ejemplo@empresa.com").strip().lower()
            password_ingresado = st.text_input("Contraseña:", type="password", placeholder="••••••••")
            boton_login = st.form_submit_button("Iniciar sesión")
            
            if boton_login:
                if correo_ingresado in db_actual["usuarios"]:
                    datos_usr = db_actual["usuarios"][correo_ingresado]
                    if datos_usr["password"] == password_ingresado:
                        if datos_usr.get("autorizado", False):
                            st.session_state.logged_in = True
                            st.session_state.usuario_actual = correo_ingresado
                            st.session_state.rol_actual = datos_usr.get("rol", "usuario")
                            
                            if st.session_state.rol_actual != "admin":
                                st.session_state.config_empresa = datos_usr["config_empresa"]
                                st.session_state.datos_empresa = {
                                    k: pd.DataFrame(v) for k, v in datos_usr["datos_empresa"].items()
                                }
                                st.session_state.tareas = datos_usr["tareas"]
                                st.session_state.historial_chat = datos_usr["historial_chat"]
                            
                            st.success("¡Acceso concedido! Cargando centro de control...")
                            st.rerun()
                        else:
                            st.error("⚠️ Acceso denegado: Tu usuario no ha sido autorizado por el administrador todavía.")
                    else:
                        st.error("❌ Contraseña incorrecta. Inténtalo de nuevo.")
                else:
                    st.error("❌ El correo ingresado no está registrado en el ecosistema.")
        
        with st.expander("ℹ️ Información de cuentas de prueba"):
            st.markdown("""
            - **Administrador general:**
              - *Correo:* `admin@empresa.com`
              - *Contraseña:* `admin123`
            - **Usuario demostración (Ferretería con datos cargados):**
              - *Correo:* `demo@ferreteria.com`
              - *Contraseña:* `demo123`
            """)
    st.stop()

# ==========================================
# MENÚ LATERAL - SÓLO PARA LOGUEADOS
# ==========================================
if "api_key" not in st.session_state:
    try:
        st.session_state.api_key = st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        st.session_state.api_key = ""

with st.sidebar:
    st.markdown(f"👤 **Sesión activa:** `{st.session_state.usuario_actual}`")
    st.markdown(f"🏷️ **Rol:** `{st.session_state.rol_actual.capitalize()}`")
    
    st.markdown("---")
    st.header("📌 Navegación")
    
    opciones_menu = []
    if st.session_state.rol_actual == "admin":
        opciones_menu.append("👥 Control del administrador")
    
    opciones_menu.extend([
        "Dashboard general", 
        "Carga y plantillas CSV", 
        "Ingresar venta manual",
        "Asignación de tareas", 
        "Chatbot con agentes", 
        "Datos del pizarrón"
    ])
    
    opcion_menu = st.radio("Secciones de trabajo:", opciones_menu)
    
    if st.session_state.rol_actual != "admin":
        st.markdown("---")
        st.subheader("Configuración de perfil")
        
        nombre_prev = st.session_state.config_empresa["nombre"]
        tipo_prev = st.session_state.config_empresa["tipo"]
        dir_prev = st.session_state.config_empresa["direccion"]
        nit_prev = st.session_state.config_empresa["nit"]
        metas_prev = st.session_state.config_empresa["metas"]
        moneda_prev = st.session_state.config_empresa.get("moneda", "$")

        st.session_state.config_empresa["nombre"] = st.text_input("Empresa S.A.:", nombre_prev)
        st.session_state.config_empresa["tipo"] = st.text_input("Tipo de comercio:", tipo_prev)
        st.session_state.config_empresa["direccion"] = st.text_input("Domicilio fiscal:", dir_prev)
        st.session_state.config_empresa["nit"] = st.text_input("NIT de la empresa:", nit_prev)
        st.session_state.config_empresa["metas"] = st.text_area("Objetivos de operaciones:", metas_prev)
        
        lista_opciones_divisa = ["$", "Q", "€", "MXN", "COP", "CLP", "PEN", "Bs.", "HNL", "NIO", "CRC", "Personalizado"]
        try:
            def_idx = lista_opciones_divisa.index(moneda_prev)
        except ValueError:
            def_idx = 11
            
        moneda_seleccionada = st.selectbox("Moneda / divisa:", options=lista_opciones_divisa, index=def_idx)
        if moneda_seleccionada == "Personalizado":
            st.session_state.config_empresa["moneda"] = st.text_input("Símbolo de tu moneda:", value=moneda_prev if moneda_prev != "Personalizado" else "$")
        else:
            st.session_state.config_empresa["moneda"] = moneda_seleccionada

        if (nombre_prev != st.session_state.config_empresa["nombre"] or 
            tipo_prev != st.session_state.config_empresa["tipo"] or
            dir_prev != st.session_state.config_empresa["direccion"] or
            nit_prev != st.session_state.config_empresa["nit"] or
            metas_prev != st.session_state.config_empresa["metas"] or
            moneda_prev != st.session_state.config_empresa["moneda"]):
            guardar_datos_usuario_actual()

    st.markdown("---")
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.usuario_actual = ""
        st.session_state.rol_actual = ""
        st.rerun()

if st.session_state.rol_actual == "admin" and opcion_menu != "👥 Control del administrador":
    if "config_empresa" not in st.session_state:
        st.session_state.config_empresa = {
            "nombre": "Administración del sistema",
            "tipo": "Soporte",
            "direccion": "N/A",
            "nit": "N/A",
            "metas": "Supervisar la plataforma.",
            "moneda": "$"
        }
        st.session_state.datos_empresa = {
            "inventario": pd.read_csv(io.StringIO(PLANTILLAS_CSV["inventario"])),
            "caja": pd.read_csv(io.StringIO(PLANTILLAS_CSV["caja"])),
            "mercadeo": pd.read_csv(io.StringIO(PLANTILLAS_CSV["mercadeo"])),
            "impuestos": pd.read_csv(io.StringIO(PLANTILLAS_CSV["impuestos"]))
        }
        st.session_state.tareas = []
        st.session_state.historial_chat = []

# ==========================================
# VISTA GENERAL: CONTROL DEL ADMINISTRADOR
# ==========================================
if st.session_state.rol_actual == "admin" and opcion_menu == "👥 Control del administrador":
    st.header("👥 Consola de control del administrador")
    st.write("Registra, autoriza y supervisa las cuentas de acceso del ecosistema de agentes inteligentes de tu plataforma.")

    col_adm1, col_adm2 = st.columns([1, 1.5])
    
    with col_adm1:
        st.markdown("### ➕ Registrar nuevo usuario")
        with st.form("form_crear_usuario", clear_on_submit=True):
            nuevo_correo = st.text_input("Asignar correo electrónico:", placeholder="correo@empresa.com").strip().lower()
            nuevo_password = st.text_input("Asignar contraseña temporal:", placeholder="Clave de acceso")
            autorizacion_inicial = st.checkbox("Autorizar acceso inmediatamente", value=True)
            btn_crear = st.form_submit_button("Crear y registrar")
            
            if btn_crear:
                if nuevo_correo and nuevo_password:
                    if nuevo_correo not in db_actual["usuarios"]:
                        db_actual["usuarios"][nuevo_correo] = {
                            "password": nuevo_password,
                            "autorizado": autorizacion_inicial,
                            "rol": "usuario",
                            "config_empresa": {
                                "nombre": "Nueva empresa limpia",
                                "tipo": "Sin definir",
                                "direccion": "Sin definir",
                                "nit": "Sin definir",
                                "metas": "Configurar las metas estratégicas de la empresa aquí.",
                                "moneda": "$"
                            },
                            "datos_empresa": {
                                "inventario": pd.read_csv(io.StringIO(BLANCO_INVENTARIO)).to_dict(orient="records"),
                                "caja": pd.read_csv(io.StringIO(BLANCO_CAJA)).to_dict(orient="records"),
                                "mercadeo": pd.read_csv(io.StringIO(BLANCO_MERCADEO)).to_dict(orient="records"),
                                "impuestos": pd.read_csv(io.StringIO(BLANCO_IMPUESTOS)).to_dict(orient="records")
                            },
                            "tareas": [],
                            "historial_chat": [
                                {"rol": "Director General", "mensaje": "Saludos. He inicializado tu nuevo entorno empresarial de forma limpia. Tu aplicación está totalmente 'en blanco' y lista para operar. Dirígete a la sección 'Carga y plantillas CSV' para descargar las plantillas estándar, adaptarlas con tus datos de negocio y subirlas para que comencemos a trabajar coordinadamente."}
                            ]
                        }
                        guardar_db(db_actual)
                        st.success(f"✅ ¡Usuario `{nuevo_correo}` registrado con éxito! Su aplicación ha sido inicializada limpia ('en blanco').")
                        st.rerun()
                    else:
                        st.error("❌ El correo ingresado ya está registrado en el sistema.")
                else:
                    st.warning("Completa todos los campos obligatorios.")

    with col_adm2:
        st.markdown("### 📋 Listado y autorización de usuarios")
        st.write("Modifica el estado de autorización para suspender o permitir el inicio de sesión.")
        
        usuarios_listados = list(db_actual["usuarios"].keys())
        
        for usr_mail in usuarios_listados:
            if usr_mail == "admin@empresa.com":
                continue
                
            datos_usr = db_actual["usuarios"][usr_mail]
            rol_usr = datos_usr.get("rol", "usuario")
            estado_aut = datos_usr.get("autorizado", False)
            
            with st.container():
                st.markdown(f"**Usuario:** `{usr_mail}` | **Rol:** `{rol_usr}`")
                col_btn_aut, col_btn_del = st.columns([2, 1])
                
                with col_btn_aut:
                    nuevo_estado = st.toggle("Autorizado para entrar", value=estado_aut, key=f"tog_{usr_mail}")
                    if nuevo_estado != estado_aut:
                        db_actual["usuarios"][usr_mail]["autorizado"] = nuevo_estado
                        guardar_db(db_actual)
                        st.success(f"Estado de `{usr_mail}` actualizado.")
                        st.rerun()
                        
                with col_btn_del:
                    if st.button("🗑️ Eliminar", key=f"del_{usr_mail}", type="secondary", use_container_width=True):
                        del db_actual["usuarios"][usr_mail]
                        guardar_db(db_actual)
                        st.warning(f"Usuario `{usr_mail}` eliminado del sistema.")
                        st.rerun()
            st.markdown("---")

# ==========================================
# CONECTOR DE LLM (OPENROUTER)
# ==========================================
def consultar_openrouter(prompt_sistema, prompt_usuario):
    if not st.session_state.api_key:
        return "⚠️ Error: No se ha configurado la API Key de OpenRouter. Ingresa tu clave en el menú lateral para activar los agentes."
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.session_state.api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Sistema de gestión multi-agente corporativo"
    }
    
    data = {
        "model": "openai/gpt-oss-120b:free",
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=35)
        if response.status_code == 200:
            res_json = response.json()
            if 'choices' in res_json and len(res_json['choices']) > 0:
                return res_json['choices'][0]['message']['content']
            return "Error: Respuesta del modelo vacía o inesperada de OpenRouter."
        else:
            return f"Error en el servidor de OpenRouter (Código {response.status_code}): {response.text}"
    except Exception as e:
        return f"Error de conectividad de red con OpenRouter: {str(e)}"

# ==========================================
# CONTEXTOS Y PROMPTS PARA LOS AGENTES
# ==========================================
def construir_contexto_empresa():
    config = st.session_state.config_empresa
    inv = st.session_state.datos_empresa["inventario"].to_string()
    caja = st.session_state.datos_empresa["caja"].to_string()
    mkt = st.session_state.datos_empresa["mercadeo"].to_string()
    imp = st.session_state.datos_empresa["impuestos"].to_string()
    tareas = json.dumps(st.session_state.tareas, indent=2)
    moneda = config.get("moneda", "$")
    
    contexto = f"""
    --- PERFIL INSTITUCIONAL DE LA EMPRESA ---
    Nombre Comercial: {config['nombre']}
    Tipo de Negocio: {config['tipo']}
    Ubicación Central: {config['direccion']}
    Identificación Fiscal (NIT): {config['nit']}
    Metas Corporativas: {config['metas']}
    Moneda Oficial Definida por el Usuario: {moneda}

    --- BASE DE DATOS COMPARTIDA (PIZARRÓN DE CONTROL EN TIEMPO REAL) ---
    [DEPARTAMENTO DE INVENTARIO] (Los valores monetarios como costo y precio están en la divisa: {moneda})
    {inv}
    
    [DEPARTAMENTO FINANCIERO - FLUJO DE CAJA] (Los ingresos, egresos y saldos acumulados corresponden a la divisa: {moneda})
    {caja}
    
    [DEPARTAMENTO DE MERCADEO Y CAMPAÑAS] (Los presupuestos y gastos están medidos en la divisa: {moneda})
    {mkt}

    [DEPARTAMENTO DE IMPUESTOS Y FISCAL] (Las bases imponibles y montos determinados están en la divisa: {moneda})
    {imp}

    [REGISTRO DE TAREAS DIARIAS EN CURSO]
    {tareas}
    
    NOTA MUY IMPORTANTE DE CONTROL (APLICACIÓN EN BLANCO):
    Si las tablas de inventario, caja, mercadeo e impuestos están vacías (sólo tienen las cabeceras), significa que el usuario es nuevo y su aplicación está en blanco. Dile amablemente que para dar un diagnóstico preciso debe subir sus archivos CSV utilizando el menú de descarga/carga de plantillas. Ofrécete a guiarlo en el proceso y haz recomendaciones teóricas basadas en su Tipo de Negocio e ID de metas.
    """
    return contexto

def obtener_prompt_agente(rol):
    contexto = construir_contexto_empresa()
    moneda = st.session_state.config_empresa.get("moneda", "$")
    
    prompts = {
        "Director General": f"""Eres el Agente Director General (CEO) de la empresa. Tu deber primordial es liderar y coordinar a tus agentes especialistas (Financiero, Inventario, Impuestos y Mercadeo). Tienes una visión global del negocio. Tu tono es profesional, analítico y altamente estratégico. Al responder, evalúa los datos históricos de todas las áreas, señala ineficiencias y explica cómo tus subordinados se van a coordinar para resolverlo de inmediato.
        IMPORTANTE: Toda cifra de dinero que menciones o presupuestes DEBE estar obligatoriamente expresada usando la moneda oficial seleccionada por el usuario: {moneda}.
        {contexto}""",
        
        "Financiero": f"""Eres el Agente Financiero de la empresa. Te encargas de custodiar el dinero de la caja, evaluar márgenes de utilidad de los productos vendidos y vigilar el presupuesto disponible. Debes alertar al CEO si el flujo de caja operativo es deficiente para cubrir las obligaciones de deudas, impuestos o inversiones publicitarias de Mercadeo. Trabaja en sintonía con Inventario para evaluar compras lógicas y con Impuestos para asegurar provisiones fiscales.
        IMPORTANTE: Toda cifra de dinero que menciones o presupuestes DEBE estar obligatoriamente expresada usando la moneda oficial seleccionada por el usuario: {moneda}.
        {contexto}""",
        
        "Inventario": f"""Eres el Agente de Inventario. Gestionas el stock de productos, vigilas las mermas, controlas las rotaciones (Alta, Media, Baja) y configuras alertas de stock crítico frente a valores mínimos de seguridad. Trabajas en conjunto con el Financiero para autorizar nuevas compras basadas en liquidez y con el Agente de Mercadeo para armar ofertas sobre productos de baja rotación.
        IMPORTANTE: Toda cifra de dinero que menciones o presupuestes DEBE estar obligatoriamente expresada usando la moneda oficial seleccionada por el usuario: {moneda}.
        {contexto}""",
        
        "Impuestos": f"""Eres el Agente de Impuestos y Control Fiscal. Eres responsable de que la empresa se encuentre al día con el fisco, previendo pagos de IVA, ISR y retenciones de manera oportuna. Debes alertar al Financiero sobre los montos que deben estar resguardados en caja para el pago de tributos pendientes para evitar multas operativas.
        IMPORTANTE: Toda cifra de dinero que menciones o presupuestes DEBE estar obligatoriamente expresada usando la moneda oficial seleccionada por el usuario: {moneda}.
        {contexto}""",
        
        "Mercadeo": f"""Eres el Agente de Mercadeo. Tu foco es maximizar la visibilidad del negocio, atraer clientes calificados, y optimizar la tasa de conversión de las campañas de publicidad. Debes utilizar los datos del Agente de Inventario para saber qué productos necesitan pauta de urgencia (baja rotación) y reportar al Financiero el Retorno de Inversión publicitaria (ROI) para solicitar presupuesto adicional.
        IMPORTANTE: Toda cifra de dinero que menciones o presupuestes DEBE estar obligatoriamente expresada usando la moneda oficial seleccionada por el usuario: {moneda}.
        {contexto}"""
    }
    return prompts.get(rol, contexto)

def extraer_json_de_respuesta(texto_crudo):
    try:
        if "```json" in texto_crudo:
            bloque = texto_crudo.split("```json")[1].split("```")[0].strip()
            return json.loads(bloque)
        elif "```" in texto_crudo:
            bloque = texto_crudo.split("```")[1].split("```")[0].strip()
            return json.loads(bloque)
        return json.loads(texto_crudo.strip())
    except Exception as e:
        raise ValueError(f"Fallo de codificación JSON: {str(e)}")

# ==========================================
# SECCIÓN: DASHBOARD GENERAL
# ==========================================
if opcion_menu == "Dashboard general":
    st.header("📈 Informe del agente director general")
    st.write("Análisis general de la empresa recopilado de forma cruzada por los agentes a cargo de los datos.")
    
    moneda = st.session_state.config_empresa.get("moneda", "$")
    
    try:
        df_inv = st.session_state.datos_empresa["inventario"]
        df_caj = st.session_state.datos_empresa["caja"]
        df_mkt = st.session_state.datos_empresa["mercadeo"]
        df_imp = st.session_state.datos_empresa["impuestos"]
        
        val_inv = (df_inv["Cantidad"] * df_inv["Costo_Unitario"]).sum() if not df_inv.empty else 0.0
        caja_act = df_caj["Saldo_Acumulado"].iloc[-1] if not df_caj.empty else 0.0
        leads_tot = df_mkt["Leads_Generados"].sum() if not df_mkt.empty else 0
        imp_pend = df_imp[df_imp["Estado_Pago"] == "Pendiente"]["Monto_Determinado"].sum() if not df_imp.empty else 0.0
    except Exception:
        val_inv, caja_act, leads_tot, imp_pend = 0.0, 0.0, 0, 0.0

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(f"""<div class='metric-container'>
            <small style='color: #64748b;'>📦 Valor de inventario</small><br>
            <b style='font-size: 22px; color: #0f172a;'>{moneda} {val_inv:,.2f}</b>
        </div>""", unsafe_allow_html=True)
    with col_m2:
        st.markdown(f"""<div class='metric-container'>
            <small style='color: #64748b;'>💰 Saldo actual en caja</small><br>
            <b style='font-size: 22px; color: #16a34a;'>{moneda} {caja_act:,.2f}</b>
        </div>""", unsafe_allow_html=True)
    with col_m3:
        st.markdown(f"""<div class='metric-container'>
            <small style='color: #64748b;'>📣 Leads generados (Mkt)</small><br>
            <b style='font-size: 22px; color: #2563eb;'>{leads_tot:,} leads</b>
        </div>""", unsafe_allow_html=True)
    with col_m4:
        st.markdown(f"""<div class='metric-container'>
            <small style='color: #64748b;'>⚖️ Impuestos por pagar</small><br>
            <b style='font-size: 22px; color: #dc2626;'>{moneda} {imp_pend:,.2f}</b>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    es_vacia = (df_inv.empty and df_caj.empty and df_mkt.empty and df_imp.empty)
    if es_vacia:
        st.warning("ℹ️ **Tu aplicación se encuentra actualmente 'en blanco'**. Sube archivos de ejemplo de tu negocio en la pestaña de carga de CSV para que los agentes cuenten con información real sobre la cual operar.")

    if st.button("🔄 Generar informe de auditoría operativa con el director general"):
        with st.spinner("El CEO está llamando a los jefes de departamento y leyendo los libros de control corporativo..."):
            prompt_sys = obtener_prompt_agente("Director General")
            prompt_user = f"Analiza detalladamente los números que tenemos en inventario, balances de caja, rendimiento de publicidad y obligaciones tributarias. Reporta de forma ejecutiva un diagnóstico crítico de la situación. Recuerda usar siempre la moneda '{moneda}' en tu respuesta."
            informe = consultar_openrouter(prompt_sys, prompt_user)
            st.session_state.ultimo_informe = informe
            st.rerun()
            
    if "ultimo_informe" in st.session_state:
        st.markdown("### 📋 Evaluación operativa de la dirección general:")
        st.markdown(st.session_state.ultimo_informe)
    else:
        st.info("Para recibir un diagnóstico de tus operaciones y cómo interactúan las metas con tus datos reales, haz clic en el botón superior.")

# ==========================================
# SECCIÓN: CARGA Y PLANTILLAS CSV
# ==========================================
elif opcion_menu == "Carga y plantillas CSV":
    st.header("📥 Descarga de plantillas y carga de archivos")
    st.write("Para que los agentes inteligentes tomen decisiones, puedes descargar nuestras plantillas estándar, editarlas con tus datos corporativos reales de tu empresa y subirlas nuevamente.")
    
    st.markdown("---")
    st.subheader("1. Descarga de plantillas oficiales")
    
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    with col_d1:
        st.write("📦 **Módulo de inventario**")
        st.download_button(
            label="Descargar CSV de inventario",
            data=PLANTILLAS_CSV["inventario"],
            file_name="plantilla_inventario.csv",
            mime="text/csv"
        )
    with col_d2:
        st.write("💰 **Módulo de caja/finanzas**")
        st.download_button(
            label="Descargar CSV de caja",
            data=PLANTILLAS_CSV["caja"],
            file_name="plantilla_caja.csv",
            mime="text/csv"
        )
    with col_d3:
        st.write("📣 **Módulo de mercadeo**")
        st.download_button(
            label="Descargar CSV de mercadeo",
            data=PLANTILLAS_CSV["mercadeo"],
            file_name="plantilla_mercadeo.csv",
            mime="text/csv"
        )
    with col_d4:
        st.write("⚖️ **Módulo de impuestos**")
        st.download_button(
            label="Descargar CSV de impuestos",
            data=PLANTILLAS_CSV["impuestos"],
            file_name="plantilla_impuestos.csv",
            mime="text/csv"
        )
        
    st.markdown("---")
    st.subheader("2. Cargar archivos de datos reales")
    
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        f_inv = st.file_uploader("Subir CSV de inventario real", type=["csv"])
        if f_inv:
            try:
                st.session_state.datos_empresa["inventario"] = pd.read_csv(f_inv)
                st.success("✅ Archivo de inventario actualizado con éxito.")
                guardar_datos_usuario_actual()
            except Exception as e:
                st.error(f"Error de formato al leer el CSV: {str(e)}")
                
        f_caj = st.file_uploader("Subir CSV de caja real", type=["csv"])
        if f_caj:
            try:
                st.session_state.datos_empresa["caja"] = pd.read_csv(f_caj)
                st.success("✅ Archivo de caja y movimientos actualizado con éxito.")
                guardar_datos_usuario_actual()
            except Exception as e:
                st.error(f"Error de formato al leer el CSV: {str(e)}")

    with col_u2:
        f_mkt = st.file_uploader("Subir CSV de mercadeo real", type=["csv"])
        if f_mkt:
            try:
                st.session_state.datos_empresa["mercadeo"] = pd.read_csv(f_mkt)
                st.success("✅ Archivo de campañas de mercadeo actualizado con éxito.")
                guardar_datos_usuario_actual()
            except Exception as e:
                st.error(f"Error de formato al leer el CSV: {str(e)}")
                
        f_imp = st.file_uploader("Subir CSV de impuestos real", type=["csv"])
        if f_imp:
            try:
                st.session_state.datos_empresa["impuestos"] = pd.read_csv(f_imp)
                st.success("✅ Archivo de obligaciones de impuestos actualizado con éxito.")
                guardar_datos_usuario_actual()
            except Exception as e:
                st.error(f"Error de formato al leer el CSV: {str(e)}")

# ==========================================
# SECCIÓN: INGRESAR VENTA MANUAL
# ==========================================
elif opcion_menu == "Ingresar venta manual":
    st.header("🛒 Registro manual de ventas")
    st.write("Registra salidas de inventario y entradas financieras de forma directa. El sistema actualizará automáticamente el stock de tu catálogo, ingresará el registro monetario en el flujo de caja, y guardará los cambios de forma persistente.")
    
    df_inv = st.session_state.datos_empresa["inventario"]
    df_caj = st.session_state.datos_empresa["caja"]
    
    if df_inv.empty:
        st.warning("⚠️ El catálogo de inventario está actualmente vacío. Por favor, carga una base de datos en la sección 'Carga y plantillas CSV' antes de registrar ventas.")
    else:
        with st.form("form_registro_venta_manual"):
            col_v1, col_v2 = st.columns(2)
            
            with col_v1:
                st.markdown("##### 📦 Detalles de artículo")
                opciones_productos = [
                    f"{row['ID_Producto']} - {row['Producto']} (Disponibles: {row['Cantidad']})" 
                    for idx, row in df_inv.iterrows()
                ]
                seleccion_prod = st.selectbox("Selecciona el producto a vender:", opciones_productos)
                
                id_prod_sel = seleccion_prod.split(" - ")[0]
                datos_prod_sel = df_inv[df_inv["ID_Producto"] == id_prod_sel].iloc[0]
                
                stock_disponible = int(datos_prod_sel["Cantidad"])
                precio_sugerido = float(datos_prod_sel["Precio_Venta"])
                
                cantidad_vender = st.number_input(
                    "Cantidad a vender:", 
                    min_value=1, 
                    max_value=max(1, stock_disponible), 
                    value=1, 
                    step=1,
                    help="El límite superior está determinado por el stock disponible en inventario."
                )
                
            with col_v2:
                st.markdown("##### 💳 Parámetros de la transacción")
                metodo_pago = st.selectbox("Método de recaudación:", ["Efectivo", "Tarjeta", "Transferencia", "Cheque", "Crédito"])
                
                moneda = st.session_state.config_empresa.get("moneda", "$")
                precio_venta_final = st.number_input(
                    f"Precio de venta unitario ({moneda}):", 
                    min_value=0.0, 
                    value=precio_sugerido, 
                    step=0.1
                )
                
                concepto_defecto = f"Venta manual de {cantidad_vender}x {datos_prod_sel['Producto']}"
                concepto_final = st.text_input("Concepto contable:", value=concepto_defecto)
                
            monto_total_venta = cantidad_vender * precio_venta_final
            st.markdown(f"### **Total neto a ingresar: {moneda} {monto_total_venta:,.2f}**")
            
            btn_confirmar_venta = st.form_submit_button("Confirmar y registrar venta")
            
            if btn_confirmar_venta:
                if stock_disponible <= 0:
                    st.error("❌ Transacción rechazada: El artículo seleccionado no tiene unidades en stock.")
                elif cantidad_vender > stock_disponible:
                    st.error(f"❌ Transacción rechazada: Intentas vender {cantidad_vender} unidades, pero solo hay {stock_disponible} disponibles.")
                else:
                    st.session_state.datos_empresa["inventario"].loc[
                        st.session_state.datos_empresa["inventario"]["ID_Producto"] == id_prod_sel,
                        "Cantidad"
                    ] -= cantidad_vender
                    
                    caja_saldo_anterior = df_caj["Saldo_Acumulado"].iloc[-1] if not df_caj.empty else 0.0
                    nuevo_saldo_acumulado = caja_saldo_anterior + monto_total_venta
                    
                    nueva_transaccion_caja = pd.DataFrame([{
                        "Fecha": str(datetime.date.today()),
                        "Concepto": concepto_final,
                        "Categoria": "Ventas",
                        "Ingreso": monto_total_venta,
                        "Egreso": 0.0,
                        "Saldo_Acumulado": nuevo_saldo_acumulado,
                        "Metodo_Pago": metodo_pago
                    }])
                    
                    st.session_state.datos_empresa["caja"] = pd.concat([
                        st.session_state.datos_empresa["caja"].astype(nueva_transaccion_caja.dtypes),
                        nueva_transaccion_caja
                    ], ignore_index=True)
                    
                    guardar_datos_usuario_actual()
                    
                    st.success(f"🎉 ¡Venta procesada con éxito! Se descontaron {cantidad_vender} unidades de '{datos_prod_sel['Producto']}' y se registró un ingreso de {moneda} {monto_total_venta:,.2f} en el flujo de caja.")
                    st.rerun()

# ==========================================
# SECCIÓN: ASIGNACIÓN DE TAREAS
# ==========================================
elif opcion_menu == "Asignación de tareas":
    st.header("📋 Tablero de distribución y asignación de tareas")
    st.write("Administra el cronograma operativo de tus agentes utilizando cualquiera de los tres modos de asignación.")
    
    st.subheader("🤖 Modo 3: Piloto automático de dirección")
    st.write("El Director General revisa el rendimiento global de la empresa y diseña de forma autónoma misiones de urgencia para resolver cuellos de botella detectados.")
    
    moneda = st.session_state.config_empresa.get("moneda", "$")

    if st.button("🚀 Iniciar generación en piloto automático"):
        with st.spinner("El CEO está examinando las tablas compartidas de impuestos pendientes, rotaciones y dinero disponible..."):
            prompt_sys = obtener_prompt_agente("Director General")
            prompt_user = f"""Evalúa el estado corporativo y genera un plan de 4 tareas de alta prioridad para hoy (una para cada especialista: Financiero, Inventario, Impuestos, Mercadeo).
            Debes retornar ÚNICAMENTE un arreglo con formato JSON estricto, sin explicaciones previas ni finales. 
            IMPORTANTE: Si mencionas montos o presupuestos en las tareas, utiliza obligatoriamente la divisa oficial definida: {moneda}.
            [
              {{"agente": "Financiero", "descripcion": "Tarea específica basada en saldo actual o egresos"}},
              {{"agente": "Inventario", "descripcion": "Tarea para mitigar productos de rotacion baja o stock critico"}},
              {{"agente": "Impuestos", "descripcion": "Misión para calcular o liquidar obligaciones próximas al vencimiento"}},
              {{"agente": "Mercadeo", "descripcion": "Estrategia de campaña comercial sobre excedentes de herramientas o stock"}}
            ]"""
            
            respuesta = consultar_openrouter(prompt_sys, prompt_user)
            try:
                tareas_auto = extraer_json_de_respuesta(respuesta)
                for nt in tareas_auto:
                    nuevo_id = max([t["id"] for t in st.session_state.tareas]) + 1 if st.session_state.tareas else 1
                    st.session_state.tareas.append({
                        "id": nuevo_id,
                        "agente": nt["agente"],
                        "descripcion": nt["descripcion"],
                        "estado": "Pendiente",
                        "fecha": str(datetime.date.today())
                    })
                st.success("🎯 Las tareas estratégicas del día han sido redactadas y enviadas al pizarrón general por el CEO.")
                guardar_datos_usuario_actual()
                st.rerun()
            except Exception as e:
                st.error("No se pudo estructurar el JSON operativo de forma directa. Inténtalo de nuevo.")
                with st.expander("Ver reporte crudo del LLM"):
                    st.text(respuesta)

    st.markdown("---")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("#### 🎯 Modo 1: Asignación directa")
        with st.form("form_creacion_directa", clear_on_submit=True):
            agente_target = st.selectbox("Asignar directamente a:", ["Financiero", "Inventario", "Impuestos", "Mercadeo"])
            desc_directa = st.text_input("Ingresa los objetivos de la tarea:")
            submit_dir = st.form_submit_button("Crear tarea")
            
            if submit_dir:
                if desc_directa:
                    nuevo_id = max([t["id"] for t in st.session_state.tareas]) + 1 if st.session_state.tareas else 1
                    st.session_state.tareas.append({
                        "id": nuevo_id,
                        "agente": agente_target,
                        "descripcion": desc_directa,
                        "estado": "Pendiente",
                        "fecha": str(datetime.date.today())
                    })
                    st.success(f"Asignación directa enviada a {agente_target}.")
                    guardar_datos_usuario_actual()
                    st.rerun()
                else:
                    st.warning("Escribe una descripción de objetivos.")

    with col_m2:
        st.markdown("#### 🗣️ Modo 2: Dictado centralizado a gerencia")
        with st.form("form_creacion_centralizada", clear_on_submit=True):
            orden_general = st.text_area("Orden global o problema genérico:", placeholder="Ej: Se aproxima la compra de stock de mercadería y necesitamos prever los saldos.")
            submit_cen = st.form_submit_button("Asignar por canal CEO")
            
            if submit_cen:
                if orden_general:
                    with st.spinner("El CEO está reuniendo a los departamentos para koordinar la estrategia..."):
                        prompt_sys = obtener_prompt_agente("Director General")
                        prompt_user = f"""El usuario ha dictado la siguiente orden general: "{orden_general}".
                        Desglosa esta orden en tareas específicas para cada uno de los especialistas involucrados.
                        Retorna la respuesta estrictamente estructurada en formato JSON, sin textos adicionales:
                        [
                          {{"agente": "Nombre del agente", "descripcion": "Detalle de la tarea coordinada"}}
                        ]"""
                        
                        respuesta_cen = consultar_openrouter(prompt_sys, prompt_user)
                        try:
                            tareas_des = extraer_json_de_respuesta(respuesta_cen)
                            for nt in tareas_des:
                                nuevo_id = max([t["id"] for t in st.session_state.tareas]) + 1 if st.session_state.tareas else 1
                                st.session_state.tareas.append({
                                    "id": nuevo_id,
                                    "agente": nt["agente"],
                                    "descripcion": nt["descripcion"],
                                    "estado": "Pendiente",
                                    "fecha": str(datetime.date.today())
                                })
                            st.success("La Gerencia General ha finalizado la coordinación e inyectado las tareas resultantes.")
                            guardar_datos_usuario_actual()
                            st.rerun()
                        except Exception:
                            st.error("No se pudo interpretar el formato JSON del modelo. Reintenta la asignación.")
                else:
                    st.warning("Digita una directiva global para la empresa.")

    st.markdown("---")
    
    st.subheader("📋 Pizarrón de operaciones diario")
    if st.session_state.tareas:
        df_tareas = pd.DataFrame(st.session_state.tareas)
        st.dataframe(df_tareas, use_container_width=True, hide_index=True)
        
        col_tid, col_testado, col_tbtn = st.columns([1, 2, 2])
        with col_tid:
            id_modificar = st.number_input("ID de la tarea a actualizar:", min_value=1, step=1)
        with col_testado:
            estado_nuevo = st.selectbox("Cambiar estado:", ["Pendiente", "En Proceso", "Completada"])
        with col_tbtn:
            st.write("")
            st.write("")
            if st.button("Guardar cambios de tarea"):
                encontrada = False
                for t in st.session_state.tareas:
                    if t["id"] == id_modificar:
                        t["estado"] = estado_nuevo
                        encontrada = True
                        break
                if encontrada:
                    st.success(f"La tarea #{id_modificar} ha cambiado de estado a '{estado_nuevo}'.")
                    guardar_datos_usuario_actual()
                    st.rerun()
                else:
                    st.error(f"La tarea con el identificador #{id_modificar} no existe.")
    else:
        st.info("No hay asignaciones cargadas para el día de hoy.")

# ==========================================
# SECCIÓN: CHATBOT CON AGENTES
# ==========================================
elif opcion_menu == "Chatbot con agentes":
    st.header("💬 Sala de reuniones ejecutiva (Chatbot)")
    st.write("Habla de manera interactiva con tus agentes especialistas. Cada agente conoce la base de datos compartida y cooperará para ayudarte a cumplir tus metas estratégicas.")
    
    interlocutor_activo = st.selectbox("Convocar a reunión a:", ["Director General", "Financiero", "Inventario", "Impuestos", "Mercadeo"])
    moneda = st.session_state.config_empresa.get("moneda", "$")

    for msj in st.session_state.historial_chat:
        clase_b = "user-bubble" if msj["rol"] == "Usuario" else "agent-bubble"
        st.markdown(f"<div class='chat-bubble {clase_b}'><b>{msj['rol']}:</b><br>{msj['mensaje']}</div>", unsafe_allow_html=True)
        
    with st.form("form_chat", clear_on_submit=True):
        input_usr = st.text_input("Introduce tus instrucciones, consultas o inquietudes sobre el estado empresarial:")
        btn_enviar = st.form_submit_button("Enviar mensaje a la sala")
        
    if btn_enviar and input_usr:
        st.session_state.historial_chat.append({"rol": "Usuario", "mensaje": input_usr})
        
        with st.spinner(f"El Agente {interlocutor_activo} está analizando las transacciones y preparando su respuesta..."):
            prompt_sys = obtener_prompt_agente(interlocutor_activo)
            dialogo_historico = "\n".join([f"{m['rol']}: {m['mensaje']}" for m in st.session_state.historial_chat[-6:]])
            prompt_completo = f"Historial de conversación reciente:\n{dialogo_historico}\n\nNueva intervención del usuario: {input_usr}\n\nRecuerda usar la divisa oficial definida en el perfil: {moneda}."
            
            respuesta_agente = consultar_openrouter(prompt_sys, prompt_completo)
            st.session_state.historial_chat.append({"rol": interlocutor_activo, "mensaje": respuesta_agente})
            guardar_datos_usuario_actual()
        st.rerun()

# ==========================================
# SECCIÓN: DATOS DEL PIZARRÓN
# ==========================================
elif opcion_menu == "Datos del pizarrón":
    st.header("💾 Registro de libros de datos")
    st.write("Esta sección muestra las bases de datos de solo lectura compartidas. Los agentes corporativos consultan estos registros al instante para emitir dictámenes coherentes.")
    
    pestana1, pestana2, pestana3, pestana4 = st.tabs(["📦 Inventario de productos", "💰 Caja y egresos", "📣 Campañas de mercadeo", "⚖️ Impuestos y provisiones"])
    
    with pestana1:
        st.dataframe(st.session_state.datos_empresa["inventario"], use_container_width=True, hide_index=True)
    with pestana2:
        st.dataframe(st.session_state.datos_empresa["caja"], use_container_width=True, hide_index=True)
    with pestana3:
        st.dataframe(st.session_state.datos_empresa["mercadeo"], use_container_width=True, hide_index=True)
    with pestana4:
        st.dataframe(st.session_state.datos_empresa["impuestos"], use_container_width=True, hide_index=True)
