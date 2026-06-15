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

# Estilos personalizados para mejorar la legibilidad y la presentación visual
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    .stAlert p { margin-bottom: 0; }
    .agent-card {
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
        background-color: #f9f9f9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .chat-bubble {
        padding: 12px 18px;
        border-radius: 12px;
        margin-bottom: 12px;
        max-width: 85%;
        line-height: 1.5;
    }
    .user-bubble { 
        background-color: #e3f2fd; 
        color: #0d47a1;
        margin-left: auto; 
        border-bottom-right-radius: 2px;
    }
    .agent-bubble { 
        background-color: #f5f5f5; 
        color: #212121;
        margin-right: auto; 
        border-bottom-left-radius: 2px;
        border-left: 4px solid #4caf50;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INICIALIZACIÓN DEL ESTADO DE LA SESIÓN
# ==========================================
if "api_key" not in st.session_state:
    try:
        st.session_state.api_key = st.secrets["OPENROUTER_API_KEY"]
    except Exception:
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
        {"rol": "Director General", "mensaje": "Bienvenido al centro de mando. Estoy listo para coordinar al equipo de especialistas según tus instrucciones globales o tus consultas directas."}
    ]

# Función para cargar datos de ejemplo si los dataframes están vacíos
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
        return "Error: No se ha configurado la API Key de OpenRouter en los secretos de Streamlit (OPENROUTER_API_KEY)."
    
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
        response = requests.post(url, headers=headers, json=data, timeout=35)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Error en la API de OpenRouter (Código {response.status_code}): {response.text}"
    except Exception as e:
        return f"Error de conexión con el proveedor LLM: {str(e)}"

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
    Tipo de Empresa: {config['tipo']}
    Dirección Fiscal: {config['direccion']}
    NIT: {config['nit']}
    Metas Estratégicas Declaradas: {config['metas']}

    ESTADO ACTUAL DE LOS DEPARTAMENTOS (MEMORIA COMPARTIDA):
    --- INVENTARIO ---
    {inv}
    
    --- CAJA / FINANZAS ---
    {caja}
    
    --- MERCADEO ---
    {mkt}

    --- LISTA DE TAREAS OPERATIVAS Y ESTADOS ---
    {tareas}
    """
    return contexto

def obtener_prompt_agente(rol):
    contexto = construir_contexto_empresa()
    
    prompts = {
        "Director General": f"""Eres el Gerente General de la empresa. Tu rol es coordinar a los agentes especialistas (Financiero, Inventario, Impuestos, Mercadeo) para cumplir las metas del negocio. Tienes visión global. Cuando respondas, analiza el contexto general de la empresa, delega inteligentemente o presenta reportes ejecutivos consolidados al usuario de forma clara y profesional.
        {contexto}""",
        
        "Financiero": f"""Eres el Agente Financiero. Te encargas de la rentabilidad, costos, análisis del flujo de caja y presupuestos de la compañía. Debes alertar si hay desviaciones de dinero o si falta capital para las estrategias de mercadeo o inventario. Coordínate activamente con el Gerente General e Impuestos.
        {contexto}""",
        
        "Inventario": f"""Eres el Agente de Inventario. Tu foco es el control de stock, rotación de productos, evitar quiebres de stock y detectar mercancía obsoleta o de baja rotación. Coordina con el Financiero para compras y con Mercadeo para liquidación de stock o promociones.
        {contexto}""",
        
        "Impuestos": f"""Eres el Agente de Impuestos. Te encargas del cumplimiento fiscal, cálculo de provisiones (IVA, ISR), retenciones y fechas límite de declaración según las normativas vigentes. Mantén la empresa a salvo de multas u auditorías desfavorables.
        {contexto}""",
        
        "Mercadeo": f"""Eres el Agente de Mercadeo. Tu objetivo es la captación de clientes, optimización de presupuestos publicitarios, análisis de conversión de campañas y diseño de estrategias de promoción, especialmente para los productos que el Agente de Inventario reporte con baja rotación.
        {contexto}"""
    }
    return prompts.get(rol, contexto)

# Función auxiliar robusta para extraer y decodificar JSON del LLM
def extraer_json_de_respuesta(texto_crudo):
    # Buscamos delimitar por los bloques de código típicos de Markdown
    if "```json" in texto_crudo:
        bloque = texto_crudo.split("```json")[1].split("```")[0].strip()
        return json.loads(bloque)
    elif "```" in texto_crudo:
        bloque = texto_crudo.split("```")[1].split("```")[0].strip()
        return json.loads(bloque)
    else:
        # Intentamos decodificar directamente en caso de que no tenga formateadores de markdown
        return json.loads(texto_crudo.strip())

# ==========================================
# 5. INTERFAZ DE USUARIO (DASHBOARD)
# ==========================================
st.title("🏢 Sistema de Gestión Empresarial Multi-Agente")
st.subheader(f"Centro de Operaciones Inteligente: {st.session_state.config_empresa['nombre']}")

# Sidebar - Navegación y Configuración del Perfil Empresarial
with st.sidebar:
    st.header("⚙️ Menú de Configuración")
    opcion_menu = st.radio("Secciones de la App:", [
        "Dashboard General", 
        "Asignación de Tareas", 
        "Chatbot con Agentes", 
        "Carga de Datos (CSV)", 
        "Datos de la Empresa"
    ])
    
    st.markdown("---")
    st.subheader("Datos de la Entidad")
    st.session_state.config_empresa["nombre"] = st.text_input("Nombre de la empresa", st.session_state.config_empresa["nombre"])
    st.session_state.config_empresa["tipo"] = st.text_input("Tipo de empresa", st.session_state.config_empresa["tipo"])
    st.session_state.config_empresa["direccion"] = st.text_input("Dirección fiscal", st.session_state.config_empresa["direccion"])
    st.session_state.config_empresa["nit"] = st.text_input("Número de NIT / Registro", st.session_state.config_empresa["nit"])
    st.session_state.config_empresa["metas"] = st.text_area("Metas estratégicas", st.session_state.config_empresa["metas"])

# ------------------------------------------
# VISTA 1: DASHBOARD GENERAL (INFORME CEO)
# ------------------------------------------
if opcion_menu == "Dashboard General":
    st.header("📊 Informe Ejecutivo del Director General")
    
    if st.button("🔄 Solicitar informe consolidado al Gerente General"):
        with st.spinner("El Director General está recopilando y analizando los datos de todos los departamentos..."):
            prompt_sys = obtener_prompt_agente("Director General")
            prompt_user = "Analiza la situación actual de todos los departamentos en base a sus tablas de datos compartidas. Evalúa si se están cumpliendo las metas empresariales de forma estratégica y genera un informe de estado para mí."
            informe = consultar_openrouter(prompt_sys, prompt_user)
            st.session_state.ultimo_informe = informe
            st.rerun()
            
    if "ultimo_informe" in st.session_state:
        st.markdown(st.session_state.ultimo_informe)
    else:
        st.info("Haz clic en el botón superior para que el Agente Director General evalúe la situación de tu negocio en tiempo real.")

    st.markdown("---")
    st.subheader("Estado Actual de Coordinación Inter-Agente")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='agent-card'><b>💰 Agente Financiero</b><br><small>Evaluando caja y flujos de egresos estratégicos.</small></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='agent-card'><b>📦 Agente de Inventario</b><br><small>Supervisando stock de alta y baja rotación.</small></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='agent-card'><b>⚖️ Agente de Impuestos</b><br><small>Calculando retenciones, IVA y provisiones del ISR.</small></div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='agent-card'><b>📣 Agente de Mercadeo</b><br><small>Diseñando campañas de conversión y optimizando pauta.</small></div>", unsafe_allow_html=True)

# ------------------------------------------
# VISTA 2: ASIGNACIÓN DE TAREAS
# ------------------------------------------
elif opcion_menu == "Asignación de Tareas":
    st.header("📋 Planificación de Tareas Operativas")
    
    # MODO 3: PILOTO AUTOMÁTICO
    st.subheader("🤖 Modo Piloto Automático")
    st.write("Permite que el Agente Director General examine proactivamente las métricas de la empresa en la base de datos compartida y asigne de manera autónoma las prioridades del día para cada uno de los especialistas.")
    
    if st.button("🚀 Activar Piloto Automático"):
        with st.spinner("El Director General está redactando la minuta operativa de hoy..."):
            prompt_sys = obtener_prompt_agente("Director General")
            prompt_user = """Genera un listado de tareas operativas críticas para hoy basado en los datos de la empresa. El formato debe ser estrictamente un arreglo JSON, sin explicaciones antes o después de la estructura:
            [
              {"agente": "Financiero", "descripcion": "Descripción de la tarea basada en los datos financieros actuales"},
              {"agente": "Inventario", "descripcion": "Descripción de la tarea basada en las alertas de inventario"},
              {"agente": "Impuestos", "descripcion": "Descripción de la tarea de provisiones o fechas límite"},
              {"agente": "Mercadeo", "descripcion": "Descripción de la tarea para promocionar productos de baja rotación o mejorar conversión"}
            ]"""
            
            respuesta = consultar_openrouter(prompt_sys, prompt_user)
            try:
                nuevas_tareas = extraer_json_de_respuesta(respuesta)
                for nt in nuevas_tareas:
                    nuevo_id = max([t["id"] for t in st.session_state.tareas]) + 1 if st.session_state.tareas else 1
                    st.session_state.tareas.append({
                        "id": nuevo_id,
                        "agente": nt["agente"],
                        "descripcion": nt["descripcion"],
                        "estado": "Pendiente",
                        "fecha": str(datetime.date.today())
                    })
                st.success("¡Operación exitosa! Las tareas automáticas se han inyectado en el pizarrón de actividades.")
                st.rerun()
            except Exception as e:
                st.error("Ocurrió un inconveniente al estructurar el JSON de tareas automáticas. Intenta ejecutarlo de nuevo.")
                with st.expander("Ver Respuesta Original"):
                    st.text(respuesta)

    st.markdown("---")
    
    # MODO 1 Y 2: CENTRALIZADO Y DIRECTO
    st.subheader("➕ Creación de Tareas Manual o Centralizada")
    col_modo1, col_modo2 = st.columns(2)
    
    with col_modo1:
        st.markdown("**Modo 1: Asignación Directa a Especialista**")
        with st.form("form_directo", clear_on_submit=True):
            agente_dest = st.selectbox("Asignar directamente a:", ["Financiero", "Inventario", "Impuestos", "Mercadeo"])
            desc_tarea = st.text_input("Especifica la tarea:")
            btn_directo = st.form_submit_button("Asignar Tarea Directa")
            
            if btn_directo:
                if desc_tarea:
                    nuevo_id = max([t["id"] for t in st.session_state.tareas]) + 1 if st.session_state.tareas else 1
                    st.session_state.tareas.append({
                        "id": nuevo_id,
                        "agente": agente_dest,
                        "descripcion": desc_tarea,
                        "estado": "Pendiente",
                        "fecha": str(datetime.date.today())
                    })
                    st.success(f"Tarea asignada directamente al especialista {agente_dest}.")
                    st.rerun()
                else:
                    st.warning("Escribe la descripción antes de enviar.")

    with col_modo2:
        st.markdown("**Modo 2: Instrucción General al Director General**")
        with st.form("form_director", clear_on_submit=True):
            instruccion_global = st.text_area("Orden global para la directiva:", placeholder="Ej: Necesitamos lanzar una oferta para el teclado de baja rotación usando las ganancias de caja.")
            btn_global = st.form_submit_button("Delegar por Gerencia")
            
            if btn_global:
                if instruccion_global:
                    with st.spinner("El Gerente General está organizando la logística..."):
                        prompt_sys = obtener_prompt_agente("Director General")
                        prompt_user = f"""El dueño de la empresa te ha dado la siguiente orden: "{instruccion_global}".
                        Por favor, delega y divide este requerimiento en subtareas específicas para cada especialista involucrado.
                        Retorna la respuesta estrictamente estructurada en este formato JSON, sin texto explicativo extra:
                        [
                          {{"agente": "Nombre del agente", "descripcion": "Tarea específica"}}
                        ]"""
                        
                        respuesta = consultar_openrouter(prompt_sys, prompt_user)
                        try:
                            tareas_desglosadas = extraer_json_de_respuesta(respuesta)
                            for nt in tareas_desglosadas:
                                nuevo_id = max([t["id"] for t in st.session_state.tareas]) + 1 if st.session_state.tareas else 1
                                st.session_state.tareas.append({
                                    "id": nuevo_id,
                                    "agente": nt["agente"],
                                    "descripcion": nt["descripcion"],
                                    "estado": "Pendiente",
                                    "fecha": str(datetime.date.today())
                                })
                            st.success("La Gerencia General ha procesado la directiva y coordinado a los subordinados correspondientes.")
                            st.rerun()
                        except Exception as e:
                            st.error("No se pudo parsear la respuesta estructurada de la gerencia. Por favor, reintenta.")
                else:
                    st.warning("Escribe un mensaje explicativo.")

    st.markdown("---")
    st.subheader("📋 Pizarrón del día de hoy")
    if st.session_state.tareas:
        df_tareas = pd.DataFrame(st.session_state.tareas)
        st.dataframe(df_tareas, use_container_width=True, hide_index=True)
        
        # Panel para la gestión rápida del estado de tareas
        col_id, col_est, col_btn = st.columns([1, 2, 2])
        with col_id:
            id_cambiar = st.number_input("ID de Tarea", min_value=1, step=1)
        with col_est:
            nuevo_estado = st.selectbox("Cambiar estado a:", ["Pendiente", "En Proceso", "Completada"])
        with col_btn:
            st.write("")
            st.write("")
            if st.button("Actualizar Tarea"):
                tarea_encontrada = False
                for t in st.session_state.tareas:
                    if t["id"] == id_cambiar:
                        t["estado"] = nuevo_estado
                        tarea_encontrada = True
                        break
                if tarea_encontrada:
                    st.success(f"La tarea #{id_cambiar} se actualizó con éxito a '{nuevo_estado}'.")
                    st.rerun()
                else:
                    st.error(f"No se encontró ninguna tarea con el ID #{id_cambiar}.")
    else:
        st.info("No hay tareas programadas para el día de hoy.")

# ------------------------------------------
# VISTA 3: CHATBOT MULTI-AGENTE
# ------------------------------------------
elif opcion_menu == "Chatbot con Agentes":
    st.header("💬 Sala de Reuniones Virtual (Chatbot)")
    st.write("Dialoga y asesórate directamente con cualquier agente de la empresa. Al tener acceso a la memoria compartida, sabrán exactamente las acciones tomadas por sus compañeros.")
    
    interlocutor = st.selectbox("¿Con quién deseas interactuar hoy?", ["Director General", "Financiero", "Inventario", "Impuestos", "Mercadeo"])
    
    # Renderizar el historial de conversación en forma de burbujas de diálogo estructurado
    for mensaje in st.session_state.historial_chat:
        clase_burbuja = "user-bubble" if mensaje["rol"] == "Usuario" else "agent-bubble"
        st.markdown(f"<div class='chat-bubble {clase_burbuja}'><b>{mensaje['rol']}:</b><br>{mensaje['mensaje']}</div>", unsafe_allow_html=True)
        
    # Formulario para enviar consultas
    with st.form("input_chat", clear_on_submit=True):
        msg_usuario = st.text_input("Escribe tu consulta o instrucción al equipo:")
        enviar_chat = st.form_submit_button("Enviar Mensaje")
        
    if enviar_chat and msg_usuario:
        # Registrar intervención del usuario
        st.session_state.historial_chat.append({"rol": "Usuario", "mensaje": msg_usuario})
        
        with st.spinner(f"El Agente {interlocutor} está analizando los pizarrones de datos y preparando su informe..."):
            prompt_sys = obtener_prompt_agente(interlocutor)
            # Pasamos un contexto con los mensajes de la conversación más recientes
            contexto_conversacion = "\n".join([f"{m['rol']}: {m['mensaje']}" for m in st.session_state.historial_chat[-6:]])
            prompt_final_user = f"Historial reciente de la conversación:\n{contexto_conversacion}\n\nPregunta o instrucción final del usuario: {msg_usuario}"
            
            respuesta_agente = consultar_openrouter(prompt_sys, prompt_final_user)
            st.session_state.historial_chat.append({"rol": interlocutor, "mensaje": respuesta_agente})
        st.rerun()

# ------------------------------------------
# VISTA 4: CARGA DE DATOS (CSV)
# ------------------------------------------
elif opcion_menu == "Carga de Datos (CSV)":
    st.header("📂 Evaluación de Entrada y Carga de Estructuras")
    st.write("Carga las plantillas empresariales con datos de tu negocio real. Los agentes adaptarán automáticamente su análisis a las nuevas bases de datos compartidas.")
    
    # Descarga de estructuras base
    st.subheader("📥 Descargar Plantillas Formateadas")
    st.write("Si no tienes plantillas a mano, puedes descargar las que usa la aplicación por defecto para estructurar tu información:")
    
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    with col_dl1:
        csv_inv = st.session_state.datos_empresa["inventario"].to_csv(index=False).encode('utf-8')
        st.download_button("Descargar Plantilla Inventario", data=csv_inv, file_name="inventario_ejemplo.csv", mime="text/csv")
    with col_dl2:
        csv_caja = st.session_state.datos_empresa["caja"].to_csv(index=False).encode('utf-8')
        st.download_button("Descargar Plantilla Caja", data=csv_caja, file_name="caja_ejemplo.csv", mime="text/csv")
    with col_dl3:
        csv_mkt = st.session_state.datos_empresa["mercadeo"].to_csv(index=False).encode('utf-8')
        st.download_button("Descargar Plantilla Mercadeo", data=csv_mkt, file_name="mercadeo_ejemplo.csv", mime="text/csv")
        
    st.markdown("---")
    st.subheader("📤 Subir Archivos Reales")
    
    file_inv = st.file_uploader("Subir CSV de Inventario", type=["csv"])
    file_caja = st.file_uploader("Subir CSV de Caja/Finanzas", type=["csv"])
    file_mkt = st.file_uploader("Subir CSV de Estrategia de Mercadeo", type=["csv"])
    
    if file_inv:
        st.session_state.datos_empresa["inventario"] = pd.read_csv(file_inv)
        st.success("CSV de Inventario cargado en la memoria central.")
    if file_caja:
        st.session_state.datos_empresa["caja"] = pd.read_csv(file_caja)
        st.success("CSV de Caja cargado en la memoria central.")
    if file_mkt:
        st.session_state.datos_empresa["mercadeo"] = pd.read_csv(file_mkt)
        st.success("CSV de Mercadeo cargado en la memoria central.")

# ------------------------------------------
# VISTA 5: DATOS DE LA EMPRESA
# ------------------------------------------
elif opcion_menu == "Datos de la Empresa":
    st.header("💾 Memoria de Datos Compartida")
    st.write("Visualiza la base de datos viva que consultan los agentes para coordinarse de manera óptima.")
    
    tab1, tab2, tab3 = st.tabs(["📦 Inventario de Productos", "💰 Flujo de Caja", "📣 Campañas de Mercadeo"])
    
    with tab1:
        st.dataframe(st.session_state.datos_empresa["inventario"], use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(st.session_state.datos_empresa["caja"], use_container_width=True, hide_index=True)
    with tab3:
        st.dataframe(st.session_state.datos_empresa["mercadeo"], use_container_width=True, hide_index=True)
