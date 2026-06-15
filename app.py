import streamlit as st
import pandas as pd
import requests
import json
import datetime
import io

st.set_page_config(
    page_title="Ecosistema de Agentes Inteligentes",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados para crear una UI premium y adaptativa
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

PLANTILLAS_CSV = {
    "inventario": (
        "ID_Producto,Producto,Categoria,Cantidad,Costo_Unitario,Precio_Venta,Rotacion,Stock_Minimo\n"
        "PROD001,Laptop Dell Inspiron 15,Tecnología,15,450.00,750.00,Alta,5\n"
        "PROD002,Monitor Samsung 24 IPS,Tecnología,40,110.00,195.00,Media,10\n"
        "PROD003,Teclado Mecánico RGB,Accesorios,8,35.00,69.99,Baja,5\n"
        "PROD004,Mouse Ergonómico Inalámbrico,Accesorios,25,18.50,39.99,Alta,8\n"
        "PROD005,Impresora HP DeskJet,Oficina,4,125.00,249.99,Baja,3\n"
        "PROD006,Escritorio de Madera Modular,Oficina,12,180.00,299.90,Media,4"
    ),
    "caja": (
        "Fecha,Concepto,Categoria,Ingreso,Egreso,Saldo_Acumulado,Metodo_Pago\n"
        "2026-06-10,Saldo inicial de operaciones,Apertura,5000.00,0.00,5000.00,Transferencia\n"
        "2026-06-11,Venta de 3 Laptops Dell,Ventas,2250.00,0.00,7250.00,Efectivo\n"
        "2026-06-12,Pago de Energía Eléctrica y Luz,Servicios,0.00,185.50,7064.50,Debito\n"
        "2026-06-13,Adquisición de stock Accesorios,Inventario,0.00,450.00,6614.50,Transferencia\n"
        "2026-06-14,Cobro Factura de Cliente Frecuente,Ventas,1200.00,0.00,7814.50,Cheque\n"
        "2026-06-14,Pago de pauta publicitaria digital,Mercadeo,0.00,250.00,7564.50,Credito"
    ),
    "mercadeo": (
        "ID_Campana,Campana,Canal,Presupuesto_Asignado,Gasto_Actual,Leads_Generados,Conversiones,Estado\n"
        "CAMP001,Cyber Monday Especial,Meta Ads,350.00,320.00,150,12,Activa\n"
        "CAMP002,Descuento Mayoristas,Email Marketing,50.00,45.00,80,18,Completada\n"
        "CAMP003,Inauguración Nueva Sucursal,Google Ads,500.00,150.00,200,5,Activa\n"
        "CAMP004,Liquidación Stock Teclados,TikTok Ads,120.00,120.00,95,8,Pausada"
    ),
    "impuestos": (
        "Periodo,Impuesto,Base_Imponible,Tasa,Monto_Determinado,Estado_Pago,Fecha_Vencimiento\n"
        "2026-05,IVA General Mensual,12500.00,0.12,1500.00,Presentado,2026-06-30\n"
        "2026-05,Pago Trimestral ISR,45000.00,0.05,2250.00,Pendiente,2026-07-15\n"
        "2026-05,Retenciones de ISR a Terceros,3200.00,0.05,160.00,Presentado,2026-06-28\n"
        "2026-06,Provision Mensual Impuestos,8500.00,0.12,1020.00,Pendiente,2026-07-31"
    )
}

if "api_key" not in st.session_state:
    try:
        st.session_state.api_key = st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        st.session_state.api_key = ""

if "config_empresa" not in st.session_state:
    st.session_state.config_empresa = {
        "nombre": "Corporación Alfa, S.A.",
        "tipo": "Comercial / Retail de Tecnología",
        "direccion": "Avenida Reforma 12-56, Zona 10, Guatemala",
        "nit": "9876543-2",
        "metas": "Maximizar el flujo de caja, reducir inventario estancado de baja rotación y provisionar correctamente los pagos de impuestos de fin de mes.",
        "moneda": "$"
    }

# Inicialización segura e incremental de las bases de datos compartidas
if "datos_empresa" not in st.session_state:
    st.session_state.datos_empresa = {}

for clave, plantilla_raw in PLANTILLAS_CSV.items():
    if clave not in st.session_state.datos_empresa:
        st.session_state.datos_empresa[clave] = pd.read_csv(io.StringIO(plantilla_raw))

if "tareas" not in st.session_state:
    st.session_state.tareas = [
        {"id": 1, "agente": "Financiero", "descripcion": "Verificar conciliación de caja y alertar saldo remanente.", "estado": "Pendiente", "fecha": "2026-06-14"},
        {"id": 2, "agente": "Inventario", "descripcion": "Identificar productos en stock mínimo para sugerir reordenamiento.", "estado": "Pendiente", "fecha": "2026-06-14"},
        {"id": 3, "agente": "Impuestos", "descripcion": "Revisar obligaciones de ISR pendientes para el mes entrante.", "estado": "Pendiente", "fecha": "2026-06-14"},
        {"id": 4, "agente": "Mercadeo", "descripcion": "Diseñar pauta en TikTok Ads para el inventario de baja rotación.", "estado": "Pendiente", "fecha": "2026-06-14"}
    ]

if "historial_chat" not in st.session_state:
    st.session_state.historial_chat = [
        {"rol": "Director General", "mensaje": "Saludos. Soy el Director General de tu empresa. Tengo acceso inmediato al estado financiero, los movimientos de caja, inventarios, impuestos y campañas de mercadeo. ¿Qué directrices deseas ordenar hoy?"}
    ]

def consultar_openrouter(prompt_sistema, prompt_usuario):
    if not st.session_state.api_key:
        return "⚠️ Error: No se ha configurado la API Key de OpenRouter. Ingresa tu clave en los secretos de Streamlit o utilízala desde el menú lateral para activar los agentes."
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.session_state.api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Sistema de Gestion Multi-Agente Corporativo"
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
            return f"Error en el servidor de OpenRouter (Código {response.status_code}): {response.text}"
    except Exception as e:
        return f"Error de conectividad de red con OpenRouter: {str(e)}"

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
    """
    return contexto

def obtener_prompt_agente(rol):
    contexto = construir_contexto_empresa()
    moneda = st.session_state.config_empresa.get("moneda", "$")
    
    prompts = {
        "Director General": f"""Eres el Agente Director General (CEO) de la empresa. Tu deber primordial es liderar y coordinar a tus agentes especialistas (Financiero, Inventario, Impuestos y Mercadeo). Tienes una visión global del negocio. Tu tono es profesional, analítico y altamente estratégico. Al responder, evalúa los datos históricos de todas las áreas, señala ineficiencias (por ejemplo: baja rotación en inventarios, impuestos de alto impacto, fugas de dinero en caja o campañas con baja conversión) y explica cómo tus subordinados se van a coordinar para resolverlo de inmediato.
        IMPORTANTE: Toda cifra de dinero que menciones o presupuestes DEBE estar obligatoriamente expresada usando la moneda oficial seleccionada por el usuario: {moneda}.
        {contexto}""",
        
        "Financiero": f"""Eres el Agente Financiero de la empresa. Te encargas de custodiar el dinero de la caja, evaluar márgenes de utilidad de los productos vendidos y vigilar el presupuesto disponible. Debes alertar al CEO si el flujo de caja operativo es deficiente para cubrir las obligaciones de nómina, impuestos o inversiones publicitarias de Mercadeo. Trabaja en sintonía con Inventario para evaluar compras lógicas y con Impuestos para asegurar provisiones.
        IMPORTANTE: Toda cifra de dinero que menciones o presupuestes DEBE estar obligatoriamente expresada usando la moneda oficial seleccionada por el usuario: {moneda}.
        {contexto}""",
        
        "Inventario": f"""Eres el Agente de Inventario. Gestionas el stock de productos, vigilas las mermas, controlas las rotaciones (Alta, Media, Baja) y configuras alertas de stock crítico frente a valores mínimos de seguridad. Trabajas en conjunto con el Financiero para autorizar nuevas compras basadas en liquidez y con el Agente de Mercadeo para armar ofertas sobre productos con rotación 'Baja'.
        IMPORTANTE: Toda cifra de dinero que menciones o presupuestes DEBE estar obligatoriamente expresada usando la moneda oficial seleccionada por el usuario: {moneda}.
        {contexto}""",
        
        "Impuestos": f"""Eres el Agente de Impuestos y Control Fiscal. Eres responsable de que la empresa se encuentre al día con el fisco, previendo pagos de IVA, ISR y retenciones de manera oportuna. Debes alertar al Financiero sobre los montos que deben estar resguardados en caja para el pago de impuestos pendientes para evitar multas penales u operativas.
        IMPORTANTE: Toda cifra de dinero que menciones o presupuestes DEBE estar obligatoriamente expresada usando la moneda oficial seleccionada por el usuario: {moneda}.
        {contexto}""",
        
        "Mercadeo": f"""Eres el Agente de Mercadeo. Tu foco es maximizar la visibilidad de la marca, generar leads calificados y optimizar la tasa de conversión de las campañas de publicidad. Debes utilizar los datos del Agente de Inventario para saber qué productos necesitan pauta urgente (baja rotación) y reportar al Financiero el Retorno de Inversión publicitaria (ROI) para solicitar presupuesto adicional.
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

with st.sidebar:
    st.header("🔑 Acceso y Perfil")
    
    st.session_state.api_key = st.text_input(
        "OpenRouter API Key:", 
        value=st.session_state.api_key, 
        type="password",
        help="Si no la has ingresado en los secretos de Streamlit (OPENROUTER_API_KEY), puedes pegarla aquí."
    )
    
    st.markdown("---")
    st.header("📌 Navegación")
    opcion_menu = st.radio("Secciones de Trabajo:", [
        "Dashboard General", 
        "Carga y Plantillas CSV", 
        "Asignación de Tareas", 
        "Chatbot con Agentes", 
        "Datos del Pizarrón"
    ])
    
    st.markdown("---")
    st.subheader("Configuración Fiscal y Perfil")
    st.session_state.config_empresa["nombre"] = st.text_input("Empresa S.A.:", st.session_state.config_empresa["nombre"])
    st.session_state.config_empresa["tipo"] = st.text_input("Tipo de Comercio:", st.session_state.config_empresa["tipo"])
    st.session_state.config_empresa["direccion"] = st.text_input("Domicilio Fiscal:", st.session_state.config_empresa["direccion"])
    st.session_state.config_empresa["nit"] = st.text_input("NIT de la Empresa:", st.session_state.config_empresa["nit"])
    st.session_state.config_empresa["metas"] = st.text_area("Objetivos de Operaciones:", st.session_state.config_empresa["metas"])
    
    # Selector de Divisas Corporativas
    moneda_actual = st.session_state.config_empresa.get("moneda", "$")
    lista_opciones_divisa = ["$", "Q", "€", "MXN", "COP", "CLP", "PEN", "Bs.", "HNL", "NIO", "CRC", "Personalizado"]
    
    try:
        def_idx = lista_opciones_divisa.index(moneda_actual)
    except ValueError:
        def_idx = 11  # Indice para "Personalizado" si no está en la lista común
        
    moneda_seleccionada = st.selectbox(
        "Moneda / Divisa:",
        options=lista_opciones_divisa,
        index=def_idx,
        help="Elige el símbolo o divisa predeterminado para tus reportes e informes de agentes."
    )
    
    if moneda_seleccionada == "Personalizado":
        st.session_state.config_empresa["moneda"] = st.text_input(
            "Especifica el símbolo de tu moneda:", 
            value=moneda_actual if moneda_actual != "Personalizado" else "$"
        )
    else:
        st.session_state.config_empresa["moneda"] = moneda_seleccionada

if opcion_menu == "Dashboard General":
    st.header("📈 Informe del Agente Director General")
    st.write("Análisis general de la empresa recopilado de forma cruzada por los agentes a cargo de los datos.")
    
    moneda = st.session_state.config_empresa.get("moneda", "$")
    
    try:
        df_inv = st.session_state.datos_empresa["inventario"]
        df_caj = st.session_state.datos_empresa["caja"]
        df_mkt = st.session_state.datos_empresa["mercadeo"]
        df_imp = st.session_state.datos_empresa["impuestos"]
        
        val_inv = (df_inv["Cantidad"] * df_inv["Costo_Unitario"]).sum()
        caja_act = df_caj["Saldo_Acumulado"].iloc[-1] if not df_caj.empty else 0.0
        leads_tot = df_mkt["Leads_Generados"].sum() if not df_mkt.empty else 0
        imp_pend = df_imp[df_imp["Estado_Pago"] == "Pendiente"]["Monto_Determinado"].sum() if not df_imp.empty else 0.0
    except Exception:
        val_inv, caja_act, leads_tot, imp_pend = 0.0, 0.0, 0, 0.0

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(f"""<div class='metric-container'>
            <small style='color: #64748b;'>📦 Valor de Inventario</small><br>
            <b style='font-size: 22px; color: #0f172a;'>{moneda} {val_inv:,.2f}</b>
        </div>""", unsafe_allow_html=True)
    with col_m2:
        st.markdown(f"""<div class='metric-container'>
            <small style='color: #64748b;'>💰 Saldo Actual en Caja</small><br>
            <b style='font-size: 22px; color: #16a34a;'>{moneda} {caja_act:,.2f}</b>
        </div>""", unsafe_allow_html=True)
    with col_m3:
        st.markdown(f"""<div class='metric-container'>
            <small style='color: #64748b;'>📣 Leads Generados (Mkt)</small><br>
            <b style='font-size: 22px; color: #2563eb;'>{leads_tot:,} leads</b>
        </div>""", unsafe_allow_html=True)
    with col_m4:
        st.markdown(f"""<div class='metric-container'>
            <small style='color: #64748b;'>⚖️ Impuestos por Pagar</small><br>
            <b style='font-size: 22px; color: #dc2626;'>{moneda} {imp_pend:,.2f}</b>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔄 Generar Informe de Auditoría Operativa con el Director General"):
        with st.spinner("El CEO está llamando a los jefes de departamento y leyendo los libros de control corporativo..."):
            prompt_sys = obtener_prompt_agente("Director General")
            prompt_user = f"Analiza detalladamente los números que tenemos en inventario, balances de caja, rendimiento de publicidad y obligaciones tributarias pendientes. Reporta de forma ejecutiva un diagnóstico crítico de la situación. Recuerda usar siempre la moneda '{moneda}' en tu respuesta."
            informe = consultar_openrouter(prompt_sys, prompt_user)
            st.session_state.ultimo_informe = informe
            st.rerun()
            
    if "ultimo_informe" in st.session_state:
        st.markdown("### 📋 Evaluación Operativa de la Dirección General:")
        st.markdown(st.session_state.ultimo_informe)
    else:
        st.info("Para recibir un diagnóstico de tus operaciones y cómo interactúan las metas con tus datos reales, haz clic en el botón superior.")

elif opcion_menu == "Carga y Plantillas CSV":
    st.header("📥 Descarga de Plantillas y Carga de Archivos")
    st.write("Para que los agentes inteligentes tomen decisiones, puedes descargar nuestras plantillas estándar, editarlas con tus datos corporativos reales y subirlas nuevamente.")
    
    st.markdown("---")
    st.subheader("1. Descarga de Plantillas Oficiales")
    
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    with col_d1:
        st.write("📦 **Módulo de Inventario**")
        st.download_button(
            label="Descargar CSV de Inventario",
            data=PLANTILLAS_CSV["inventario"],
            file_name="plantilla_inventario.csv",
            mime="text/csv"
        )
    with col_d2:
        st.write("💰 **Módulo de Caja/Finanzas**")
        st.download_button(
            label="Descargar CSV de Caja",
            data=PLANTILLAS_CSV["caja"],
            file_name="plantilla_caja.csv",
            mime="text/csv"
        )
    with col_d3:
        st.write("📣 **Módulo de Mercadeo**")
        st.download_button(
            label="Descargar CSV de Mercadeo",
            data=PLANTILLAS_CSV["mercadeo"],
            file_name="plantilla_mercadeo.csv",
            mime="text/csv"
        )
    with col_d4:
        st.write("⚖️ **Módulo de Impuestos**")
        st.download_button(
            label="Descargar CSV de Impuestos",
            data=PLANTILLAS_CSV["impuestos"],
            file_name="plantilla_impuestos.csv",
            mime="text/csv"
        )
        
    st.markdown("---")
    st.subheader("2. Cargar Archivos de Datos Reales")
    
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        f_inv = st.file_uploader("Subir CSV de Inventario Real", type=["csv"])
        if f_inv:
            try:
                st.session_state.datos_empresa["inventario"] = pd.read_csv(f_inv)
                st.success("✅ Archivo de Inventario actualizado con éxito.")
            except Exception as e:
                st.error(f"Error de formato al leer el CSV: {str(e)}")
                
        f_caj = st.file_uploader("Subir CSV de Caja Real", type=["csv"])
        if f_caj:
            try:
                st.session_state.datos_empresa["caja"] = pd.read_csv(f_caj)
                st.success("✅ Archivo de Caja y Movimientos actualizado con éxito.")
            except Exception as e:
                st.error(f"Error de formato al leer el CSV: {str(e)}")

    with col_u2:
        f_mkt = st.file_uploader("Subir CSV de Mercadeo Real", type=["csv"])
        if f_mkt:
            try:
                st.session_state.datos_empresa["mercadeo"] = pd.read_csv(f_mkt)
                st.success("✅ Archivo de Campañas de Mercadeo actualizado con éxito.")
            except Exception as e:
                st.error(f"Error de formato al leer el CSV: {str(e)}")
                
        f_imp = st.file_uploader("Subir CSV de Impuestos Real", type=["csv"])
        if f_imp:
            try:
                st.session_state.datos_empresa["impuestos"] = pd.read_csv(f_imp)
                st.success("✅ Archivo de Obligaciones de Impuestos actualizado con éxito.")
            except Exception as e:
                st.error(f"Error de formato al leer el CSV: {str(e)}")

elif opcion_menu == "Asignación de Tareas":
    st.header("📋 Tablero de Distribución y Asignación de Tareas")
    st.write("Administra el cronograma operativo de tus agentes utilizando cualquiera de los tres modos de asignación.")
    
    st.subheader("🤖 Modo 3: Piloto Automático de Dirección")
    st.write("El Director General revisa el rendimiento global de la empresa y diseña de forma autónoma misiones de urgencia para resolver cuellos de botella detectados.")
    
    moneda = st.session_state.config_empresa.get("moneda", "$")

    if st.button("🚀 Iniciar Generación en Piloto Automático"):
        with st.spinner("El CEO está examinando las tablas compartidas de impuestos pendientes, rotaciones y dinero disponible..."):
            prompt_sys = obtener_prompt_agente("Director General")
            prompt_user = f"""Evalúa exhaustivamente el estado corporativo y genera un plan de 4 tareas de alta prioridad para hoy (una para cada especialista: Financiero, Inventario, Impuestos, Mercadeo).
            Debes retornar ÚNICAMENTE un arreglo con formato JSON estricto, sin explicaciones previas ni finales. 
            IMPORTANTE: Si mencionas montos o presupuestos en las tareas, utiliza obligatoriamente la divisa oficial definida: {moneda}.
            [
              {{"agente": "Financiero", "descripcion": "Tarea específica basada en saldo actual o egresos"}},
              {{"agente": "Inventario", "descripcion": "Tarea para mitigar productos de rotacion baja o stock critico"}},
              {{"agente": "Impuestos", "descripcion": "Misión para calcular o liquidar obligaciones próximas al vencimiento"}},
              {{"agente": "Mercadeo", "descripcion": "Estrategia puntual de venta basada en productos excedentes"}}
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
                st.rerun()
            except Exception as e:
                st.error("No se pudo estructurar el JSON operativo de forma directa. Inténtalo de nuevo.")
                with st.expander("Ver Reporte Crudo del LLM"):
                    st.text(respuesta)

    st.markdown("---")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("#### 🎯 Modo 1: Asignación Directa")
        with st.form("form_creacion_directa", clear_on_submit=True):
            agente_target = st.selectbox("Asignar directamente a:", ["Financiero", "Inventario", "Impuestos", "Mercadeo"])
            desc_directa = st.text_input("Ingresa los objetivos de la tarea:")
            submit_dir = st.form_submit_button("Crear Tarea")
            
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
                    st.rerun()
                else:
                    st.warning("Escribe una descripción de objetivos.")

    with col_m2:
        st.markdown("#### 🗣️ Modo 2: Dictado Centralizado a Gerencia")
        with st.form("form_creacion_centralizada", clear_on_submit=True):
            orden_general = st.text_area("Orden global o problema genérico:", placeholder="Ej: Se aproxima la declaración de IVA e ISR, y necesitamos liquidez.")
            submit_cen = st.form_submit_button("Asignar por Canal CEO")
            
            if submit_cen:
                if orden_general:
                    with st.spinner("El CEO está reuniendo a los departamentos para coordinar la estrategia..."):
                        prompt_sys = obtener_prompt_agente("Director General")
                        prompt_user = f"""El usuario ha dictado la siguiente orden general: "{orden_general}".
                        Desglosa esta orden en tareas específicas para cada uno de los especialistas involucrados en resolverlo.
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
                            st.rerun()
                        except Exception:
                            st.error("No se pudo interpretar el formato JSON del modelo. Reintenta la asignación.")
                else:
                    st.warning("Digita una directiva global para la empresa.")

    st.markdown("---")
    
    st.subheader("📋 Pizarrón de Operaciones Diario")
    if st.session_state.tareas:
        df_tareas = pd.DataFrame(st.session_state.tareas)
        st.dataframe(df_tareas, use_container_width=True, hide_index=True)
        
        col_tid, col_testado, col_tbtn = st.columns([1, 2, 2])
        with col_tid:
            id_modificar = st.number_input("ID de la Tarea a actualizar:", min_value=1, step=1)
        with col_testado:
            estado_nuevo = st.selectbox("Cambiar estado:", ["Pendiente", "En Proceso", "Completada"])
        with col_tbtn:
            st.write("")
            st.write("")
            if st.button("Guardar Cambios de Tarea"):
                encontrada = False
                for t in st.session_state.tareas:
                    if t["id"] == id_modificar:
                        t["estado"] = estado_nuevo
                        encontrada = True
                        break
                if encontrada:
                    st.success(f"La tarea #{id_modificar} ha cambiado de estado a '{estado_nuevo}'.")
                    st.rerun()
                else:
                    st.error(f"La tarea con el identificador #{id_modificar} no existe.")
    else:
        st.info("No hay asignaciones cargadas para el día de hoy.")

elif opcion_menu == "Chatbot con Agentes":
    st.header("💬 Sala de Reuniones Ejecutiva (Chatbot)")
    st.write("Habla de manera interactiva con tus agentes especialistas. Cada agente conoce la base de datos compartida y cooperará para ayudarte a cumplir tus metas estratégicas.")
    
    interlocutor_activo = st.selectbox("Convocar a reunión a:", ["Director General", "Financiero", "Inventario", "Impuestos", "Mercadeo"])
    moneda = st.session_state.config_empresa.get("moneda", "$")

    for msj in st.session_state.historial_chat:
        clase_b = "user-bubble" if msj["rol"] == "Usuario" else "agent-bubble"
        st.markdown(f"<div class='chat-bubble {clase_b}'><b>{msj['rol']}:</b><br>{msj['mensaje']}</div>", unsafe_allow_html=True)
        
    with st.form("form_chat", clear_on_submit=True):
        input_usr = st.text_input("Introduce tus instrucciones, consultas o inquietudes sobre el estado empresarial:")
        btn_enviar = st.form_submit_button("Enviar Mensaje a la Sala")
        
    if btn_enviar and input_usr:
        st.session_state.historial_chat.append({"rol": "Usuario", "mensaje": input_usr})
        
        with st.spinner(f"El Agente {interlocutor_activo} está analizando las transacciones y preparando su respuesta..."):
            prompt_sys = obtener_prompt_agente(interlocutor_activo)
            dialogo_historico = "\n".join([f"{m['rol']}: {m['mensaje']}" for m in st.session_state.historial_chat[-6:]])
            prompt_completo = f"Historial de conversación reciente:\n{dialogo_historico}\n\nNueva intervención del usuario: {input_usr}\n\nRecuerda usar la divisa oficial definida en el perfil: {moneda}."
            
            respuesta_agente = consultar_openrouter(prompt_sys, prompt_completo)
            st.session_state.historial_chat.append({"rol": interlocutor_activo, "mensaje": respuesta_agente})
        st.rerun()

elif opcion_menu == "Datos del Pizarrón":
    st.header("💾 Registro de Libros de Datos")
    st.write("Esta sección muestra las bases de datos de solo lectura compartidas. Los agentes corporativos consultan estos registros al instante para emitir dictámenes coherentes.")
    
    pestana1, pestana2, pestana3, pestana4 = st.tabs(["📦 Inventario de Productos", "💰 Caja y Egresos", "📣 Campañas de Mercadeo", "⚖️ Impuestos y Provisiones"])
    
    with pestana1:
        st.dataframe(st.session_state.datos_empresa["inventario"], use_container_width=True, hide_index=True)
    with pestana2:
        st.dataframe(st.session_state.datos_empresa["caja"], use_container_width=True, hide_index=True)
    with pestana3:
        st.dataframe(st.session_state.datos_empresa["mercadeo"], use_container_width=True, hide_index=True)
    with pestana4:
        st.dataframe(st.session_state.datos_empresa["impuestos"], use_container_width=True, hide_index=True)
