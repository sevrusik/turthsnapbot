"""
FSM States for bot conversation flow
"""

from aiogram.fsm.state import State, StatesGroup


class ScenarioStates(StatesGroup):
    """States for scenario selection and flow"""
    selecting_scenario = State()


class AdultBlackmailStates(StatesGroup):
    """States for Adult/General Digital Blackmail scenario (👤 I'm being blackmailed)"""
    waiting_for_evidence = State()  # Step 1: Upload photo for analysis
    reviewing_analysis = State()     # Step 2: Review scoring + verdict
    counter_measures = State()       # Step 3: Counter-attack options


class TeenagerSOSStates(StatesGroup):
    """States for Teenager SOS scenario (🆘 I need help)"""
    psychological_stop = State()     # Step 1: Calming message
    waiting_for_photo = State()      # Step 2: Photo analysis (empathetic tone)
    ally_search = State()            # Step 3: How to tell parents
    emergency_protection = State()   # Step 4: Stop the Spread


class AnalysisStates(StatesGroup):
    """Legacy states for photo analysis flow (backwards compatibility)"""
    waiting_for_photo = State()
    processing = State()
    awaiting_payment = State()
