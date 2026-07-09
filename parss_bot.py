import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- TELEGRAM BOT TOKENİNİZ ---
TELEGRAM_TOKEN = "8691262487:AAGIFozV0iwfROK9LpMewU4CuaETpxmYzpQ"

# --- API SERVİS ŞABLONLARI ---
API_TC      = "https://arastir.vip/api/tc.php?tc="
API_ADSOYAD = "https://arastir.vip/api/adsoyad.php?adi={}&soyadi={}&il={}&ilce={}"
API_ADRES   = "https://arastir.vip/api/adres.php?tc="
API_GSMTC   = "https://arastir.vip/api/gsm_tc.php?gsm="
API_TCGSM   = "https://arastir.vip/api/tcgsm.php?tc="
API_ISYERI  = "https://arastir.vip/api/isyeri.php?tc="
API_SULALE  = "https://arastir.vip/api/sulale.php?tc="

# 🆕 KAPANAN APİ (TEST AMAÇLI EKLENDİ)
API_TAPU    = "https://nowercheck.com/nowerapi/tapu.php?tc="

# --- START MENÜSÜ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rehber = (
        "<b>╔════════════════════════╗</b>\n"
        "<b>       ⚡ PARS SORGU PANEL v1.0 ⚡  </b>\n"
        "<b>╚════════════════════════╝</b>\n\n"
        "<b>🛠 KOMUT LİSTESİ</b>\n"
        " ├─ <code>/tc [no]</code> • TC Sorgula\n"
        " ├─ <code>/adres [tc]</code> • Adres Bilgisi\n"
        " ├─ <code>/sulale [tc]</code> • Sülale Ağacı\n"
        " ├─ <code>/isyeri [tc]</code> • İşyeri Bilgisi\n"
        " ├─ <code>/tcgsm [tc]</code> • TC'den GSM Bul\n"
        " ├─ <code>/gsmtc [gsm]</code> • GSM'den TC Bul\n"
        " ├─ <code>/tapu [tc]</code> • Tapu Bilgisi (Test)\n"
        " └─ <code>/adsoyad [isim] [soyisim] [il] [ilçe]</code>\n\n"
        "<b>👑 YÖNETİM &amp; GELİŞTİRİCİLER</b>\n"
        " ⚡ Kurucu: @parssrogue\n"
        " ⚡ Kurucu: @devamravex1\n\n"
        "<i>Sorgulamak istediğiniz komutu ve parametreyi yazıp gönderin.</i>\n"
        "<b>────────────────────────</b>"
    )
    await update.message.reply_text(rehber, parse_mode="HTML")

# --- VERİLERİ ŞEKİLLİ VE TOPLU YAZDIRAN MOTOR ---
def sekilli_tasarim_hazirla(data_obj, baslik, index=None):
    tasarim = ""
    if index:
        tasarim += f"<b>⭐ KAYIT #{index}</b>\n"
    else:
        tasarim += f"<b>📊 {baslik.upper()} SONUCU</b>\n"
        
    tasarim += "<b>╭───────────────────────</b>\n"
    
    if isinstance(data_obj, dict):
        for key, value in data_obj.items():
            temiz_val = value if value and str(value).strip() not in ["", "-"] else "Bulunamadı"
            tasarim += f"<b>│ ➜ {key.upper()}:</b> <code>{temiz_val}</code>\n"
    else:
        tasarim += f"<b>│ ➜ BİLGİ:</b> <code>{data_obj}</code>\n"
        
    tasarim += "<b>╰───────────────────────</b>\n"
    return tasarim

# --- TEKLİ SORGULAR İÇİN YARDIMCI FONKSİYON ---
async def tekli_sorgu_motoru(update: Update, context: ContextTypes.DEFAULT_TYPE, api_url, komut_adi, baslik):
    if not context.args:
        await update.message.reply_text(f"⚠️ <b>Kullanım Hatası!</b>\nLütfen parametre girin. Örn: <code>/{komut_adi} 11111111111</code>", parse_mode="HTML")
        return
    
    girdi = context.args[0]
    bekleme_mesaji = await update.message.reply_text("⚡ <b>Veritabanı sorgulanıyor, lütfen bekleyin...</b>", parse_mode="HTML")
    
    try:
        # Timeout süresini 5 saniyeye düşürdüm ki kapalı sitelerde bot dakikalarca donup kalmasın
        response = requests.get(f"{api_url}{girdi}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                if not data:
                    await bekleme_mesaji.edit_text("❌ <b>Sistemde eşleşen herhangi bir kayıt bulunamadı.</b>", parse_mode="HTML")
                    return
                
                tasarim_toplam = f"<b>👥 TOPLAM {len(data)} KAYIT BULUNDU ({baslik.upper()})</b>\n\n"
                for index, eleman in enumerate(data, start=1):
                    tasarim_toplam += sekilli_tasarim_hazirla(eleman, baslik, index=index) + "\n"
                
                await bekleme_mesaji.edit_text(tasarim_toplam, parse_mode="HTML")
            
            elif isinstance(data, dict):
                cikti = sekilli_tasarim_hazirla(data, baslik)
                await bekleme_mesaji.edit_text(cikti, parse_mode="HTML")
        else:
            await bekleme_mesaji.edit_text(f"❌ <b>API hatası döndü. Durum Kodu: {response.status_code}</b>", parse_mode="HTML")
    except requests.exceptions.ConnectionError:
        await bekleme_mesaji.edit_text("❌ <b>Bağlantı Hatası:</b> API sunucusu aktif değil, domain süresi bitmiş veya site tamamen kapatılmış.", parse_mode="HTML")
    except Exception as e:
        await bekleme_mesaji.edit_text(f"❌ <b>Bir hata oluştu:</b> <code>{str(e)}</code>", parse_mode="HTML")

# --- KOMUT FONKSİYONLARI ---
async def tc_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tekli_sorgu_motoru(update, context, API_TC, "tc", "TC")

async def adres_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tekli_sorgu_motoru(update, context, API_ADRES, "adres", "Adres")

async def sulale_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tekli_sorgu_motoru(update, context, API_SULALE, "sulale", "Sülale")

async def tcgsm_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tekli_sorgu_motoru(update, context, API_TCGSM, "tcgsm", "TC -> GSM")

async def gsmtc_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tekli_sorgu_motoru(update, context, API_GSMTC, "gsmtc", "GSM -> TC")

async def isyeri_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tekli_sorgu_motoru(update, context, API_ISYERI, "isyeri", "İşyeri")

# 🆕 TAPU SORGUSU (TEST FONKSİYONU)
async def tapu_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await tekli_sorgu_motoru(update, context, API_TAPU, "tapu", "Tapu")

async def adsoyad_sorgu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ <b>Kullanım Hatası!</b>\nÖrn: <code>/adsoyad Ahmet Yılmaz İstanbul</code>", parse_mode="HTML")
        return
    
    isim = context.args[0]
    soyisim = context.args[1]
    il = context.args[2] if len(context.args) > 2 else ""
    ilce = context.args[3] if len(context.args) > 3 else ""
    
    bekleme_mesaji = await update.message.reply_text("⚡ <b>Ad Soyad veritabanı taranıyor...</b>", parse_mode="HTML")
    url = API_ADSOYAD.format(isim, soyisim, il, ilce)
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            tasarim_toplam = "<b>👤 AD SOYAD SORGULAMA SONUÇLARI</b>\n\n"
            
            if isinstance(data, list):
                if not data:
                    await bekleme_mesaji.edit_text("❌ <b>Bu isimde bir kayıt bulunamadı.</b>", parse_mode="HTML")
                    return
                for index, kisi in enumerate(data, start=1):
                    tasarim_toplam += sekilli_tasarim_hazirla(kisi, "Ad Soyad", index=index) + "\n"
            else:
                tasarim_toplam += sekilli_tasarim_hazirla(data, "Ad Soyad")
                
            await bekleme_mesaji.edit_text(tasarim_toplam, parse_mode="HTML")
        else:
            await bekleme_mesaji.edit_text("❌ <b>API sunucusundan geçersiz yanıt alındı.</b>", parse_mode="HTML")
    except Exception as e:
        await bekleme_mesaji.edit_text(f"❌ <b>Bir hata oluştu:</b> <code>{str(e)}</code>", parse_mode="HTML")

# --- BOT BAŞLATMA ---
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tc", tc_sorgu))
    app.add_handler(CommandHandler("adres", adres_sorgu))
    app.add_handler(CommandHandler("sulale", sulale_sorgu))
    app.add_handler(CommandHandler("tcgsm", tcgsm_sorgu))
    app.add_handler(CommandHandler("gsmtc", gsmtc_sorgu))
    app.add_handler(CommandHandler("isyeri", isyeri_sorgu))
    app.add_handler(CommandHandler("adsoyad", adsoyad_sorgu))
    
    # 🆕 Tapu komutunun bota eklenmesi
    app.add_handler(CommandHandler("tapu", tapu_sorgu))
    
    print("Bot aktif, yeni test sürümü yüklendi!")
    app.run_polling()

if __name__ == "__main__":
    main()

