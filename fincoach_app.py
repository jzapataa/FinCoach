from datetime import datetime
import os

import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


# ============================================================
# Configuración de página
# ============================================================

st.set_page_config(
    page_title="FinCoach AI V2",
    page_icon="💸",
    layout="wide"
)

st.title("💸 FinCoach AI V2")
st.markdown(
    """
    Asistente de salud financiera personal.  
    Esta V2 separa correctamente **hipoteca/vivienda** de **deuda no hipotecaria**.
    
    > Herramienta educativa y de organización financiera.  
    > No sustituye a un asesor financiero profesional.
    """
)


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.header("Configuración")

    model_name = st.selectbox(
        "Modelo",
        ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
    )

    temperature = st.slider(
        "Temperatura",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.1,
        help="Para análisis financiero conviene usar valores bajos."
    )

    st.divider()

    modo_analisis = st.selectbox(
        "Modo de análisis",
        [
            "Diagnóstico completo",
            "Plan de ahorro",
            "Análisis de vivienda/hipoteca",
            "Análisis de deudas",
            "Plan de emergencia",
            "Preparación para invertir"
        ]
    )


# ============================================================
# API Key
# ============================================================

if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

if "GOOGLE_API_KEY" not in os.environ:
    st.error("No se ha encontrado GOOGLE_API_KEY. Configúrala en los secrets del despliegue.")
    st.stop()


# ============================================================
# Modelo
# ============================================================

chat_model = ChatGoogleGenerativeAI(
    model=model_name,
    temperature=temperature
)


# ============================================================
# Funciones de cálculo
# ============================================================

def porcentaje(valor, total):
    if total <= 0:
        return 0
    return round((valor / total) * 100, 2)


def calcular_salud_financiera(
    ingresos_mensuales,
    coste_vivienda_mensual,
    gastos_fijos_sin_vivienda,
    gastos_variables_esenciales,
    gastos_ocio,
    pago_deudas_no_hipotecarias,
    deuda_no_hipotecaria_total,
    hipoteca_pendiente,
    ahorro_actual,
    ahorro_inversion_mensual
):
    gastos_basicos = (
        coste_vivienda_mensual
        + gastos_fijos_sin_vivienda
        + gastos_variables_esenciales
        + pago_deudas_no_hipotecarias
    )

    gastos_totales_sin_ahorro = gastos_basicos + gastos_ocio

    margen_antes_ahorro = ingresos_mensuales - gastos_totales_sin_ahorro
    margen_final = margen_antes_ahorro - ahorro_inversion_mensual

    tasa_vivienda = porcentaje(coste_vivienda_mensual, ingresos_mensuales)
    tasa_gastos_fijos_sin_vivienda = porcentaje(gastos_fijos_sin_vivienda, ingresos_mensuales)
    tasa_variables_esenciales = porcentaje(gastos_variables_esenciales, ingresos_mensuales)
    tasa_ocio = porcentaje(gastos_ocio, ingresos_mensuales)
    tasa_deuda_no_hipotecaria = porcentaje(pago_deudas_no_hipotecarias, ingresos_mensuales)
    tasa_ahorro_inversion = porcentaje(ahorro_inversion_mensual, ingresos_mensuales)
    tasa_capacidad_ahorro = porcentaje(margen_antes_ahorro, ingresos_mensuales)
    tasa_gastos_basicos = porcentaje(gastos_basicos, ingresos_mensuales)

    if gastos_basicos > 0:
        meses_colchon_basico = round(ahorro_actual / gastos_basicos, 1)
    else:
        meses_colchon_basico = 0

    if gastos_totales_sin_ahorro > 0:
        meses_colchon_total = round(ahorro_actual / gastos_totales_sin_ahorro, 1)
    else:
        meses_colchon_total = 0

    # ========================================================
    # Scoring V2
    # La hipoteca NO penaliza igual que deuda de consumo.
    # Se penaliza si la cuota mensual de vivienda pesa demasiado.
    # ========================================================

    score = 100

    # Margen mensual final
    if margen_final < 0:
        score -= 30
    elif margen_final < ingresos_mensuales * 0.05:
        score -= 15
    elif margen_final < ingresos_mensuales * 0.10:
        score -= 8

    # Capacidad potencial de ahorro
    if tasa_capacidad_ahorro < 5:
        score -= 25
    elif tasa_capacidad_ahorro < 10:
        score -= 15
    elif tasa_capacidad_ahorro < 20:
        score -= 7

    # Coste de vivienda
    if tasa_vivienda > 40:
        score -= 20
    elif tasa_vivienda > 35:
        score -= 12
    elif tasa_vivienda > 30:
        score -= 6

    # Deuda no hipotecaria
    if tasa_deuda_no_hipotecaria > 25:
        score -= 25
    elif tasa_deuda_no_hipotecaria > 15:
        score -= 15
    elif tasa_deuda_no_hipotecaria > 10:
        score -= 8

    # Fondo de emergencia según gastos básicos
    if meses_colchon_basico < 1:
        score -= 25
    elif meses_colchon_basico < 3:
        score -= 15
    elif meses_colchon_basico < 6:
        score -= 7

    # Ocio excesivo, penalización suave
    if tasa_ocio > 25:
        score -= 10
    elif tasa_ocio > 20:
        score -= 6
    elif tasa_ocio > 15:
        score -= 3

    # Deuda no hipotecaria total alta
    if deuda_no_hipotecaria_total > ingresos_mensuales * 6:
        score -= 15
    elif deuda_no_hipotecaria_total > ingresos_mensuales * 3:
        score -= 8

    score = max(0, min(100, round(score)))

    if score >= 80:
        nivel = "Buena"
    elif score >= 60:
        nivel = "Mejorable"
    elif score >= 40:
        nivel = "Delicada"
    else:
        nivel = "Crítica"

    return {
        "gastos_basicos": gastos_basicos,
        "gastos_totales_sin_ahorro": gastos_totales_sin_ahorro,
        "margen_antes_ahorro": margen_antes_ahorro,
        "margen_final": margen_final,
        "tasa_vivienda": tasa_vivienda,
        "tasa_gastos_fijos_sin_vivienda": tasa_gastos_fijos_sin_vivienda,
        "tasa_variables_esenciales": tasa_variables_esenciales,
        "tasa_ocio": tasa_ocio,
        "tasa_deuda_no_hipotecaria": tasa_deuda_no_hipotecaria,
        "tasa_ahorro_inversion": tasa_ahorro_inversion,
        "tasa_capacidad_ahorro": tasa_capacidad_ahorro,
        "tasa_gastos_basicos": tasa_gastos_basicos,
        "meses_colchon_basico": meses_colchon_basico,
        "meses_colchon_total": meses_colchon_total,
        "score": score,
        "nivel": nivel,
        "hipoteca_pendiente": hipoteca_pendiente,
        "deuda_no_hipotecaria_total": deuda_no_hipotecaria_total
    }


def interpretar_ratio_vivienda(tasa_vivienda):
    if tasa_vivienda <= 25:
        return "Cómodo"
    elif tasa_vivienda <= 35:
        return "Razonable"
    elif tasa_vivienda <= 40:
        return "Alto"
    else:
        return "Muy alto"


def interpretar_deuda_no_hipotecaria(tasa_deuda):
    if tasa_deuda == 0:
        return "Sin deuda no hipotecaria"
    elif tasa_deuda <= 10:
        return "Controlada"
    elif tasa_deuda <= 20:
        return "Vigilar"
    else:
        return "Alta"


# ============================================================
# Prompt
# ============================================================

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
Eres FinCoach AI, un asistente experto en salud financiera personal.

Tu objetivo es ayudar al usuario a entender su situación financiera, organizarse mejor,
detectar riesgos y crear un plan de acción realista.

Reglas importantes:
- No eres asesor financiero regulado.
- No recomiendes productos financieros concretos.
- No digas "compra este ETF", "vende esto" o "invierte en X".
- Puedes hablar de conceptos generales: fondo de emergencia, ahorro, presupuesto, deuda, diversificación, inversión periódica, control de gastos.
- No trates la hipoteca igual que una deuda de consumo.
- La hipoteca debe analizarse como coste de vivienda, deuda garantizada y compromiso de largo plazo.
- La deuda no hipotecaria incluye tarjetas, préstamos personales, financiación, coche, compras aplazadas u otras deudas de consumo.
- Si hay poca liquidez, prioriza fondo de emergencia antes que invertir más.
- Si hay deuda no hipotecaria cara, prioriza reducirla antes que aumentar inversión.
- Sé claro, directo y práctico.
- No juzgues al usuario.
- Responde en español.

Formato de respuesta:

## 1. Diagnóstico general
Explica la situación financiera global.

## 2. Análisis de vivienda/hipoteca
Analiza el coste mensual de vivienda sobre ingresos.
Si hay hipoteca pendiente, aclara que no es necesariamente mala, pero sí un compromiso relevante.

## 3. Análisis de deuda no hipotecaria
Evalúa si hay deudas de consumo, préstamos, tarjetas o financiación.
Indica si deberían ser prioridad.

## 4. Fondo de emergencia
Valora si el colchón actual es suficiente usando gastos básicos y gastos totales.

## 5. Capacidad de ahorro
Analiza margen mensual, ahorro actual y capacidad potencial.

## 6. Puntos fuertes
Lista aspectos positivos.

## 7. Riesgos o puntos débiles
Lista riesgos detectados.

## 8. Prioridades
Ordena qué debería hacer primero, segundo y tercero.

## 9. Plan de acción a 30 días
Da acciones concretas y realistas para el próximo mes.

## 10. Plan a 3 meses
Da una estrategia sencilla para mejorar la situación.

## 11. Recomendación final
Da una conclusión clara y accionable.

## 12. Aviso
Incluye un aviso breve indicando que esto es orientación educativa y no asesoramiento financiero personalizado regulado.
"""
        ),
        (
            "human",
            """
Modo de análisis solicitado:
{modo_analisis}

Datos del usuario:

Ingresos mensuales netos:
{ingresos_mensuales} €

Tipo de vivienda:
{tipo_vivienda}

Coste mensual de vivienda:
{coste_vivienda_mensual} €

Hipoteca pendiente:
{hipoteca_pendiente} €

Gastos fijos sin vivienda:
{gastos_fijos_sin_vivienda} €

Gastos variables esenciales:
{gastos_variables_esenciales} €

Gastos de ocio/no esenciales:
{gastos_ocio} €

Pago mensual de deudas no hipotecarias:
{pago_deudas_no_hipotecarias} €

Deuda no hipotecaria total:
{deuda_no_hipotecaria_total} €

Ahorro líquido actual:
{ahorro_actual} €

Ahorro o inversión mensual actual:
{ahorro_inversion_mensual} €

Objetivo financiero principal:
{objetivo_financiero}

Horizonte del objetivo:
{horizonte_objetivo}

Perfil de riesgo declarado:
{perfil_riesgo}

Notas adicionales:
{notas_adicionales}

Métricas calculadas por la aplicación:

Gastos básicos mensuales:
{gastos_basicos} €

Gastos totales sin contar ahorro/inversión:
{gastos_totales_sin_ahorro} €

Margen mensual antes de ahorro/inversión:
{margen_antes_ahorro} €

Margen final después de ahorro/inversión:
{margen_final} €

Porcentaje de vivienda sobre ingresos:
{tasa_vivienda} %

Porcentaje de gastos fijos sin vivienda:
{tasa_gastos_fijos_sin_vivienda} %

Porcentaje de variables esenciales:
{tasa_variables_esenciales} %

Porcentaje de ocio/no esenciales:
{tasa_ocio} %

Porcentaje de deuda no hipotecaria mensual:
{tasa_deuda_no_hipotecaria} %

Porcentaje de ahorro/inversión actual:
{tasa_ahorro_inversion} %

Capacidad potencial de ahorro:
{tasa_capacidad_ahorro} %

Gastos básicos sobre ingresos:
{tasa_gastos_basicos} %

Meses de colchón cubriendo gastos básicos:
{meses_colchon_basico}

Meses de colchón cubriendo gastos totales:
{meses_colchon_total}

Puntuación de salud financiera:
{score}/100

Nivel de salud financiera:
{nivel}

Interpretación del ratio vivienda:
{interpretacion_vivienda}

Interpretación deuda no hipotecaria:
{interpretacion_deuda}
"""
        )
    ]
)

cadena = prompt_template | chat_model


# ============================================================
# Estado
# ============================================================

if "ultimo_informe" not in st.session_state:
    st.session_state.ultimo_informe = ""

if "historico_informes" not in st.session_state:
    st.session_state.historico_informes = []


# ============================================================
# Formulario principal
# ============================================================

with st.form("formulario_financiero_v2"):
    st.subheader("📌 Datos financieros")

    col1, col2 = st.columns(2)

    with col1:
        ingresos_mensuales = st.number_input(
            "Ingresos mensuales netos (€)",
            min_value=0.0,
            value=2000.0,
            step=50.0
        )

        tipo_vivienda = st.selectbox(
            "Tipo de vivienda",
            [
                "Hipoteca fija",
                "Hipoteca variable",
                "Hipoteca mixta",
                "Alquiler",
                "Vivienda pagada",
                "Sin coste de vivienda",
                "Otro"
            ]
        )

        coste_vivienda_mensual = st.number_input(
            "Coste mensual de vivienda (€)",
            min_value=0.0,
            value=300.0,
            step=25.0,
            help="Hipoteca o alquiler mensual. No incluyas suministros aquí."
        )

        hipoteca_pendiente = st.number_input(
            "Hipoteca pendiente (€)",
            min_value=0.0,
            value=45000.0,
            step=1000.0,
            help="Solo si tienes hipoteca. Si estás de alquiler, deja 0."
        )

        gastos_fijos_sin_vivienda = st.number_input(
            "Gastos fijos sin vivienda (€)",
            min_value=0.0,
            value=400.0,
            step=25.0,
            help="Luz, agua, internet, seguros, gimnasio, móvil, suscripciones, etc."
        )

    with col2:
        gastos_variables_esenciales = st.number_input(
            "Gastos variables esenciales (€)",
            min_value=0.0,
            value=350.0,
            step=25.0,
            help="Comida, gasolina, transporte, farmacia, gastos básicos variables."
        )

        gastos_ocio = st.number_input(
            "Gastos de ocio/no esenciales (€)",
            min_value=0.0,
            value=250.0,
            step=25.0,
            help="Restaurantes, ropa, ocio, caprichos, compras no esenciales."
        )

        pago_deudas_no_hipotecarias = st.number_input(
            "Pago mensual de deudas no hipotecarias (€)",
            min_value=0.0,
            value=0.0,
            step=25.0,
            help="Préstamos personales, coche, tarjetas, financiación, compras aplazadas."
        )

        deuda_no_hipotecaria_total = st.number_input(
            "Deuda no hipotecaria total (€)",
            min_value=0.0,
            value=0.0,
            step=100.0,
            help="No incluyas aquí la hipoteca."
        )

        ahorro_actual = st.number_input(
            "Ahorro líquido actual (€)",
            min_value=0.0,
            value=2500.0,
            step=100.0,
            help="Dinero disponible en cuenta, fondo monetario o equivalente líquido."
        )

        ahorro_inversion_mensual = st.number_input(
            "Ahorro o inversión mensual actual (€)",
            min_value=0.0,
            value=200.0,
            step=25.0
        )

    st.divider()

    col3, col4 = st.columns(2)

    with col3:
        perfil_riesgo = st.selectbox(
            "Perfil de riesgo",
            ["Conservador", "Moderado", "Agresivo", "No lo sé"]
        )

    with col4:
        horizonte_objetivo = st.selectbox(
            "Horizonte del objetivo",
            [
                "Menos de 6 meses",
                "6-12 meses",
                "1-3 años",
                "Más de 3 años",
                "No lo tengo claro"
            ]
        )

    objetivo_financiero = st.text_input(
        "Objetivo financiero principal",
        value="Crear un fondo de emergencia y mejorar mi capacidad de ahorro",
        placeholder="Ej: ahorrar 10.000 €, comprar una casa, eliminar deudas, empezar a invertir..."
    )

    notas_adicionales = st.text_area(
        "Notas adicionales",
        height=100,
        placeholder="Ej: vivo en pareja, tengo ingresos variables, quiero amortizar hipoteca, quiero empezar a invertir..."
    )

    analizar = st.form_submit_button("Analizar salud financiera")


# ============================================================
# Generación de análisis
# ============================================================

if analizar:
    if ingresos_mensuales <= 0:
        st.warning("Introduce unos ingresos mensuales mayores que 0 para poder analizar la situación.")
    else:
        metricas = calcular_salud_financiera(
            ingresos_mensuales=ingresos_mensuales,
            coste_vivienda_mensual=coste_vivienda_mensual,
            gastos_fijos_sin_vivienda=gastos_fijos_sin_vivienda,
            gastos_variables_esenciales=gastos_variables_esenciales,
            gastos_ocio=gastos_ocio,
            pago_deudas_no_hipotecarias=pago_deudas_no_hipotecarias,
            deuda_no_hipotecaria_total=deuda_no_hipotecaria_total,
            hipoteca_pendiente=hipoteca_pendiente,
            ahorro_actual=ahorro_actual,
            ahorro_inversion_mensual=ahorro_inversion_mensual
        )

        interpretacion_vivienda = interpretar_ratio_vivienda(metricas["tasa_vivienda"])
        interpretacion_deuda = interpretar_deuda_no_hipotecaria(metricas["tasa_deuda_no_hipotecaria"])

        st.subheader("📊 Métricas calculadas")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Salud financiera",
                f"{metricas['score']}/100",
                metricas["nivel"]
            )
            st.progress(metricas["score"] / 100)

        with col2:
            st.metric(
                "Vivienda / ingresos",
                f"{metricas['tasa_vivienda']}%",
                interpretacion_vivienda
            )

        with col3:
            st.metric(
                "Deuda no hipotecaria",
                f"{metricas['tasa_deuda_no_hipotecaria']}%",
                interpretacion_deuda
            )

        with col4:
            st.metric(
                "Colchón básico",
                f"{metricas['meses_colchon_basico']} meses"
            )

        col5, col6, col7, col8 = st.columns(4)

        with col5:
            st.metric(
                "Margen final mensual",
                f"{metricas['margen_final']:.2f} €"
            )

        with col6:
            st.metric(
                "Capacidad ahorro",
                f"{metricas['tasa_capacidad_ahorro']}%"
            )

        with col7:
            st.metric(
                "Gastos básicos",
                f"{metricas['gastos_basicos']:.2f} €"
            )

        with col8:
            st.metric(
                "Colchón total",
                f"{metricas['meses_colchon_total']} meses"
            )

        if hipoteca_pendiente > 0:
            st.info(
                "La hipoteca se está tratando como coste de vivienda y compromiso financiero de largo plazo, "
                "no como deuda de consumo."
            )

        if deuda_no_hipotecaria_total > 0:
            st.warning(
                "Hay deuda no hipotecaria. El análisis la tratará como prioridad distinta a la hipoteca."
            )

        st.subheader("🧠 Informe generado")

        datos_prompt = {
            "modo_analisis": modo_analisis,
            "ingresos_mensuales": ingresos_mensuales,
            "tipo_vivienda": tipo_vivienda,
            "coste_vivienda_mensual": coste_vivienda_mensual,
            "hipoteca_pendiente": hipoteca_pendiente,
            "gastos_fijos_sin_vivienda": gastos_fijos_sin_vivienda,
            "gastos_variables_esenciales": gastos_variables_esenciales,
            "gastos_ocio": gastos_ocio,
            "pago_deudas_no_hipotecarias": pago_deudas_no_hipotecarias,
            "deuda_no_hipotecaria_total": deuda_no_hipotecaria_total,
            "ahorro_actual": ahorro_actual,
            "ahorro_inversion_mensual": ahorro_inversion_mensual,
            "objetivo_financiero": objetivo_financiero,
            "horizonte_objetivo": horizonte_objetivo,
            "perfil_riesgo": perfil_riesgo,
            "notas_adicionales": notas_adicionales if notas_adicionales.strip() else "No indicadas",
            "interpretacion_vivienda": interpretacion_vivienda,
            "interpretacion_deuda": interpretacion_deuda,
            **metricas
        }

        try:
            response_placeholder = st.empty()
            full_response = ""

            for chunk in cadena.stream(datos_prompt):
                contenido = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                full_response += contenido
                response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)

            fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

            informe_completo = f"""
# Informe de salud financiera V2

Fecha: {fecha}

## Métricas principales

- Salud financiera: {metricas['score']}/100
- Nivel: {metricas['nivel']}
- Tipo de vivienda: {tipo_vivienda}
- Coste vivienda/ingresos: {metricas['tasa_vivienda']}%
- Interpretación vivienda: {interpretacion_vivienda}
- Hipoteca pendiente: {hipoteca_pendiente:.2f} €
- Deuda no hipotecaria total: {deuda_no_hipotecaria_total:.2f} €
- Deuda no hipotecaria/ingresos mensual: {metricas['tasa_deuda_no_hipotecaria']}%
- Interpretación deuda no hipotecaria: {interpretacion_deuda}
- Margen final mensual: {metricas['margen_final']:.2f} €
- Capacidad potencial de ahorro: {metricas['tasa_capacidad_ahorro']}%
- Colchón cubriendo gastos básicos: {metricas['meses_colchon_basico']} meses
- Colchón cubriendo gastos totales: {metricas['meses_colchon_total']} meses

---

{full_response}
"""

            st.session_state.ultimo_informe = informe_completo

            st.session_state.historico_informes.insert(
                0,
                {
                    "fecha": fecha,
                    "score": metricas["score"],
                    "nivel": metricas["nivel"],
                    "informe": informe_completo
                }
            )

        except Exception as e:
            st.error(f"Error al generar el informe: {str(e)}")
            st.info(
                "Revisa que tengas configurada correctamente la variable de entorno GOOGLE_API_KEY "
                "y que el modelo seleccionado esté disponible."
            )


# ============================================================
# Descargar informe
# ============================================================

if st.session_state.ultimo_informe:
    st.divider()

    st.download_button(
        label="Descargar último informe en Markdown",
        data=st.session_state.ultimo_informe,
        file_name="informe_salud_financiera_v2.md",
        mime="text/markdown"
    )


# ============================================================
# Histórico
# ============================================================

if st.session_state.historico_informes:
    st.divider()
    st.subheader("📚 Histórico de informes")

    for i, item in enumerate(st.session_state.historico_informes[:5], start=1):
        with st.expander(
            f"{i}. {item['fecha']} - Salud financiera {item['score']}/100 ({item['nivel']})"
        ):
            st.markdown(item["informe"])

    if st.button("Limpiar histórico"):
        st.session_state.historico_informes = []
        st.session_state.ultimo_informe = ""
        st.rerun()