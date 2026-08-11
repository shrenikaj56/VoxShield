from utils.helpers import risk_level, decision_for_risk_level


def build_contributor_summary(transaction_risk, voice_risk, behavior_risk, context_risk, transaction_reasons, voice_reasons, behavior_reasons, context_reasons):
    contributors = []
    contributors.extend([('Transaction', tx) for tx in transaction_reasons])
    contributors.extend([('Voice', vx) for vx in voice_reasons])
    contributors.extend([('Behavior', bx) for bx in behavior_reasons])
    contributors.extend([('Context', cx) for cx in context_reasons])
    return contributors


def fusion_score(transaction_risk_score, voice_risk_score, behavior_risk_score, context_risk_score=0):
    from utils.config import RISK_WEIGHTS
    final = (
        transaction_risk_score * RISK_WEIGHTS['transaction'] +
        voice_risk_score * RISK_WEIGHTS['voice'] +
        behavior_risk_score * RISK_WEIGHTS['behavior'] +
        context_risk_score * RISK_WEIGHTS['context']
    )
    return int(round(final))


def evaluate_risk(transaction_risk, voice_risk, behavior_risk, context_risk=None):
    if context_risk is None:
        context_risk = {'score': 0, 'reasons': []}
    score = fusion_score(
        transaction_risk['score'],
        voice_risk['score'],
        behavior_risk['score'],
        context_risk['score']
    )
    level = risk_level(score)
    decision = decision_for_risk_level(level)
    return {
        'score': score,
        'level': level,
        'decision': decision,
        'reasons': {
            'transaction': transaction_risk['reasons'],
            'voice': voice_risk['reasons'],
            'behavior': behavior_risk['reasons'],
            'context': context_risk['reasons'],
        }
    }
