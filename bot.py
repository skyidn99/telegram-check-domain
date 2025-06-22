import telebot
import requests
import threading
import time
import os

# --- Konfigurasi Awal ---
# Ambil token bot dan chat id dari environment variables
TOKEN = os.environ.get('TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# Inisialisasi bot
bot = telebot.TeleBot(TOKEN)

# Nama file yang berisi daftar domain (sesuai repositori)
DOMAIN_FILE = 'domains.txt'

# --- FUNGSI BARU: Untuk memvalidasi input domain ---
def is_valid_domain(domain):
    """Fungsi sederhana untuk memeriksa apakah input terlihat seperti domain"""
    if '.' in domain and ' ' not in domain and len(domain) > 3:
        return True
    return False

# --- BAGIAN BARU: Perintah /add ---
@bot.message_handler(commands=['add'])
def add_domain(message):
    # Cek apakah perintah dijalankan di chat yang diizinkan
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "Anda tidak diizinkan menggunakan perintah ini di chat ini.")
        return

    try:
        # Ambil domain dari pesan, contoh: /add domain.com
        domain_to_add = message.text.split()[1].strip().lower()

        if not is_valid_domain(domain_to_add):
            bot.reply_to(message, "Format domain tidak valid. Pastikan tidak ada spasi dan mengandung titik (.).")
            return

    except IndexError:
        # Jika pengguna hanya mengetik /add tanpa domain
        bot.reply_to(message, "Penggunaan salah. Contoh: `/add contohdomain.com`", parse_mode="Markdown")
        return

    # Pastikan file domains.txt ada
    if not os.path.exists(DOMAIN_FILE):
        with open(DOMAIN_FILE, 'w') as f:
            pass # Buat file kosong jika belum ada

    # Baca domain yang sudah ada untuk menghindari duplikat
    with open(DOMAIN_FILE, 'r') as f:
        existing_domains = [line.strip().lower() for line in f.readlines()]

    if domain_to_add in existing_domains:
        bot.reply_to(message, f"Domain `{domain_to_add}` sudah ada dalam daftar.", parse_mode="Markdown")
        return

    # Tambahkan domain baru ke file
    with open(DOMAIN_FILE, 'a') as f:
        f.write(f"{domain_to_add}\n")

    bot.reply_to(message, f"Domain `{domain_to_add}` berhasil ditambahkan ke daftar pantau.", parse_mode="Markdown")

# --- BAGIAN BARU: Perintah /delete ---
@bot.message_handler(commands=['delete'])
def delete_domain(message):
    # Cek apakah perintah dijalankan di chat yang diizinkan
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "Anda tidak diizinkan menggunakan perintah ini di chat ini.")
        return

    try:
        domain_to_delete = message.text.split()[1].strip().lower()
    except IndexError:
        bot.reply_to(message, "Penggunaan salah. Contoh: `/delete contohdomain.com`", parse_mode="Markdown")
        return

    if not os.path.exists(DOMAIN_FILE):
        bot.reply_to(message, f"File `{DOMAIN_FILE}` tidak ditemukan. Tidak ada domain untuk dihapus.", parse_mode="Markdown")
        return

    # Baca semua domain dari file
    with open(DOMAIN_FILE, 'r') as f:
        lines = f.readlines()

    # Buat list baru tanpa domain yang ingin dihapus
    new_lines = []
    domain_found = False
    for line in lines:
        if line.strip().lower() != domain_to_delete:
            new_lines.append(line)
        else:
            domain_found = True

    if not domain_found:
        bot.reply_to(message, f"Domain `{domain_to_delete}` tidak ditemukan dalam daftar.", parse_mode="Markdown")
        return

    # Tulis kembali ke file dengan daftar domain yang sudah diperbarui
    with open(DOMAIN_FILE, 'w') as f:
        f.writelines(new_lines)

    bot.reply_to(message, f"Domain `{domain_to_delete}` berhasil dihapus dari daftar pantau.", parse_mode="Markdown")


# --- Fungsi cek domain (Sudah disesuaikan) ---
def cek_domain():
    if not os.path.exists(DOMAIN_FILE):
        return f"File `{DOMAIN_FILE}` tidak ditemukan. Tambahkan domain dengan perintah `/add`."

    with open(DOMAIN_FILE, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]

    if not domains:
        return "Daftar domain kosong. Tambahkan domain dengan perintah `/add`."

    status_report = "<b>Domain Status Report</b>\n\n"
    for domain in domains:
        try:
            response = requests.get(f'https://isthisblocked.com/api/check?host={domain}')
            data = response.json()
            if data.get('blocked'):
                status_report += f"<a href='http://{domain}'>{domain}</a>: 🔴 Blocked\n"
            else:
                status_report += f"<a href='http://{domain}'>{domain}</a>: 🟢 Not Blocked\n"
        except requests.RequestException as e:
            status_report += f"<a href='http://{domain}'>{domain}</a>: ⚠️ Error checking ({e})\n"
    return status_report

# --- Fungsi kirim pesan dan loop (Tidak ada perubahan) ---
def kirim_pesan_cek_domain():
    pesan = cek_domain()
    if pesan:
        try:
            bot.send_message(CHAT_ID, pesan, parse_mode='HTML', disable_web_page_preview=True)
        except Exception as e:
            print(f"Gagal mengirim pesan: {e}")

def loop_cek():
    while True:
        kirim_pesan_cek_domain()
        time.sleep(1800) # Jeda 30 menit

# --- Perintah /start (Pesan pembuka diperbarui) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot aktif! Pengecekan domain berjalan setiap 30 menit.\n\nGunakan perintah:\n`/add domain.com` untuk menambah domain.\n`/delete domain.com` untuk menghapus domain.")

# --- Menjalankan bot (Tidak ada perubahan) ---
if __name__ == "__main__":
    print("Bot sedang berjalan...")
    thread = threading.Thread(target=loop_cek)
    thread.daemon = True
    thread.start()
    bot.polling(none_stop=True)
