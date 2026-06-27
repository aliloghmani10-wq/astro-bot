import os, io, logging, threading, datetime, pytz
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes,
)
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from astro_engine import (
    to_julian, calc_positions, calc_houses,
    calc_aspects, calc_transit, now_jd,
)
from chart_renderer import draw_circular, draw_diamond, draw_transit

TOKEN = os.environ.get('BOT_TOKEN', '')

app = Flask(__name__)

@app.route('/')
def health():
    return 'Astro Bot is alive!'

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

NAME, DATE, TIME, CITY, CHOOSE = range(5)
store = {}
geo = Nominatim(user_agent='astro_bot_v2', timeout=10)

KB_MAIN = ReplyKeyboardMarkup([
    ['🔮 چارت تولد جدید'],['🔄 ترانزیت لحظه‌ای'],['ℹ️ راهنما'],
], resize_keyboard=True)

KB_TYPE = ReplyKeyboardMarkup([
    ['🌍 تروپیکال','⭐ سایدریال'],
    ['💎 الماسی','🔄 ترانزیت'],
    ['📋 همه چارت‌ها'],
], resize_keyboard=True, one_time_keyboard=True)

async def cmd_start(update, ctx):
    await update.message.reply_text(
        "🌟 *ربات چارت تولد*\n\n"
        "چارت دقیق با Swiss Ephemeris\n\n"
        "🌍 تروپیکال  ⭐ سایدریال\n"
        "💎 الماسی  🔄 ترانزیت\n\n"
        "/new رو بزن شروع کن 👇",
        parse_mode='Markdown', reply_markup=KB_MAIN)
    return ConversationHandler.END

async def conv_start(update, ctx):
    await update.message.reply_text("✏️ اسمت رو بنویس:", reply_markup=ReplyKeyboardRemove())
    return NAME

async def conv_name(update, ctx):
    store[update.effective_user.id] = {'name': update.message.text.strip()}
    await update.message.reply_text(
        "📅 تاریخ تولد میلادی:\n`YYYY/MM/DD`\nمثال: `1995/06/15`",
        parse_mode='Markdown')
    return DATE

async def conv_date(update, ctx):
    uid = update.effective_user.id
    try:
        p = update.message.text.strip().replace('-','/').split('/')
        y,m,d = int(p[0]),int(p[1]),int(p[2])
        if not(1900<=y<=2100 and 1<=m<=12 and 1<=d<=31): raise ValueError
        store[uid].update(year=y,month=m,day=d)
    except:
        await update.message.reply_text("❌ دوباره: `1995/06/15`", parse_mode='Markdown')
        return DATE
    await update.message.reply_text(
        "🕐 ساعت تولد:\n`HH:MM`\nمثال: `14:30`", parse_mode='Markdown')
    return TIME

async def conv_time(update, ctx):
    uid = update.effective_user.id
    try:
        p = update.message.text.strip().split(':')
        h = int(p[0]); m = int(p[1]) if len(p)>1 else 0
        if not(0<=h<=23 and 0<=m<=59): raise ValueError
        store[uid].update(hour=h,minute=m)
    except:
        await update.message.reply_text("❌ دوباره: `14:30`", parse_mode='Markdown')
        return TIME
    await update.message.reply_text(
        "🌐 شهر تولدت (انگلیسی):\nمثال: `Tehran`", parse_mode='Markdown')
    return CITY

async def conv_city(update, ctx):
    uid = update.effective_user.id
    city = update.message.text.strip()
    await update.message.reply_text("🔍 پیدا کردن مختصات...")
    try:
        loc = geo.geocode(city)
        if not loc:
            await update.message.reply_text("❌ پیدا نشد. دوباره بنویس:")
            return CITY
        store[uid].update(lat=loc.latitude, lon=loc.longitude, city=loc.address)
        await update.message.reply_text(
            f"✅ {loc.address}\n📍 {loc.latitude:.4f}, {loc.longitude:.4f}\n\nنوع چارت 👇",
            reply_markup=KB_TYPE)
    except:
        await update.message.reply_text("⚠️ خطا. دوباره بنویس:")
        return CITY
    return CHOOSE

async def conv_choose(update, ctx):
    uid = update.effective_user.id
    choice = update.message.text.strip()
    data = store.get(uid)
    if not data:
        await update.message.reply_text("❌ /new رو بزن.")
        return ConversationHandler.END

    await update.message.reply_text("⏳ در حال محاسبه...", reply_markup=ReplyKeyboardRemove())

    try:
        jd = to_julian(data['year'],data['month'],data['day'],data['hour'],data['minute'])
        lat, lon = data['lat'], data['lon']
        ds = f"{data['year']}/{data['month']:02d}/{data['day']:02d}  {data['hour']:02d}:{data['minute']:02d}  |  {data.get('city','')}"
        charts = []

        if 'تروپیکال' in choice or 'همه' in choice:
            pos=calc_positions(jd,'tropical'); hs=calc_houses(jd,lat,lon); asp=calc_aspects(pos)
            charts.append(('🌍 تروپیکال', draw_circular(data['name'],pos,hs,asp,'tropical',ds), pos))

        if 'سایدریال' in choice or 'همه' in choice:
            pos=calc_positions(jd,'sidereal'); hs=calc_houses(jd,lat,lon); asp=calc_aspects(pos)
            charts.append(('⭐ سایدریال', draw_circular(data['name'],pos,hs,asp,'sidereal',ds), pos))

        if 'الماسی' in choice or 'همه' in choice:
            pos=calc_positions(jd,'sidereal'); hs=calc_houses(jd,lat,lon)
            charts.append(('💎 الماسی', draw_diamond(data['name'],pos,hs,[],ds), pos))

        if 'ترانزیت' in choice or 'همه' in choice:
            bp=calc_positions(jd,'tropical'); hs=calc_houses(jd,lat,lon)
            tp,ta=calc_transit(bp)
            now=datetime.datetime.now(pytz.timezone('Asia/Tehran'))
            charts.append(('🔄 ترانزیت', draw_transit(data['name'],bp,tp,ta,hs,ds+f"\nTransit: {now.strftime('%Y/%m/%d %H:%M')}"), bp))

        for title, img, pos in charts:
            buf = io.BytesIO(); img.save(buf,'PNG',optimize=True); buf.seek(0)
            cap = f"*{title}*\n\n"
            if pos:
                for pn,p in pos.items():
                    cap += f"{p['sym']} {p['fa']}: {p['deg']}°{p['min']}' {p['sign_sym']} {p['sign_fa']}\n"
            await update.message.reply_photo(photo=buf, caption=cap[:1024], parse_mode='Markdown')

        await update.message.reply_text("✅ تموم!\n/new برای چارت جدید", reply_markup=KB_MAIN)
    except Exception as e:
        log.exception("err")
        await update.message.reply_text(f"❌ خطا: {e}", reply_markup=KB_MAIN)
    return ConversationHandler.END

async def cmd_transit(update, ctx):
    await update.message.reply_text("⏳ ...")
    try:
        pos = calc_positions(now_jd(), 'tropical')
        now = datetime.datetime.now(pytz.timezone('Asia/Tehran'))
        txt = f"🔄 *ترانزیت لحظه‌ای*\n{now.strftime('%Y/%m/%d %H:%M')}\n\n"
        for pn,p in pos.items():
            txt += f"{p['sym']} {p['fa']}: {p['deg']}°{p['min']}' {p['sign_sym']} {p['sign_fa']}\n"
        await update.message.reply_text(txt, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

async def cmd_help(update, ctx):
    await update.message.reply_text(
        "/new — چارت تولد\n/transit — ترانزیت\n/help — راهنما",
        reply_markup=KB_MAIN)

async def conv_cancel(update, ctx):
    await update.message.reply_text("❌ لغو", reply_markup=KB_MAIN)
    return ConversationHandler.END

def run_bot():
    application = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[
            CommandHandler('new', conv_start),
            MessageHandler(filters.Regex('^🔮 چارت تولد جدید$'), conv_start),
        ],
        states={
            NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, conv_name)],
            DATE:[MessageHandler(filters.TEXT & ~filters.COMMAND, conv_date)],
            TIME:[MessageHandler(filters.TEXT & ~filters.COMMAND, conv_time)],
            CITY:[MessageHandler(filters.TEXT & ~filters.COMMAND, conv_city)],
            CHOOSE:[MessageHandler(filters.TEXT & ~filters.COMMAND, conv_choose)],
        },
        fallbacks=[CommandHandler('cancel', conv_cancel)],
    )
    application.add_handler(conv)
    application.add_handler(CommandHandler('start', cmd_start))
    application.add_handler(CommandHandler('help', cmd_help))
    application.add_handler(CommandHandler('transit', cmd_transit))
    application.add_handler(MessageHandler(filters.Regex('^🔄 ترانزیت لحظه‌ای$'), cmd_transit))
    application.add_handler(MessageHandler(filters.Regex('^ℹ️ راهنما$'), cmd_help))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
