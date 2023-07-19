import re
import requests
from bs4 import BeautifulSoup
import tweepy
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from tkinter import messagebox
import instaloader
import praw
import threading
import shodan

def show_about():
    about_text = "JackOSINT - Herramienta de Open Source Intelligence (OSINT)\n\n" \
                 "Creada por Christian de López.\n" \
                 "Todos los derechos reservados.\n\n" \
                 "Esta herramienta realiza búsquedas en Google, Twitter, Instagram, Reddit, " \
                 "correos electrónicos, Shodan, Bing y Yandex para obtener información pública.\n" \
                 "Recuerda utilizarla de forma ética y respetar los términos de servicio de las plataformas.\n\n" \
                 "¡Disfruta usando JackOSINT para tus propósitos de OSINT!"

    messagebox.showinfo("Acerca de", about_text)

def show_config():
    config_window = tk.Toplevel(root)
    config_window.title("Configuración de Claves de API")
    config_window.geometry("400x200")

    api_frame = ttk.Labelframe(config_window, text="Claves de API de Twitter y Shodan")
    api_frame.pack(pady=10, padx=10)

    api_key_label = ttk.Label(api_frame, text="API Key de Twitter:")
    api_key_label.grid(row=0, column=0, padx=5, pady=5)
    api_key_entry = ttk.Entry(api_frame, width=30)
    api_key_entry.grid(row=0, column=1, padx=5, pady=5)

    api_secret_label = ttk.Label(api_frame, text="API Secret de Twitter:")
    api_secret_label.grid(row=1, column=0, padx=5, pady=5)
    api_secret_entry = ttk.Entry(api_frame, width=30)
    api_secret_entry.grid(row=1, column=1, padx=5, pady=5)

    shodan_api_key_label = ttk.Label(api_frame, text="API Key de Shodan:")
    shodan_api_key_label.grid(row=2, column=0, padx=5, pady=5)
    shodan_api_key_entry = ttk.Entry(api_frame, width=30)
    shodan_api_key_entry.grid(row=2, column=1, padx=5, pady=5)

    def save_config():
        global TWITTER_API_KEY, TWITTER_API_SECRET, SHODAN_API_KEY
        TWITTER_API_KEY = api_key_entry.get()
        TWITTER_API_SECRET = api_secret_entry.get()
        SHODAN_API_KEY = shodan_api_key_entry.get()
        config_window.destroy()

    save_button = ttk.Button(api_frame, text="Guardar", command=save_config)
    save_button.grid(row=3, column=1, padx=5, pady=10)

def search_google(query, num_results=5):
    url = f"https://www.google.com/search?q={query}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        results = soup.find_all('div', class_='tF2Cxc')
        return [(result.find('h3').text, result.find('a')['href']) for result in results[:num_results]]

def extract_emails_from_text(text):
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return emails

def search_twitter(query, num_results=5, lang="es"):
    if not TWITTER_API_KEY or not TWITTER_API_SECRET:
        messagebox.showwarning("Claves de API no configuradas", "Por favor, configura las claves de API de Twitter antes de realizar búsquedas en Twitter.")
        return []

    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    tweets = tweepy.Cursor(api.search, q=query, lang=lang).items(num_results)
    return [(tweet.user.screen_name, tweet.text, tweet.created_at) for tweet in tweets]

def search_instagram(query, num_results=5):
    loader = instaloader.Instaloader()
    profile = instaloader.Profile.from_username(loader.context, query)

    posts = []
    for post in profile.get_posts():
        if len(posts) >= num_results:
            break
        posts.append((profile.username, post.caption, post.url))

    return posts

def search_reddit(query, num_results=5):
    reddit = praw.Reddit(
        client_id="your_client_id",
        client_secret="your_client_secret",
        user_agent="your_user_agent",
    )

    subreddit = reddit.subreddit("all")
    posts = []
    for post in subreddit.search(query, limit=num_results):
        posts.append((post.author.name, post.title, post.url))

    return posts

def search_emails(query, num_results=5):
    google_results = search_google(query, num_results)
    emails = []

    for title, link in google_results:
        try:
            response = requests.get(link)
            if response.status_code == 200:
                extracted_emails = extract_emails_from_text(response.text)
                emails.extend(extracted_emails)
        except:
            continue

    return list(set(emails))  # Remove duplicates

def search_shodan(query, num_results=5):
    if not SHODAN_API_KEY:
        messagebox.showwarning("API Key de Shodan no configurada", "Por favor, configura la API Key de Shodan antes de realizar búsquedas en Shodan.")
        return []

    api = shodan.Shodan(SHODAN_API_KEY)

    try:
        results = api.search(query, limit=num_results)
        return [(result['ip_str'], result['org'], result['data']) for result in results['matches']]
    except shodan.APIError as e:
        print(e)
        return []

def search_bing(query, num_results=5):
    # Agregar la lógica para buscar en Bing aquí
    pass

def search_yandex(query, num_results=5):
    # Agregar la lógica para buscar en Yandex aquí
    pass

def perform_search(query, num_results, selected_sources):
    results = {}

    if 'Google' in selected_sources:
        google_results = search_google(query, num_results)
        results["Google"] = google_results

    if 'Twitter' in selected_sources:
        twitter_results = search_twitter(query, num_results)
        results["Twitter"] = twitter_results

    if 'Instagram' in selected_sources:
        instagram_results = search_instagram(query, num_results)
        results["Instagram"] = instagram_results

    if 'Reddit' in selected_sources:
        reddit_results = search_reddit(query, num_results)
        results["Reddit"] = reddit_results

    if 'Correos Electrónicos' in selected_sources:
        email_results = search_emails(query, num_results)
        results["Correos Electrónicos"] = [(email,) for email in email_results]

    if 'Shodan' in selected_sources:
        shodan_results = search_shodan(query, num_results)
        results["Shodan"] = shodan_results

    if 'Bing' in selected_sources:
        bing_results = search_bing(query, num_results)
        results["Bing"] = bing_results

    if 'Yandex' in selected_sources:
        yandex_results = search_yandex(query, num_results)
        results["Yandex"] = yandex_results

    root.after(1000, display_results, results)

def clear_results():
    output_text.config(state=tk.NORMAL)
    output_text.delete('1.0', tk.END)
    output_text.config(state=tk.DISABLED)
    status_label.config(text="")
    progress_bar["value"] = 0

def display_results(results):
    result_text = ""
    summary_text = ""

    for source_name, result in results.items():
        result_text += f"\nResultados de {source_name}:\n\n"
        if source_name == "Google":
            for title, link in result:
                result_text += f"Titulo: {title}\nEnlace: {link}\n\n"
        elif source_name == "Twitter":
            for username, text, created_at in result:
                result_text += f"Usuario: {username}\nTexto: {text}\nFecha: {created_at}\n\n"
        elif source_name == "Instagram":
            for username, caption, url in result:
                result_text += f"Usuario: {username}\nDescripción: {caption}\nURL: {url}\n\n"
        elif source_name == "Reddit":
            for author, title, url in result:
                result_text += f"Autor: {author}\nTítulo: {title}\nURL: {url}\n\n"
        elif source_name == "Correos Electrónicos":
            for email in result:
                result_text += f"Correo Electrónico: {email[0]}\n\n"
        elif source_name == "Shodan":
            for ip_str, org, data in result:
                result_text += f"IP: {ip_str}\nOrganización: {org}\nDatos: {data}\n\n"

        # Resumen ejecutivo
        if source_name not in ["Correos Electrónicos", "Shodan"]:
            summary_text += f"{source_name}: {len(result)} resultados\n"

    output_text.config(state=tk.NORMAL)
    output_text.insert(tk.END, result_text)
    output_text.config(state=tk.DISABLED)

    if summary_text:
        output_text.insert(tk.END, "\nResumen Ejecutivo:\n\n")
        output_text.insert(tk.END, summary_text)

    status_label.config(text="Búsqueda completada.")
    progress_bar["value"] = 0
    messagebox.showinfo("Búsqueda completada", "Se han obtenido los resultados de la búsqueda.")

def save_results():
    if output_text.get("1.0", tk.END) == "\nNo se han realizado búsquedas aún.":
        messagebox.showwarning("Sin resultados", "No se han realizado búsquedas aún.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])

    if file_path:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(output_text.get("1.0", tk.END))
        messagebox.showinfo("Guardado exitoso", "Los resultados han sido guardados exitosamente.")

# Variables globales para las claves de API
TWITTER_API_KEY = ""
TWITTER_API_SECRET = ""
SHODAN_API_KEY = ""

# Configuración de la interfaz gráfica
root = tk.Tk()
root.title("JackOSINT - Herramienta de OSINT")
root.geometry("800x600")

# Barra de menú
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Archivo", menu=file_menu)
file_menu.add_command(label="Acerca de", command=show_about)
file_menu.add_separator()
file_menu.add_command(label="Guardar resultados", command=save_results)
file_menu.add_separator()
file_menu.add_command(label="Salir", command=exit_app)

# Sección de configuración
config_frame = ttk.Frame(root, padding="20")
config_frame.pack(fill="both", expand=True)

config_button = ttk.Button(config_frame, text="Configurar Claves de API", command=show_config)
config_button.pack(anchor="e", padx=5, pady=5)

# Sección de búsqueda
search_frame = ttk.Frame(root, padding="20")
search_frame.pack(fill="both", expand=True)

search_query_label = ttk.Label(search_frame, text="Consulta de Búsqueda:")
search_query_label.pack(anchor="w", padx=5, pady=5)
search_query_entry = ttk.Entry(search_frame, width=40)
search_query_entry.pack(anchor="w", padx=5, pady=5)

num_results_label = ttk.Label(search_frame, text="Número de Resultados:")
num_results_label.pack(anchor="w", padx=5, pady=5)
num_results_entry = ttk.Entry(search_frame, width=10)
num_results_entry.insert(tk.END, "5")  # Valor predeterminado de 5 resultados
num_results_entry.pack(anchor="w", padx=5, pady=5)

sources_frame = ttk.Labelframe(search_frame, text="Fuentes de Búsqueda")
sources_frame.pack(anchor="w", padx=5, pady=5)

sources = [tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()]
check_google = ttk.Checkbutton(sources_frame, text="Google", variable=sources[0], onvalue="Google", offvalue="")
check_google.pack(anchor="w", padx=5, pady=2)
check_twitter = ttk.Checkbutton(sources_frame, text="Twitter", variable=sources[1], onvalue="Twitter", offvalue="")
check_twitter.pack(anchor="w", padx=5, pady=2)
check_instagram = ttk.Checkbutton(sources_frame, text="Instagram", variable=sources[2], onvalue="Instagram", offvalue="")
check_instagram.pack(anchor="w", padx=5, pady=2)
check_reddit = ttk.Checkbutton(sources_frame, text="Reddit", variable=sources[3], onvalue="Reddit", offvalue="")
check_reddit.pack(anchor="w", padx=5, pady=2)
check_emails = ttk.Checkbutton(sources_frame, text="Correos Electrónicos", variable=sources[4], onvalue="Correos Electrónicos", offvalue="")
check_emails.pack(anchor="w", padx=5, pady=2)
check_shodan = ttk.Checkbutton(sources_frame, text="Shodan", variable=sources[5], onvalue="Shodan", offvalue="")
check_shodan.pack(anchor="w", padx=5, pady=2)
check_bing = ttk.Checkbutton(sources_frame, text="Bing", variable=sources[6], onvalue="Bing", offvalue="")
check_bing.pack(anchor="w", padx=5, pady=2)
check_yandex = ttk.Checkbutton(sources_frame, text="Yandex", variable=sources[7], onvalue="Yandex", offvalue="")
check_yandex.pack(anchor="w", padx=5, pady=2)

search_button = ttk.Button(search_frame, text="Buscar", command=search_and_display)
search_button.pack(anchor="w", padx=5, pady=10)

# Barra de progreso
progress_bar = ttk.Progressbar(root, mode='determinate', length=400)
progress_bar.pack(pady=10)

# Resultados
result_frame = ttk.Frame(root, padding="20")
result_frame.pack(fill="both", expand=True)

status_label = ttk.Label(result_frame, text="", font=("Helvetica", 12, "bold"))
status_label.pack(anchor="w", padx=5, pady=5)

output_text = scrolledtext.ScrolledText(result_frame, width=80, height=20, state=tk.DISABLED)
output_text.pack(padx=20, pady=10)

# Botón para guardar resultados
save_button = ttk.Button(root, text="Guardar Resultados", command=save_results)
save_button.pack(anchor="e", padx=20, pady=10)

# Estilos personalizados
style = ttk.Style()
style.configure("TLabel", font=("Helvetica", 12))
style.configure("TButton", font=("Helvetica", 12))
style.configure("TCheckbutton", font=("Helvetica", 12))
style.configure("TEntry", font=("Helvetica", 12))

# Ejecutar la aplicación
root.mainloop()
