"""
Bot Notification Service

Sends analysis results back to users via Telegram
"""

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
from typing import Dict, Optional
import aiohttp

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import settings

logger = logging.getLogger(__name__)


class BotNotifier:
    """
    Sends notifications to users via Telegram bot
    """

    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    async def _reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Convert GPS coordinates to city/country name using Nominatim (OpenStreetMap)

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Returns:
            "City, Country" or None if lookup fails
        """
        try:
            # Nominatim API (free, no API key required)
            url = f"https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "zoom": 10,  # City level
                "accept-language": "en"
            }
            headers = {
                "User-Agent": "TruthSnapBot/1.0"  # Required by Nominatim
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as response:
                    if response.status == 200:
                        data = await response.json()
                        address = data.get("address", {})

                        # Try to get city (various possible fields)
                        city = (
                            address.get("city") or
                            address.get("town") or
                            address.get("village") or
                            address.get("municipality") or
                            address.get("county")
                        )

                        country = address.get("country")

                        if city and country:
                            return f"{city}, {country}"
                        elif city:
                            return city
                        elif country:
                            return country

        except Exception as e:
            logger.warning(f"Reverse geocoding failed for {latitude}, {longitude}: {e}")

        return None

    def _format_exif_datetime(self, exif_datetime: str) -> str:
        """
        Format EXIF datetime to human-readable format

        Input: "2025:12:16 07:42:09" or "2025-12-16 07:42:09"
        Output: "16 Dec 2025, 07:42"
        """
        try:
            # Replace : with - for standard parsing
            datetime_str = exif_datetime.replace(':', '-', 2)

            # Parse datetime
            from datetime import datetime
            dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

            # Format nicely
            return dt.strftime('%d %b %Y, %H:%M')
        except:
            # Fallback to original if parsing fails
            return exif_datetime

    def _format_software_name(self, software: str, camera_make: str = '', camera_model: str = '') -> str:
        """
        Format software name to be more user-friendly

        Examples:
        - "26.2" (from iPhone) → "iOS 26.2"
        - "Adobe Photoshop 2024" → "Adobe Photoshop 2024"
        - "GIMP 2.10" → "GIMP 2.10"
        """
        software = str(software).strip()

        # Check if it's just a version number (iPhone/iOS)
        if software.replace('.', '').isdigit():
            # It's a version number - likely iOS
            if 'apple' in camera_make or 'iphone' in camera_model:
                return f"iOS {software}"
            else:
                return f"Version {software}"

        # Return as-is if it already looks like a proper name
        return software

    def _format_camera_name(self, make: str, model: str) -> str:
        """
        Format camera make/model to be more readable

        Examples:
        - "apple", "iphone 13" → "Apple iPhone 13"
        - "canon", "eos r5" → "Canon EOS R5"
        - "samsung", "galaxy s23" → "Samsung Galaxy S23"
        """
        # Clean inputs
        make = str(make).strip().title() if make else ''
        model = str(model).strip() if model else ''

        # Special case: iPhone
        if 'iphone' in model.lower():
            # "iphone 13" → "iPhone 13"
            model_parts = model.split()
            model = 'iPhone ' + ' '.join(model_parts[1:]) if len(model_parts) > 1 else 'iPhone'

        # Special case: EOS (Canon)
        elif 'eos' in model.lower():
            # "eos r5" → "EOS R5"
            model = model.upper()

        # Special case: Galaxy (Samsung)
        elif 'galaxy' in model.lower():
            # "galaxy s23" → "Galaxy S23"
            model = model.title()

        # Combine make and model
        if make and model:
            # Avoid duplication: "Apple iPhone" not "Apple apple iphone"
            if make.lower() not in model.lower():
                return f"{make} {model}"
            else:
                return model.title()
        elif make:
            return make
        elif model:
            return model.title()
        else:
            return "Unknown"

    def _build_free_message(
        self,
        emoji: str,
        verdict_label: str,
        confidence: float,
        result: Dict,
        processing_ms: int,
        verdict: str
    ) -> str:
        """Build basic message for free tier users"""

        message = f"{emoji} <b>{verdict_label}</b>\n\n"
        message += f"<b>Confidence:</b> {confidence * 100:.1f}%\n"

        # Add watermark info if detected
        if result.get('watermark_detected'):
            watermark = result.get('watermark_analysis', {})
            watermark_type = watermark.get('type', 'Unknown')
            message += f"\n🔍 <b>Watermark detected:</b> {watermark_type.upper()}\n"

        # Processing time
        message += f"\n⏱ <b>Analysis time:</b> {processing_ms / 1000:.1f}s\n"

        # Call to action based on verdict
        if verdict == 'ai_generated':
            message += (
                "\n⚠️ <b>This image appears to be AI-generated.</b>\n\n"
                "If you're being blackmailed with this photo:\n"
                "1. DO NOT pay the blackmailer\n"
                "2. Save this analysis as evidence\n"
                "3. Report to authorities\n"
                "4. Block the sender"
            )
        elif verdict == 'real':
            message += (
                "\n✅ <b>This appears to be a real photograph.</b>\n\n"
                "Our AI did not detect manipulation or generation patterns."
            )
        elif verdict == 'inconclusive':
            message += (
                "\n❓ <b>Unable to determine with high confidence.</b>\n\n"
                "Consider getting a manual review or trying again with a higher quality image."
            )

        return message

    async def _build_pro_message(
        self,
        emoji: str,
        verdict_label: str,
        confidence: float,
        result: Dict,
        processing_ms: int,
        analysis_id: str,
        verdict: str
    ) -> str:
        """Build enhanced message for pro tier users with detailed forensic data"""

        # Header with verdict and confidence
        message = f"{emoji} <b>{verdict_label} ({confidence * 100:.1f}%)</b>\n\n"

        # Processing time
        message += f"⏱ <b>Analysis time:</b> {processing_ms / 1000:.1f}s\n\n"

        # === DIGITAL FOOTPRINT SECTION ===
        message += "🗂 <b>DIGITAL FOOTPRINT:</b>\n"

        metadata = result.get('metadata', {})
        validation = result.get('metadata_validation', {})

        # Capture date/time
        date_time_raw = metadata.get('exif', {}).get('DateTimeOriginal') or \
                        metadata.get('exif', {}).get('DateTime') or \
                        metadata.get('exif', {}).get('CreateDate')

        if date_time_raw:
            # Format EXIF datetime: "2025:12:16 07:42:09" → "16 Dec 2025, 07:42"
            date_time = self._format_exif_datetime(date_time_raw)
            message += f"📅 <b>Captured:</b> {date_time}\n"
        else:
            message += f"📅 <b>Captured:</b> <i>No timestamp (suspicious)</i>\n"

        # Software/Creator
        software_raw = metadata.get('exif', {}).get('Software') or \
                       metadata.get('exif', {}).get('Creator') or \
                       metadata.get('exif', {}).get('CreatorTool')

        camera_make = metadata.get('exif', {}).get('Make', '').lower()
        camera_model = metadata.get('exif', {}).get('Model', '').lower()

        if software_raw:
            # Format software name nicely
            software = self._format_software_name(software_raw, camera_make, camera_model)

            # Check if AI software
            ai_indicators = ['photoshop', 'midjourney', 'dall-e', 'stable diffusion',
                           'ai', 'gemini', 'imagen', 'firefly', 'canva', 'generative']
            is_ai_software = any(ai in software.lower() for ai in ai_indicators)

            if is_ai_software:
                message += f"🛠 <b>Created with:</b> {software} ⚠️ <i>(AI Signature)</i>\n"
            else:
                message += f"🛠 <b>Created with:</b> {software}\n"
        else:
            message += f"🛠 <b>Created with:</b> <i>Unknown/Stripped</i>\n"

        # Camera/Device
        if camera_make or camera_model:
            # Format camera name nicely
            camera_info = self._format_camera_name(camera_make, camera_model)
            message += f"📱 <b>Device:</b> {camera_info}\n"
        else:
            if verdict == 'ai_generated':
                message += f"📱 <b>Device:</b> <i>No Camera Data (AI Signature)</i>\n"
            else:
                message += f"📱 <b>Device:</b> <i>Not available</i>\n"

        # GPS Location
        gps = metadata.get('gps')
        if gps and gps.get('latitude') and gps.get('longitude'):
            lat = gps['latitude']
            lon = gps['longitude']

            # Create Google Maps link
            maps_url = f"https://www.google.com/maps?q={lat},{lon}"

            # Try to get city name via reverse geocoding
            location_name = await self._reverse_geocode(lat, lon)

            if location_name:
                # Show: "City, Country" + clickable coordinates
                message += f"📍 <b>GPS:</b> {location_name} (<a href=\"{maps_url}\">{lat:.4f}, {lon:.4f}</a>)\n"
            else:
                # Show: clickable coordinates only
                message += f"📍 <b>GPS:</b> <a href=\"{maps_url}\">{lat:.4f}, {lon:.4f}</a>\n"
        else:
            message += f"📍 <b>GPS:</b> <i>None Detected</i>\n"

        message += "\n"

        # === RED FLAGS SECTION ===
        red_flags = validation.get('red_flags', [])
        ai_signatures = result.get('ai_signatures', {})
        fft_analysis = result.get('fft_analysis', {})
        face_swap = result.get('face_swap_analysis', {})

        has_red_flags = (
            red_flags or
            ai_signatures.get('patterns_detected') or
            (fft_analysis.get('score', 0) > 0.6) or
            (face_swap.get('score', 0) > 0.5)
        )

        if has_red_flags:
            message += "⚠️ <b>RED FLAGS:</b>\n"

            # AI Pattern detection
            if ai_signatures.get('patterns_detected'):
                ai_score = result.get('findings', [{}])[0].get('ai_score', 0)
                if ai_score > 0.7:
                    message += f"• <b>AI Pattern:</b> Strong (GAN/Diffusion)\n"
                elif ai_score > 0.5:
                    message += f"• <b>AI Pattern:</b> Moderate\n"
                else:
                    message += f"• <b>AI Pattern:</b> Weak indicators\n"

            # Metadata issues
            fraud_score = validation.get('score', 0)
            if fraud_score >= 80:
                message += f"• <b>Metadata:</b> Stripped/Manipulated ({fraud_score}/100)\n"
            elif fraud_score >= 50:
                message += f"• <b>Metadata:</b> Suspicious ({fraud_score}/100)\n"

            # Specific red flags (top 2)
            for flag in red_flags[:2]:
                reason = flag.get('reason', '').replace('EXIF', 'Metadata')
                if reason:
                    message += f"• {reason}\n"

            # FFT Analysis
            if fft_analysis.get('score', 0) > 0.6:
                message += f"• <b>Frequency Analysis:</b> AI artifacts detected\n"

            # Face swap detection
            if face_swap.get('score', 0) > 0.5:
                faces = face_swap.get('faces_detected', 0)
                message += f"• <b>Face Integrity:</b> Artifacts detected ({faces} face{'s' if faces != 1 else ''})\n"

            # Watermark detection
            if result.get('watermark_detected'):
                watermark = result.get('watermark_analysis', {})
                wm_type = watermark.get('type', 'Unknown')
                message += f"• <b>Watermark:</b> {wm_type} detected\n"

            # Visual watermark (OCR)
            if result.get('visual_watermark', {}).get('detected'):
                vw = result['visual_watermark']
                provider = vw.get('provider', 'Unknown')
                text = vw.get('text_found', '')
                message += f"• <b>Visual Mark:</b> \"{text}\" ({provider})\n"

            message += "\n"

        # === VERDICT SECTION ===
        message += "🛡 <b>WHAT TO DO:</b>\n"

        if verdict == 'ai_generated':
            message += (
                "• <b>DO NOT</b> pay the blackmailer\n"
                "• Save this analysis as evidence\n"
                "• Report to authorities immediately\n"
                "• Block the sender\n\n"
                "<i>This image shows strong AI generation signatures.</i>"
            )
        elif verdict == 'manipulated':
            message += (
                "• This image has been altered\n"
                "• <b>DO NOT</b> pay if being blackmailed\n"
                "• Save as evidence and report\n\n"
                "<i>Detected manipulation/editing patterns.</i>"
            )
        elif verdict == 'real':
            message += (
                "• This appears to be an authentic photo\n"
                "• Consider context and source\n"
                "• If threatened, still report to authorities\n\n"
                "<i>No AI or manipulation detected.</i>"
            )
        else:
            message += (
                "• Analysis inconclusive\n"
                "• Request manual review\n"
                "• Report if being threatened\n\n"
                "<i>Unable to determine with high confidence.</i>"
            )

        # Analysis ID
        message += f"\n📄 <b>Analysis ID:</b> <code>{analysis_id}</code>"

        return message

    async def send_analysis_result(
        self,
        chat_id: int,
        message_id: int,
        result: Dict,
        tier: str,
        analysis_id: str,
        scenario: str = None
    ):
        """
        Send analysis result to user

        Args:
            chat_id: Chat ID
            message_id: Message ID to reply to
            result: Analysis result from FraudLens
            tier: User tier (free/pro)
            analysis_id: Analysis ID
            scenario: Scenario context (adult_blackmail/teenager_sos/None)
        """

        # Build message based on verdict
        verdict = result['verdict']
        confidence = result['confidence']

        # Emoji and message mapping
        verdict_emoji = {
            'real': '✅',
            'ai_generated': '🤖',
            'manipulated': '⚠️',
            'inconclusive': '❓'
        }

        verdict_text = {
            'real': 'REAL PHOTO',
            'ai_generated': 'AI-GENERATED',
            'manipulated': 'MANIPULATED',
            'inconclusive': 'INCONCLUSIVE'
        }

        emoji = verdict_emoji.get(verdict, '❓')
        verdict_label = verdict_text.get(verdict, verdict.upper())

        # Processing time
        processing_ms = result.get('processing_time_ms', 0)

        # Always show full PRO message for all users
        message = await self._build_pro_message(
            emoji, verdict_label, confidence, result,
            processing_ms, analysis_id, verdict
        )

        # Build keyboard based on scenario
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        if scenario == "adult_blackmail":
            # Adult Blackmail scenario - show Counter-measures + PDF
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="📄 Get Forensic PDF",
                    callback_data=f"pdf_report:{analysis_id}"
                )
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="🛡️ Counter-measures",
                    callback_data="adult:counter_measures"
                )
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="🔙 Back to Main Menu",
                    callback_data="scenario:select"
                )
            ])

        elif scenario == "teenager_sos":
            # Teenager SOS scenario - show Parent Help + Stop Spread
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="📄 Get PDF Report",
                    callback_data=f"pdf_report:{analysis_id}"
                )
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="🤝 How to tell my parents",
                    callback_data="teen:tell_parents"
                )
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="🚫 Stop the Spread",
                    callback_data="teen:stop_spread"
                )
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="📚 What is sextortion?",
                    callback_data="teen:education"
                )
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="🔙 Back to Main Menu",
                    callback_data="scenario:select"
                )
            ])

        else:
            # Legacy flow (no scenario) - show basic buttons
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="📄 Get PDF Report",
                    callback_data=f"pdf_report:{analysis_id}"
                )
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="📤 Share Result",
                    switch_inline_query=f"Analysis: {verdict_label}"
                )
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="🔙 Back to Main Menu",
                    callback_data="scenario:select"
                )
            ])

        # Send message
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML",
                reply_to_message_id=message_id,
                reply_markup=keyboard if keyboard.inline_keyboard else None
            )

            logger.info(f"Sent analysis result to chat {chat_id}")

        except Exception as e:
            logger.error(f"Failed to send result to chat {chat_id}: {e}")
            raise

    async def send_error_message(
        self,
        chat_id: int,
        message_id: int,
        error: str
    ):
        """
        Send error message to user

        Args:
            chat_id: Chat ID
            message_id: Message ID to reply to
            error: Error message
        """

        message = (
            "❌ <b>Analysis Failed</b>\n\n"
            "Sorry, something went wrong during analysis.\n\n"
            f"<code>{error}</code>\n\n"
            "Please try again or contact support: /support"
        )

        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML",
                reply_to_message_id=message_id
            )

            logger.info(f"Sent error message to chat {chat_id}")

        except Exception as e:
            logger.error(f"Failed to send error to chat {chat_id}: {e}")

    async def close(self):
        """Close bot session"""
        await self.bot.session.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
