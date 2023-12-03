import pandas as pd
from openpyxl import load_workbook
import re


# Carga el archivo Excel
def cargar_archivo(excel_path):
    df = pd.read_excel(excel_path)
    return df


# Buscar una asignatura
def buscar_asignatura(df, identificador):
    identificador = str(identificador).strip()

    df["NRC"] = df["NRC"].apply(lambda x: str(x).strip())

    asignatura_por_nrc = df[df["NRC"] == identificador]

    if asignatura_por_nrc.empty:
        asignatura_por_clave = df[df["Clave"] == identificador]
        if not asignatura_por_clave.empty:
            return asignatura_por_clave
    else:
        return asignatura_por_nrc

    print("La asignatura no existe.")
    return None


# Agregar una asignatura
def agregar_asignatura(df, datos_asignatura):
    nueva_asignatura_df = pd.DataFrame([datos_asignatura])
    nueva_asignatura_df = nueva_asignatura_df.reindex(columns=df.columns)
    df_actualizado = pd.concat([df, nueva_asignatura_df], ignore_index=True)
    return df_actualizado


# Eliminar una asignatura
def eliminar_asignatura(df, clave_asignatura):
    df = df[df["Clave"] != clave_asignatura]
    return df


# Modificar una asignatura
def modificar_asignatura(df, clave_asignatura, cambios):
    index = df.index[df["Clave"] == clave_asignatura].tolist()
    if index:
        idx = index[0]
        for campo, nuevo_valor in cambios.items():
            valor_anterior = df.at[idx, campo]
            df.at[idx, campo] = nuevo_valor
            df.at[
                idx, "Comentario"
            ] = f"Actualizado {campo}: {valor_anterior} -> {nuevo_valor}"
    else:
        print("La asignatura no existe.")
    return df


# Generar horario para el alumno
def generar_horario(df, nrcs):
    df['NRC'] = df['NRC'].apply(lambda x: str(x).zfill(5))  # Asegura un formato de 5 dígitos con ceros a la izquierda si es necesario
    nrcs = [str(nrc).zfill(5) for nrc in nrcs]
    horario = df[df['NRC'].isin(nrcs)]

    return horario


# Verificar conflictos
def verificar_conflictos(horario):
    conflictos = []
    for _, asignatura_i in horario.iterrows():
        for _, asignatura_j in horario.iterrows():
            if asignatura_i["NRC"] != asignatura_j["NRC"]:
                if asignatura_i["Dias"] == asignatura_j["Dias"]:
                    rango_i = set(
                        range(
                            int(asignatura_i["Hora"][:2]), int(asignatura_i["Hora"][3:])
                        )
                    )
                    rango_j = set(
                        range(
                            int(asignatura_j["Hora"][:2]), int(asignatura_j["Hora"][3:])
                        )
                    )
                    if rango_i & rango_j:
                        conflicto = f"Conflicto entre NRC {asignatura_i['NRC']} y NRC {asignatura_j['NRC']} a las {asignatura_i['Dias']}"
                        if conflicto not in conflictos:
                            conflictos.append(conflicto)
    return conflictos


# Guardar los cambios en el archivo Excel
def guardar_archivo(df, excel_path):
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    print(f"Archivo guardado con éxito en: {excel_path}")


# Encuentra materias cruzadas
def materias_cruzadas(df, clave_asignatura, horario_nuevo):
    materias = df[
        (df["Dias"] == horario_nuevo["Dias"]) & (df["Hora"] == horario_nuevo["Hora"])
    ]
    cruzadas = materias[materias["Clave"] != clave_asignatura]
    return cruzadas


# Actualizar materias cruzadas
def actualizar_materias_cruzadas(df, clave_asignatura, horario_nuevo):
    cruzadas = materias_cruzadas(df, clave_asignatura, horario_nuevo)
    if not cruzadas.empty:
        df.at[df["Clave"] == clave_asignatura, "Listas_cruzadas"] = ", ".join(
            cruzadas["Clave"].astype(str)
        )
    return df


# Encontrar salón disponible
def encontrar_salon_disponible(df, horario_nuevo):
    salones_ocupados = df[
        (df["Dias"] == horario_nuevo["Dias"]) & (df["Hora"] == horario_nuevo["Hora"])
    ]["Salon"].unique()
    todos_los_salones = df["Salon"].unique().tolist()  # Lista completa de salones
    salones_disponibles = [
        salon for salon in todos_los_salones if salon not in salones_ocupados
    ]
    if salones_disponibles:
        return salones_disponibles[0]  # Retorna el primer salón disponible
    else:
        return None
