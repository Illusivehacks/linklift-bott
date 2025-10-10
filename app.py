from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
import os
import requests
import re
import logging
from douyin_tiktok_scraper.scraper import Scraper
from dotenv import load_dotenv
import instaloader
import yt_dlp
import snscrape.modules.twitter as sntwitter

# Configuration
logging.getLogger().setLevel(logging.CRITICAL)
load_dotenv()

# Initialize scrapers
tiktok_api = Scraper()
instagram_loader = instaloader.Instaloader()

token = os.getenv("TOKEN")
BOT_USERNAME = '@Linklift_bot'
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

async def hybrid_parsing_tiktok(url: str):
    """TikTok/Douyin scraper - Your original function enhanced"""
    try:
        result = await tiktok_api.hybrid_parsing(url)

        video = result["video_data"]["nwm_video_url_HQ"]
        video_hq = result["video_data"]["nwm_video_url_HQ"]
        music = result["music"]["play_url"]["uri"]
        caption = result["desc"]

        print("🎵 TikTok Video URL:", video)
        print("🎵 TikTok Video_HQ URL:", video_hq)
        print("🎵 TikTok Play URL:", music)
        print("🎵 TikTok Caption:", caption)
        
        response_video = requests.get(video)
        response_video_hq = requests.get(video_hq)

        if response_video.status_code == 200:
            video_stream = BytesIO(response_video.content)
        else:
            print(f"Failed to download TikTok MP4. Status code: {response_video.status_code}")

        if response_video_hq.status_code == 200:
            video_stream_hq = BytesIO(response_video_hq.content)
        else:
            print(f"Failed to download TikTok MP4. Status code: {response_video_hq.status_code}")
        
    except Exception as e:
        print(f'❌ TikTok error occurred: {str(e)}')
        return None

    return video_stream, video_stream_hq, music, caption, video_hq

async def download_instagram(url: str):
    """Instagram Reels/Posts downloader"""
    try:
        print("📸 Processing Instagram URL...")
        
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info['url']
            title = info.get('title', 'Instagram Video')
            thumbnail = info.get('thumbnail', None)
            
            print(f"📸 Instagram Video URL: {video_url}")
            
            response = requests.get(video_url)
            if response.status_code == 200:
                video_stream = BytesIO(response.content)
                return video_stream, None, None, title, video_url
            else:
                print(f"❌ Failed to download Instagram video. Status: {response.status_code}")
                return None
                
    except Exception as e:
        print(f'❌ Instagram error occurred: {str(e)}')
        return None

async def download_youtube(url: str):
    """YouTube Videos/Shorts downloader"""
    try:
        print("📺 Processing YouTube URL...")
        
        ydl_opts = {
            'format': 'best[height<=720][ext=mp4]',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info['url']
            title = info.get('title', 'YouTube Video')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')
            
            print(f"📺 YouTube Video URL: {video_url}")
            
            response = requests.get(video_url)
            if response.status_code == 200:
                video_stream = BytesIO(response.content)
                return video_stream, None, None, f"{title} - {uploader}", video_url
            else:
                print(f"❌ Failed to download YouTube video. Status: {response.status_code}")
                return None
                
    except Exception as e:
        print(f'❌ YouTube error occurred: {str(e)}')
        return None

async def download_twitter(url: str):
    """Twitter/X Video downloader"""
    try:
        print("🐦 Processing Twitter URL...")
        
        # Extract tweet ID from URL
        tweet_id_match = re.search(r'/status/(\d+)', url)
        if not tweet_id_match:
            return None
            
        tweet_id = tweet_id_match.group(1)
        
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info['url']
            title = info.get('title', 'Twitter Video')
            uploader = info.get('uploader', 'Unknown')
            
            print(f"🐦 Twitter Video URL: {video_url}")
            
            response = requests.get(video_url)
            if response.status_code == 200:
                video_stream = BytesIO(response.content)
                return video_stream, None, None, f"{title} - @{uploader}", video_url
            else:
                print(f"❌ Failed to download Twitter video. Status: {response.status_code}")
                return None
                
    except Exception as e:
        print(f'❌ Twitter error occurred: {str(e)}')
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
            f"📦 Optimizing for fast delivery...\n"
            f"🎯 Almost ready!\n\n"
            f"{CREATOR_HASHTAG}",
            parse_mode='Markdown'
        )

        try:
            # Route to appropriate scraper
            if platform == 'tiktok':
                result = await hybrid_parsing_tiktok(text)
                platform_name = "TikTok"
            elif platform == 'instagram':
                result = await download_instagram(text)
                platform_name = "Instagram"
            elif platform == 'youtube':
                result = await download_youtube(text)
                platform_name = "YouTube"
            elif platform == 'twitter':
                result = await download_twitter(text)
                platform_name = "Twitter"
            else:
                result = None

            if result:
                video = result[0]
                video_hq = result[1] if result[1] else video
                music = result[2]
                caption = result[3]
                link = result[4]
                
                # Create caption text
                caption_text = f"✨ *{platform_name} Download Complete!* 🎉\n\n"
                if caption:
                    caption_text += f"📝 *Caption:* {caption}\n"
                if music:
                    caption_text += f"🎵 *Sound:* {music}\n"
                caption_text += f"🔗 *Link:* {link}\n\n"
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
                        text=f"✅ *{platform_name} Download Successful!* 🎉\n\n"
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
                         f"Please try a different link or platform.\n\n"
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