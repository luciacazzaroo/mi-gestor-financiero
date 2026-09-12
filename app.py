import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Gestor Financiero", page_icon="💰", layout="centered")

if 'movimientos' not in st.session_state:
    st.session_state.movimientos = pd.DataFrame(columns=['Fecha', 'Tipo', 'Categoría', 'Monto'])

if 'inversiones' not in st.session_state:
    st.session_state.inversiones = pd.DataFrame(columns=['Fecha', 'Monto Actual'])

st.title("💰 Gestor Financiero Personal")
st.write("Registrá tus movimientos, controlá tu saldo y visualizá el rendimiento de tus inversiones.")

tab1, tab2, tab3 = st.tabs(["📝 Registro de Movimientos", "💵 Saldo Disponible", "📈 Rendimiento de Inversiones"])

# --- APARTADO 1: REGISTRO DE MOVIMIENTOS ---
with tab1:
    st.header("Ingresar Nuevo Movimiento")
    
    with st.form("form_movimientos", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.radio("Tipo de movimiento", ["Ingreso ⬆️", "Egreso ⬇️"])
            monto = st.number_input("Monto ($)", min_value=0.0, step=1000.0)
        with col2:
            # CAMBIO AQUÍ: Ahora es un campo de texto libre para escribir lo que quieras
            categoria = st.text_input("Categoría", placeholder="Ej: Supermercado, Alquiler, Gimnasio...")
            fecha = st.date_input("Fecha", date.today())
            
        submit_movimiento = st.form_submit_button("Registrar")

    if submit_movimiento and monto > 0:
        # Si no escribe nada en categoría, le asignamos "Sin Categoría" por defecto
        cat_final = categoria.strip() if categoria.strip() != "" else "Sin Categoría"
        
        nuevo_mov = pd.DataFrame({'Fecha': [fecha], 'Tipo': [tipo], 'Categoría': [cat_final], 'Monto': [monto]})
        st.session_state.movimientos = pd.concat([st.session_state.movimientos, nuevo_mov], ignore_index=True)
        st.success("¡Movimiento registrado con éxito!")

    st.subheader("Historial de Movimientos")
    if not st.session_state.movimientos.empty:
        st.dataframe(st.session_state.movimientos, use_container_width=True)
    else:
        st.info("No hay movimientos registrados todavía.")

# --- APARTADO 2: SALDO DISPONIBLE ---
with tab2:
    st.header("Dinero Disponible")
    if not st.session_state.movimientos.empty:
        df = st.session_state.movimientos
        ingresos = df[df['Tipo'] == "Ingreso ⬆️"]['Monto'].sum()
        egresos = df[df['Tipo'] == "Egreso ⬇️"]['Monto'].sum()
        saldo_total = ingresos - egresos

        col1, col2, col3 = st.columns(3)
        col1.metric("Ingresos Totales", f"${ingresos:,.2f}")
        col2.metric("Egresos Totales", f"${egresos:,.2f}")
        col3.metric("Saldo Líquido", f"${saldo_total:,.2f}", delta=saldo_total)
    else:
        st.metric("Saldo Líquido", "$0.00")
        st.info("Registrá ingresos y egresos para ver tu saldo.")

# --- APARTADO 3: INVERSIONES ---
with tab3:
    st.header("Rendimiento de Inversiones")
    st.write("Registrá el monto total que tenés en inversiones hoy para ver cómo crece con el tiempo.")
    
    with st.form("form_inversiones", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha_inv = st.date_input("Fecha de registro", date.today())
        with col2:
            monto_inv = st.number_input("Monto Total Actual ($)", min_value=0.0, step=1000.0)
        submit_inversion = st.form_submit_button("Actualizar Inversión")

    if submit_inversion and monto_inv > 0:
        nueva_inv = pd.DataFrame({'Fecha': [fecha_inv], 'Monto Actual': [monto_inv]})
        st.session_state.inversiones = pd.concat([st.session_state.inversiones, nueva_inv], ignore_index=True)
        st.success("¡Inversión actualizada!")

    if not st.session_state.inversiones.empty:
        df_inv = st.session_state.inversiones.copy()
        df_inv['Fecha'] = pd.to_datetime(df_inv['Fecha'])
        df_inv = df_inv.set_index('Fecha')
        
        st.subheader("Evolución del Capital")
        st.line_chart(df_inv['Monto Actual'])
        st.dataframe(st.session_state.inversiones, use_container_width=True)
    else:
        st.info("Registrá el estado de tus inversiones para ver el gráfico de rendimiento.")
