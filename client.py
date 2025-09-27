# client.py
# Cliente básico que interactúa con la API usando autenticación básica

import requests, base64

BASE = "http://127.0.0.1:5000"

def basic_auth_header(usuario, contraseña):
    creds = f"{usuario}:{contraseña}"
    encoded = base64.b64encode(creds.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

def registrar_usuario():
    usuario = input("Usuario nuevo: ").strip()
    contraseña = input("Contraseña: ").strip()
    r = requests.post(f"{BASE}/registro", json={"usuario": usuario, "contraseña": contraseña})
    print(r.status_code, r.json())

def login():
    usuario = input("Usuario: ").strip()
    contraseña = input("Contraseña: ").strip()
    headers = basic_auth_header(usuario, contraseña)
    r = requests.get(f"{BASE}/login", headers=headers)
    print(r.status_code, r.json())

def ver_tareas():
    usuario = input("Usuario: ").strip()
    contraseña = input("Contraseña: ").strip()
    headers = basic_auth_header(usuario, contraseña)
    r = requests.get(f"{BASE}/tareas", headers=headers)
    if r.status_code == 200:
        print("Contenido HTML recibido:")
        print(r.text)
    else:
        print(r.status_code, r.json())

def main():
    while True:
        print("\nOpciones: [1] Registro [2] Login [3] Ver tareas [4] Salir")
        opt = input("> ").strip()
        if opt == "1":
            registrar_usuario()
        elif opt == "2":
            login()
        elif opt == "3":
            ver_tareas()
        elif opt == "4":
            print("Chau!")
            break
        else:
            print("Opción inválida")

if __name__ == "__main__":
    main()