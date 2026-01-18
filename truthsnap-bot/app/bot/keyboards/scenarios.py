"""
Keyboard builders for scenario-based flows
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_scenario_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Initial scenario selection keyboard

    Returns keyboard with two main scenarios:
    - 👤 I'm being blackmailed (Adult/General)
    - 🆘 I need help (Teenager)
    """
    keyboard = [
        [InlineKeyboardButton(
            text="👤 I'm being blackmailed",
            callback_data="scenario:adult_blackmail"
        )],
        [InlineKeyboardButton(
            text="🆘 I need help (Teenager)",
            callback_data="scenario:teenager_sos"
        )],
        [InlineKeyboardButton(
            text="📚 Knowledge Base",
            callback_data="scenario:knowledge_base"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_adult_blackmail_step1_keyboard() -> InlineKeyboardMarkup:
    """
    Adult Blackmail Scenario - Step 1: After analysis completed

    Shows options:
    - 📄 Get Forensic PDF
    - 🛡️ Counter-measures
    """
    keyboard = [
        [InlineKeyboardButton(
            text="📄 Get Forensic PDF",
            callback_data="adult:forensic_pdf"
        )],
        [InlineKeyboardButton(
            text="🛡️ Counter-measures",
            callback_data="adult:counter_measures"
        )],
        [InlineKeyboardButton(
            text="🔙 Back to scenarios",
            callback_data="scenario:select"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_counter_measures_keyboard(analysis_id: str) -> InlineKeyboardMarkup:
    """
    Counter-measures menu for Adult Blackmail scenario

    Shows:
    - 💬 Safe Response Generator
    - 🚫 Report to StopNCII
    - 🚨 Report to FBI IC3
    - 📄 Download Forensic PDF
    """
    keyboard = [
        [InlineKeyboardButton(
            text="💬 Generate Safe Response",
            callback_data="counter:safe_response"
        )],
        [InlineKeyboardButton(
            text="🚫 Report to StopNCII",
            url="https://stopncii.org/"
        )],
        [InlineKeyboardButton(
            text="🚨 Report to FBI IC3",
            url="https://www.ic3.gov/Home/ComplaintChoice/default.aspx"
        )],
        [InlineKeyboardButton(
            text="📄 Download PDF Report",
            callback_data=f"pdf_report:{analysis_id}"
        )],
        [InlineKeyboardButton(
            text="🔙 Back",
            callback_data="adult:back_to_analysis"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_teenager_step2_keyboard() -> InlineKeyboardMarkup:
    """
    Teenager SOS - Step 2: After photo analysis

    Shows:
    - 🤝 How to tell my parents
    - 🚫 Stop the Spread
    - 📚 What is sextortion?
    """
    keyboard = [
        [InlineKeyboardButton(
            text="🤝 How to tell my parents",
            callback_data="teen:tell_parents"
        )],
        [InlineKeyboardButton(
            text="🚫 Stop the Spread",
            callback_data="teen:stop_spread"
        )],
        [InlineKeyboardButton(
            text="📚 What is sextortion?",
            callback_data="teen:education"
        )],
        [InlineKeyboardButton(
            text="🔙 Back to scenarios",
            callback_data="scenario:select"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_stop_spread_keyboard() -> InlineKeyboardMarkup:
    """
    Emergency protection resources for teenagers

    Links to:
    - Take It Down (NCMEC anonymous removal)
    - FBI Tips for Teens
    - NCMEC CyberTipline
    """
    keyboard = [
        [InlineKeyboardButton(
            text="🔗 Take It Down (Anonymous Removal)",
            url="https://takeitdown.ncmec.org/"
        )],
        [InlineKeyboardButton(
            text="📱 FBI Tips for Teens",
            url="https://www.fbi.gov/video-repository/newss-sextortion-know-the-warning-signs/view"
        )],
        [InlineKeyboardButton(
            text="🚨 Report to NCMEC",
            url="https://report.cybertip.org"
        )],
        [InlineKeyboardButton(
            text="🔙 Back",
            callback_data="teen:back_to_analysis"
        )],
        [InlineKeyboardButton(
            text="🏠 Main Menu",
            callback_data="scenario:select"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_tell_parents_keyboard(analysis_id: str) -> InlineKeyboardMarkup:
    """
    Parent communication helper

    Shows:
    - 📄 Get PDF Report to show parents
    - 💬 See conversation script
    - 🔙 Back
    """
    keyboard = [
        [InlineKeyboardButton(
            text="📄 Get PDF Report (Show to parents)",
            callback_data=f"pdf_report:{analysis_id}"
        )],
        [InlineKeyboardButton(
            text="💬 See conversation script",
            callback_data="teen:conversation_script"
        )],
        [InlineKeyboardButton(
            text="🔙 Back",
            callback_data="teen:back_to_analysis"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
