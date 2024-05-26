import streamlit as st
from streamlit_option_menu import option_menu
from enviar import send_email
from google_sheets import googleSheets
from google_calendar import googleCalendar
import uuid
import numpy as np
import datetime as dt
import pytz  # Asegúrate de tener instalada esta librería


page_title = "Salon de Belleza"
page_icon = "img/logo.png"
layout = "centered"

horas = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"]
estilistas = ["Estilista Andrea", "Estilista Ivana"]
servicios = ["Limpieza Facial", "Manicura", "Depilación" ]

document = "Salon-de-belleza"
sheets = "reservas"
credentials = st.secrets["google"]["credentials_google"]
idcalendar = "bd0f9cbb546605068b2ae12e4507237c5d09e38078e7bbbcb2931cbce4cbd7ea@group.calendar.google.com"
idcalendar2 = "9afb0e25166fe6f723fd43445757f6a8794c40543bc7959faa2dc27a3850c158@group.calendar.google.com"
timezone = "America/Montevideo"


def agregar_hora_extra(time):
    parsed_time = dt.datetime.strptime(time, "%H:%M").time()
    new_time = (dt.datetime.combine(dt.date.today(), parsed_time) + dt.timedelta(hours=1, minutes=0)).time()
    return new_time.strftime("%H:%M")

def generate_id():
    return str(uuid.uuid4())

st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)

st.image("img/logo.png", width=250)

st.title("Salon de Belleza")
st.text("Calle direccion, N28")

selected = option_menu(menu_title=None, options=["Reservar"],
                       icons=["calendar-plus"], 
                       orientation="horizontal")


if selected == "Reservar":
    st.subheader("Reservar")
    
    c1, c2 = st.columns(2)
    
    nombre = c1.text_input("Tu nombre*", placeholder="Nombre Completo")
    email = c2.text_input("Tu email*", placeholder="Email")
    fecha = c1.date_input("Fecha")
    estilista = c1.selectbox("Estilistas", estilistas)    
    if fecha:
        if estilista == "Estilista Andrea":
            id = idcalendar
        elif estilista == "Estilista Ivana":
            id = idcalendar2
            
        calendar = googleCalendar(credentials, id)
        hours_blocked = calendar.get_events_start_time(str(fecha))
        result_hours = np.setdiff1d(horas, hours_blocked)
    hora = c2.selectbox("Hora", result_hours)
    servicios = c2.selectbox("Servicio", servicios)

    
    enviar = st.button("Reservar")
    
    ##BACKEND
    if enviar:
        with st.spinner("Cargando..."):
            if nombre == "":
                st.warning("El nombre es obligatorio")
            elif email == "":
                st.warning("El email es obligatorio")
            else:
                parsed_time = dt.datetime.strptime(hora, "%H:%M").time()
                start_dt = dt.datetime.combine(fecha, parsed_time)
                end_dt = start_dt + dt.timedelta(hours=1)
                
                # Convertir a la zona horaria local
                local_tz = pytz.timezone(timezone)
                start_dt = local_tz.localize(start_dt)
                end_dt = local_tz.localize(end_dt)
                
                # Formatear a ISO 8601
                start_time = start_dt.isoformat()
                end_time = end_dt.isoformat()
                
                calendar = googleCalendar(credentials, id)
                calendar.create_event(nombre, start_time, end_time, timezone)
                
                # GOOGLE SHEETS
                uid = generate_id()
                data = [[nombre, email, str(fecha), hora, estilista, servicios, uid]]
                gs = googleSheets(credentials, document, sheets)
                range = gs.get_last_row_range()
                gs.write_data(range, data)
                
                send_email(email, nombre, fecha, hora, estilista)
                
                st.success("Nos ha llegado tu reserva!")
