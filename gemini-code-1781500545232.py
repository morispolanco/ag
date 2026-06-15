import streamlit as np
import streamlit as st
import pandas as pd
import requests
import json
import datetime

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Gestión Empresarial Multi-Agente",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado para mejorar la interfaz
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    .stAlert p { margin-bottom: 0; }
    .agent-card {
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
        background-color: #f9f9f9;
    }
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        max-width: 80%;
    }
    .user-bubble { background-color: #e3f2fd; margin-left: auto; }
    .agent-bubble { background-color: #f1f1f1; margin-right: auto; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INICIALIZACIÓN DEL ESTADO DE LA SESIÓN
# ==========================================
if "api_key" not in st.session_state:
    try:
        st.session_state.api_key = st.secrets["OPENROUTER_API_KEY"]
    except:
        st.session_state.api_key = ""

if "config_empresa" not in st.session_state:
    st.session_state.config_empresa = {
        "nombre": "Mi Empresa S.A.",
        "tipo": "Comercial / Retail",
        "direccion": "Ciudad de Guatemala",
        "nit": "1234567-8",
        "metas": "Incrementar ventas un 15% este mes y optimizar el inventario de baja rotación."
    }

if "datos_empresa" not in st.session_state:
    st.session_state.datos_empresa = {
        "inventario": pd.DataFrame(columns=["Producto", "Cantidad", "Costo", "Precio Venta", "Rotacion"]),
        "caja": pd.DataFrame(columns=["Fecha", "Concepto", "Ingreso", "Egreso", "Saldo"]),
        "mercadeo": pd.DataFrame(columns=["Campaña", "Canal", "Presupuesto", "Leads", "Conversion"])
    }

if "tareas" not in st.session_state:
    st.session_state.tareas = [
        {"id": 1, "agente": "Financiero", "descripcion": "Revisar el flujo de caja semanal", "estado": "Pendiente", "fecha": "2026-06-14"},
        {"id": 2, "agente": "Inventario", "descripcion": "Identificar productos con stock crítico", "estado": "Pendiente", "fecha": "2026-06-14"},
        {"id": 3, "agente": "Impuestos", "descripcion": "Calcular la provisión del IVA mensual", "estado": "Pendiente", "fecha": "2026-06-14"},
        {"id": 4, "agente": "Mercadeo", "descripcion": "Monitorear rendimiento de pauta en redes", "estado": "Pendiente", "fecha": "2026-06-14"}
    ]

if "historial_chat" not in st.session_state:
    st.session_state.historial_chat = [
        {"rol": "Director General", "mensaje": "Bienvenido al centro de mando. Estoy listo para coordinar al equipo según tus instrucciones."}
    ]

# Datos de plantilla por defecto si el usuario no sube archivos
def cargar_datos_plantilla():
    st.session_state.datos_empresa["inventario"] = pd.DataFrame([
        {"Producto": "Laptop Alpha", "Cantidad": 15, "Costo": 500, "Precio Venta": 800, "Rotacion": "Alta"},
        {"Producto": "Monitor 24", "Cantidad": 40, "Costo": 120, "Precio Venta": 200, "Rotacion": "Media"},
        {"Producto": "Teclado Mecánico", "Cantidad": 8, "Costo": 40, "Precio Venta": 75, "Rotacion": "Baja"}
    ])
    st.session_state.datos_empresa["caja"] = pd.DataFrame([
        {"Fecha": "2026-06-10", "Concepto": "Saldo inicial", "Ingreso": 5000, "Egreso": 0, "Saldo": 5000},
        {"Fecha": "2026-06-11", "Concepto": "Venta de 2 Laptops", "Ingreso": 1600, "Egreso": 0, "Saldo": 6600},
        {"Fecha": "2026-06-12", "Concepto": "Pago de internet y luz", "Ingreso": 0, "Egreso": 300, "Saldo": 6300}
    ])
    st.session_state.datos_empresa["mercadeo"] = pd.DataFrame([
        {"Campaña": "Lanzamiento Junio", "Canal": "Meta Ads", "Presupuesto": 250, "Leads": 120, "Conversion": "5%"},
        {"Campaña": "Descuentos Corporativos", "Canal": "LinkedIn", "Presupuesto": 150, "Leads": 30, "Conversion": "12%"}
    ])

if st.session_state.datos_empresa["inventario"].empty:
    cargar_datos_plantilla()

# ==========================================
# 3. CONECTOR DE LLM (OPENROUTER)
# ==========================================
def consultar_openrouter(prompt_sistema, prompt_usuario):
    if not st.session_state.api_key:
        return "Error: No se ha configurado la API Key de OpenRouter en los secretos de Streamlit."
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.session_state.api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "openai/gpt-oss-120b:free",
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Error en la API ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Error de conexión: {str(e)}"

# ==========================================
# 4. PROMPTS DEL SISTEMA MULTI-AGENTE
# ==========================================
def construir_contexto_empresa():
    config = st.session_state.config_empresa
    inv = st.session_state.datos_empresa["inventario"].to_string()
    caja = st.session_state.datos_empresa["caja"].to_string()
    mkt = st.session_state.datos_empresa["mercadeo"].to_string()
    tareas = json.dumps(st.session_state.tareas, indent=2)
    
    contexto = f"""
    DATOS GENERALES DE LA EMPRESA:
    Nombre: {config['nombre']}
    Tipo: {config['tipo']}
    Dirección: {config['direccion']}
    NIT: {config['nit']}
    Metas Actuales: {config['metas']}

    ESTADO DE LOS DEPARTAMENTOS (MEMORIA COMPARTIDA):
    --- INVENTARIO ---
    {inv}
    
    --- CAJA / FINANZAS ---
    {caja}
    
    --- MERCADEO ---
    {mkt}

    --- LISTA DE TAREAS Y ESTADOS ---
    {tareas}
    """
    return contexto

def obtener_prompt_agente(rol):
    contexto = construir_contexto_empresa()
    
    prompts = {
        "Director General": f"""Eres el Gerente General de la empresa. Tu rol es coordinar a los agentes especialistas (Financiero, Inventario, Impuestos, Mercadeo) para cumplir las metas del negocio. Tienes visión global. Cuando respondas, analiza el contexto general de la empresa, delega inteligentemente o presenta reportes ejecutivos consolidados al usuario.
        {contexto}""",
        
        "Financiero": f"""Eres el Agente Financiero. Te encargas de la rentabilidad, costos, análisis del flujo de caja y presupuestos. Debes alertar si hay desviaciones de dinero o si falta capital para las estrategias de mercadeo o inventario.
        {contexto}""",
        
        "Inventario": f"""Eres el Agente de Inventario. Tu foco es el control de stock, rotación de productos, evitar quiebres de stock y detectar mercancía obsoleta o de baja rotación. Coordina con el Financiero para compras y con Mercadeo para promociones.
        {contexto}""",
        
        "Impuestos": f"""Eres el Agente de Impuestos. Te encargas del cumplimiento fiscal, cálculo de provisiones (IVA, ISR), retenciones y fechas límite de declaración según las normativas del país. Mantén la empresa a salvo de multas.
        {contexto}""",
        
        "Mercadeo": f"""Eres el Agente de Mercadeo. Tu objetivo es la captación de clientes, optimización del embudo de ventas, análisis de conversión de campañas y diseño de estrategias de promoción, especialmente para los productos que el Agente de Inventario reporte con baja rotación.
        {contexto}"""
    }
    return prompts.get(rol, contexto)

# ==========================================
# 5. INTERFAZ DE USUARIO (DASHBOARD)
# ==========================================
st.title("🏢 Sistema de Gestión Empresarial Multi-Agente")
st.subheader(f"Centro de control operativo: {st.session_state.config_empresa['nombre']}")

# Sidebar - Navegación y Configuración
with st.sidebar:
    st.header("⚙️ Configuración y Datos")
    opcion_menu = st.radio("Ir a:", ["Dashboard General", "Asignación de Tareas", "Chatbot con Agentes", "Carga de Datos (CSV)", "Datos de la Empresa"])
    
    st.markdown("---")
    st.subheader("Datos de la Entidad")
    st.session_state.config_empresa["nombre"] = st.text_input("Nombre de la empresa", st.session_state.config_empresa["nombre"])
    st.session_state.config_empresa["tipo"] = st.text_input("Tipo de empresa", st.session_state.config_empresa["tipo"])
    st.session_state.config_empresa["direccion"] = st.text_input("Dirección fiscal", st.session_state.config_empresa["direccion"])
    st.session_state.config_empresa["nit"] = st.text_input("Número de NIT", st.session_state.config_empresa["nit"])
    st.session_state.config_empresa["metas"] = st.text_area("Metas estratégicas", st.session_state.config_empresa["metas"])

# ------------------------------------------
# VISTA 1: DASHBOARD GENERAL (REPORTE DEL CEO)
# ------------------------------------------
if opcion_menu == "Dashboard General":
    st.header("📊 Informe Ejecutivo del Director General")
    
    if st.button("🔄 Solicitar informe actualizado al Gerente General"):
        with st.spinner("El Director General está reuniendo los reportes de los departamentos..."):
            prompt_sys = obtener_prompt_agente("Director General")
            prompt_user = "Por favor, analiza la situación actual de todos los departamentos, evalúa si estamos alineados con las metas declaradas y genera un resumen ejecutivo estratégico destacando problemas urgentes y avances."
            informe = consultar_openrouter(prompt_sys, prompt_user)
            st.session_state.ultimo_informe = informe
            
    if "ultimo_informe" in st.session_state:
        st.markdown(st.session_state.ultimo_informe)
    else:
        st.info("Haz clic en el botón superior para que el Agente Director General evalúe la situación de la empresa en tiempo real.")

    st.markdown("---")
    st.subheader("Estado Actual del Equipo de Agentes")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='agent-card'><b>💰 Agente Financiero</b><br><small>Monitoreando Flujo de Caja e ISR</small></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='agent-card'><b>📦 Agente de Inventario</b><br><small>Monitoreando Stock y Rotación</small></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='agent-card'><b>⚖️ Agente de Impuestos</b><br><small>Monitoreando Obligaciones Fiscales</small></div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='agent-card'><b>📣 Agente de Mercadeo</b><br><small>Monitoreando Campañas y Conversión</small></div>", unsafe_allow_html=True)

# ------------------------------------------
# VISTA 2: ASIGNACIÓN DE TAREAS
# ------------------------------------------
elif opcion_menu == "Asignación de Tareas":
    st.header("📋 Gestión y Asignación de Tareas Diarias")
    
    # MODO 3: PILOTO AUTOMÁTICO
    st.subheader("🤖 Modo Piloto Automático")
    st.write("Permite que el Agente Director analice los datos actuales de la empresa y auto-genere las tareas prioritarias del día para cada especialista.")
    
    if st.button("🚀 Activar Piloto Automático"):
        with st.spinner("El Director General está analizando debilidades en los datos para asignar responsabilidades..."):
            prompt_sys = obtener_prompt_agente("Director General")
            prompt_user = """Analiza los datos de la empresa (inventario, caja, mercadeo) y genera un listado en formato JSON estrictamente estructurado de tareas urgentes para el día de hoy. 
            El formato debe ser exactamente un arreglo JSON como este:
            [
              {"agente": "Financiero", "descripcion": "Descripción corta de la tarea"},
              {"agente": "Inventario", "descripcion": "Descripción corta de la tarea"}
            ]
            Genera una tarea por cada uno de los 4 agentes especialistas. No devuelvas nada de texto adicional, solo el JSON."""
            
            respuesta = consultar_openrouter(prompt_sys, prompt_user)
            try:
                # Limpieza por si el modelo incluye marcas de bloque de código
                if "```json" in respuesta:
                    respuesta = respuesta.split("```json")[1].split("```")[0].strip()
                elif "```" in respuesta:
                    respuesta = respuesta.split("```")[1].split("```")[0].strip()
                
                nuevas_tareas = json.loads(respuesta)
                for nt in nuevas_tareas:
                    nuevo_id = max([t["id"] for t in st.session_state.tareas]) + 1 if st.session_state.tareas else 1
                    st.session_state.tareas.append({
                        "id": nuevo_id,
                        "agente": nt["agente"],
                        "descripcion": nt["descripcion"],
                        "estado": "Pendiente",
                        "fecha": str(datetime.date.today())
                    })
                st.success("¡Piloto automático ejecutado! Tareas estratégicas añadidas exitosamente.")
            except Exception as e:
                st.error("El modelo no devolvió el formato JSON limpio requerido. Inténtalo de nuevo.")
                with st.expander("Ver respuesta del modelo"):
                    st.write(respuesta)

    st.markdown("---")
    
    # MODO 1 Y 2: DIRECTO O POR DIRECTOR GENERAL
    st.subheader("➕ Asignación Manual / Centralizada")
    col_modo1, col_modo2 = st.columns(2)
    
    with col_modo1:
        st.markdown("**Modo 1: Asignación Directa**")
        with st.form("form_directo"):
            agente_dest = st.selectbox("Asignar directamente a:", ["Financiero", "Inventario", "Impuestos", "Mercadeo"])
            desc_tarea = st.text_input("Descripción de la tarea")
            if st.form_submit_submit_button("Asignar Tarea Directa"):
                if desc_tarea:
                    nuevo_id = max([t["id"] for t in st.session_state.tareas]) + 1 if st.session_state.tareas else 1
                    st.session_state.tareas.append({
                        "id": nuevo_id, "agente": agente_dest, "descripcion": desc_tarea, "estado": "Pendiente", "fecha": str(datetime.date.today())
                    })
                    st.success("Tarea asignada de forma directa.")
                else:
                    st.warning("Escribe una descripción.")

    with col_modo2:
        st.markdown("**Modo 2: Dictar a través del Director General**")
        with st.form("form_director"):
            instruccion_general = st.text_area("Dicta una orden general o problema", placeholder="Ej: Las ventas bajaron y tenemos poco saldo en caja, resuelvan esto.")
            if st.form_submit_button("Enviar orden al Director General"):
                if instruccion_general:
                    with st.spinner("El Director General procesa la orden y subdivide el trabajo..."):
                        prompt_sys = obtener_prompt_agente("Director General")
                        prompt_user = f"El usuario ha dado esta instrucción global: '{instruccion_general}'. Desglosa esta orden en tareas específicas para los agentes necesarios. Devuelve un formato JSON estructurado: [{{'agente': 'Nombre', 'descripcion': 'tarea'}}]."
                        respuesta = consultar_openrouter(prompt_sys, prompt_user)
                        try:
                            if "
http://googleusercontent.com/immersive_entry_chip/0
http://googleusercontent.com/immersive_entry_chip/1
3. **Configuración en la Nube:** Al crear la aplicación en el panel de control de Streamlit Cloud, dirígete a **Advanced Settings** -> **Secrets** y pega tu token de autenticación de OpenRouter respetando la clave utilizada en el script:
   ```toml
   OPENROUTER_API_KEY = "sk-or-v1-..."