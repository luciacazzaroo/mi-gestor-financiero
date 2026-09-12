import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client

st.set_page_config(page_title="Gestor Financiero", page_icon="💰", layout="centered")

# --- CONEXIÓN A SUPABASE ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- CONTROL DE SESIÓN ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- PANTALLA DE LOGIN / REGISTRO ---
if st.session_state.user is None:
    st.title("💰 Gestor Financiero")
    st.subheader("Iniciá sesión o registrate para guardar tus datos de forma segura")

    tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Crear Cuenta"])

    with tab_login:
        with st.form("form_login"):
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            submit_login = st.form_submit_button("Entrar")

            if submit_login:
                try:
                    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = response.user
                    st.success("¡Bienvenido/a!")
                    st.rerun()
                except Exception as e:
                    st.error("Error al iniciar sesión: Usuario o contraseña incorrectos.")

    with tab_registro:
        with st.form("form_registro"):
            new_email = st.text_input("Correo electrónico para registro")
            new_password = st.text_input("Contraseña nueva (min 6 caracteres)", type="password")
            submit_registro = st.form_submit_button("Crear Cuenta")

            if submit_registro:
                try:
                    response = supabase.auth.sign_up({"email": new_email, "password": new_password})
                    st.success("Cuenta creada con éxito. Ya podés iniciar sesión en la otra pestaña.")
                except Exception as e:
                    st.error(f"Error al registrar: {e}")

else:
    # --- USUARIO AUTENTICADO ---
    user = st.session_state.user
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.title("💰 Mi Gestor Financiero")
        st.caption(f"Sesión iniciada como: **{user.email}**")
    with col_head2:
        if st.button("Cerrar Sesión"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["📝 Movimientos", "💵 Saldo Disponible", "📈 Inversiones"])

    # --- TAB 1: MOVIMIENTOS ---
    with tab1:
        st.header("Ingresar Nuevo Movimiento")
        with st.form("form_movimientos", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                tipo = st.radio("Tipo de movimiento", ["Ingreso ⬆️", "Egreso ⬇️"])
                monto = st.number_input("Monto ($)", min_value=0.0, step=1000.0)
            with col2:
                categoria = st.text_input("Categoría", placeholder="Ej: Supermercado, Alquiler...")
                fecha_mov = st.date_input("Fecha", date.today())
            submit_mov = st.form_submit_button("Guardar en la Base de Datos")

        if submit_mov and monto > 0:
            cat_final = categoria.strip() if categoria.strip() != "" else "Sin Categoría"
            data = {
                "user_id": user.id,
                "fecha": str(fecha_mov),
                "tipo": tipo,
                "categoria": cat_final,
                "monto": float(monto)
            }
            supabase.table("movimientos").insert(data).execute()
            st.success("¡Movimiento guardado permanentemente!")

        st.subheader("Historial Guardado")
        res_mov = supabase.table("movimientos").select("*").eq("user_id", user.id).execute()
        if res_mov.data:
            df_mov = pd.DataFrame(res_mov.data)[['fecha', 'tipo', 'categoria', 'monto']]
            df_mov.columns = ['Fecha', 'Tipo', 'Categoría', 'Monto']
            st.dataframe(df_mov, use_container_width=True)
        else:
            st.info("No hay movimientos guardados aún.")

    # --- TAB 2: SALDO DISPONIBLE ---
    with tab2:
        st.header("Dinero Disponible")
        res_mov = supabase.table("movimientos").select("*").eq("user_id", user.id).execute()
        if res_mov.data:
            df = pd.DataFrame(res_mov.data)
            ingresos = df[df['tipo'] == "Ingreso ⬆️"]['monto'].sum()
            egresos = df[df['tipo'] == "Egreso ⬇️"]['monto'].sum()
            saldo_total = ingresos - egresos

            col1, col2, col3 = st.columns(3)
            col1.metric("Ingresos Totales", f"${ingresos:,.2f}")
            col2.metric("Egresos Totales", f"${egresos:,.2f}")
            col3.metric("Saldo Líquido", f"${saldo_total:,.2f}", delta=float(saldo_total))
        else:
            st.metric("Saldo Líquido", "$0.00")
            st.info("Registrá movimientos para calcular tu saldo.")

    # --- TAB 3: INVERSIONES ---
    with tab3:
        st.header("Rendimiento de Inversiones")
        with st.form("form_inv", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                fecha_inv = st.date_input("Fecha de registro", date.today())
            with col2:
                monto_inv = st.number_input("Monto Total Actual ($)", min_value=0.0, step=1000.0)
            submit_inv = st.form_submit_button("Guardar Inversión")

        if submit_inv and monto_inv > 0:
            data_inv = {
                "user_id": user.id,
                "fecha": str(fecha_inv),
                "monto_actual": float(monto_inv)
            }
            supabase.table("inversiones").insert(data_inv).execute()
            st.success("¡Inversión actualizada en la base de datos!")

        res_inv = supabase.table("inversiones").select("*").eq("user_id", user.id).order("fecha").execute()
        if res_inv.data:
            df_inv = pd.DataFrame(res_inv.data)[['fecha', 'monto_actual']]
            df_inv.columns = ['Fecha', 'Monto Actual']
            df_chart = df_inv.copy()
            df_chart['Fecha'] = pd.to_datetime(df_chart['Fecha'])
            df_chart = df_chart.set_index('Fecha')
            
            st.subheader("Evolución del Capital")
            st.line_chart(df_chart['Monto Actual'])
            st.dataframe(df_inv, use_container_width=True)
        else:
            st.info("No hay registros de inversiones en la base de datos.")
