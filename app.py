from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
import os
import requests
import re
import logging
from dotenv import load_dotenv
import yt_dlp

# Configuration
logging.getLogger().setLevel(logging.CRITICAL)
load_dotenv()

token = os.getenv("TOKEN")
BOT_USERNAME = '@LinkLift_Bot'
CREATOR_HASHTAG = "@illusivehacks"

# Platform detection patterns
PLATFORM_PATTERNS = {
    'tiktok': r'(https?://(vm\.|www\.)?tiktok\.com/[^\s]+)',
    'instagram': r'(https?://(www\.)?instagram\.com/(p|reel)/[^\s]+)',
    'youtube': r'(https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[^\s]+)',
    'twitter': r'(https?://(twitter\.com|x\.com)/[^\s]+/status/[^\s]+)'
}

# Platform emojis for aesthetic display
PLATFORM_EMOJIS = {
    'instagram': '📸',
    'tiktok': '🎵', 
    'youtube': '📺',
    'twitter': '🐦'
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = f"""
✨ *Welcome to LinkLift - Your Social Downloader!* ✨

⚡ *Lightning Fast Downloads From:*
📸 Instagram Reels/Posts
🎵 TikTok Videos  
📺 YouTube Videos/Shorts
🐦 Twitter/X Videos

💫 *How to use:*
Simply send me a link from any supported platform and I'll handle the rest!

*Powered by* {CREATOR_HASHTAG}
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = f"""
🆘 *LinkLift Help Guide* 🆘

*Supported Platforms:*
• *Instagram*: Reels, Posts
• *TikTok*: All video formats
• *YouTube*: Videos, Shorts
• *Twitter/X*: Video tweets

*How to Download:*
1. Copy video link
2. Paste here
3. Get your download! ✨

*Example Links:*
`https://www.instagram.com/reel/xxx/`
`https://www.tiktok.com/@user/video/xxx`
`https://youtube.com/shorts/xxx`
`https://twitter.com/user/status/xxx`

{CREATOR_HASHTAG} 💻
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is custom command')

def detect_platform(url: str) -> str:
    """Detect which platform the URL belongs to"""
    for platform, pattern in PLATFORM_PATTERNS.items():
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    return None

async def download_video(url: str, platform: str):
    """Universal video downloader using yt-dlp"""
    try:
        print(f"🚀 Processing {platform} URL: {url}")
        
        ydl_opts = {
            'format': 'best[height<=720][ext=mp4]/best[ext=mp4]/best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info['url']
            title = info.get('title', f'{platform.title()} Video')
            uploader = info.get('uploader', 'Unknown')
            duration = info.get('duration', 0)
            
            print(f"✅ {platform} Video URL found: {video_url}")
            
            # Download video to memory
            response = requests.get(video_url, stream=True)
            if response.status_code == 200:
                video_stream = BytesIO()
                for chunk in response.iter_content(chunk_size=8192):
                    video_stream.write(chunk)
                video_stream.seek(0)
                
                caption = f"{title}"
                if uploader and uploader != 'Unknown':
                    caption += f" - @{uploader}"
                
                return video_stream, None, None, caption, video_url
            else:
                print(f"❌ Failed to download {platform} video. Status: {response.status_code}")
                return None
                
    except Exception as e:
        print(f'❌ {platform} download error: {str(e)}')
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    user = update.message.from_user

    print(f'👤 User ({user.first_name}) in {message_type}: "{text}"')
    
    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
        else:
            return
    elif message_type == 'private':
        # Detect platform
        platform = detect_platform(text)
        
        if not platform:
            await update.message.reply_text(
                f"❌ *Unsupported Link* ❌\n\n"
                f"I support: 📸 Instagram • 🎵 TikTok • 📺 YouTube • 🐦 Twitter\n\n"
                f"Send a valid link from any of these platforms! ✨\n\n"
                f"{CREATOR_HASHTAG}",
                parse_mode='Markdown'
            )
            return

        platform_emoji = PLATFORM_EMOJIS.get(platform, '📹')
        processing_message = await update.message.reply_text(
            f"⚡ *{platform_emoji} Processing {platform.title()}...*\n\n"
            f"🚀 Downloading at lightning speed...\n"
            f"📦 Optimizing for fast delivery...\n\n"
            f"{CREATOR_HASHTAG}",
            parse_mode='Markdown'
        )

        try:
            result = await download_video(text, platform)

            if result:
                video = result[0]
                video_hq = result[1] if result[1] else video
                music = result[2]
                caption = result[3]
                link = result[4]
                
                # Create caption text
                caption_text = f"✨ *{platform.title()} Download Complete!* 🎉\n\n"
                if caption:
                    caption_text += f"📝 *Title:* {caption}\n"
                if music:
                    caption_text += f"🎵 *Sound:* {music}\n"
                caption_text += f"🔗 *Direct Link:* {link}\n\n"
                caption_text += f"💫 *Powered by* {CREATOR_HASHTAG}\n"
                caption_text += f"🎊 *Enjoy your content!*"
                
                # Fallback text for large files
                fallback_text = f"📦 *Video Too Large - Link Provided* ⚡\n\n{caption_text}"

                try:
                    await update.message.reply_video(
                        video=InputFile(video_hq), 
                        caption=caption_text,
                        parse_mode='Markdown'
                    )
                    await context.bot.edit_message_text(
                        chat_id=update.message.chat_id,
                        message_id=processing_message.message_id,
                        text=f"✅ *{platform.title()} Download Successful!* 🎉\n\n"
                             f"⚡ Lightning fast service!\n\n"
                             f"{CREATOR_HASHTAG}",
                        parse_mode='Markdown'
                    )
                    
                except Exception as e:
                    if "Request Entity Too Large" in str(e) or "413" in str(e):
                        print("📦 Video is too large, sending link instead")
                        await context.bot.edit_message_text(
                            chat_id=update.message.chat_id,
                            message_id=processing_message.message_id,
                            text=fallback_text,
                            parse_mode='Markdown'
                        )
                    else:
                        raise e

            else:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=processing_message.message_id,
                    text=f"❌ *Download Failed* 😔\n\n"
                         f"Sorry {user.first_name}! Couldn't download from {platform}.\n"
                         f"Please try a different link.\n\n"
                         f"{CREATOR_HASHTAG}",
                    parse_mode='Markdown'
                )

        except Exception as e:
            print(f'💥 Error in handle_message: {str(e)}')
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=processing_message.message_id,
                text=f"⚡ *Temporary Error* ⚡\n\n"
                     f"Please try again with a different link!\n\n"
                     f"Error: {str(e)[:100]}...\n\n"
                     f"{CREATOR_HASHTAG}",
                parse_mode='Markdown'
            )

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'🚨 Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('🚀 Starting LinkLift Bot...')
    print('📸 Supporting: Instagram, TikTok, YouTube, Twitter')
    print(f'💫 Creator: {CREATOR_HASHTAG}')
    
    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('🔍 Polling...')
    app.run_polling(poll_interval=3)
