from modules.transaction_analysis import calculate_transaction_risk
from modules.voice_analysis import analyze_voice
from modules.behavior_analysis import calculate_behavior_risk
from modules.context_analysis import calculate_context_risk
from modules.explainability import evaluate_risk, fusion_score
from utils.helpers import risk_level, decision_for_risk_level


def run_risk_engine(transaction, voice_transcript='', audio_path=None, behavior=None, context=None, api_key=None):
    tx = calculate_transaction_risk(transaction)
    behavior_risk = calculate_behavior_risk(behavior)
    voice = analyze_voice(voice_transcript or '', api_key=api_key)
    context_risk = calculate_context_risk(context)

    result = evaluate_risk(tx, voice, behavior_risk, context_risk)
    return {
        'transaction': tx,
        'voice': voice,
        'behavior': behavior_risk,
        'context': context_risk,
        'final': result,
    }
