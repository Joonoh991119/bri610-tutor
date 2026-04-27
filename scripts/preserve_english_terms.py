#!/usr/bin/env python3
"""
Preserve English-original technical terms in lecture summaries.

User mandate: 학술 용어, 전자기학 / 신경과학 고유명사는 한국어로 번역하지
말고 영어 원형 유지. 번역어가 본문에 들어가 있으면 영어 원형 + (Korean
parenthetical) 형태로 변환.

Strategy: regex pass that detects common Korean technical translations and
replaces them with `English term (Korean explanation)` form. The first
occurrence of each term gets the parenthetical; subsequent occurrences in the
same summary keep just the English form.

Idempotent: tracks already-converted (English (Korean)) patterns and skips.
"""
import re, os, psycopg2

DB_DSN = os.environ.get('DATABASE_URL', 'dbname=bri610 user=tutor password=tutor610 host=localhost')

# Korean term → (English, Korean parenthetical to use on first occurrence).
# Order: longest Korean phrase first to avoid partial matches.
TERM_MAP = [
    # (Korean translation, English, Korean explanation in parens)
    ('정상상태',           'steady state',          '평형 도달 후 시간 비의존 상태'),
    ('비정상상태',         'transient state',       '시간 의존 동적 상태'),
    ('누설 전류',          'leaky current',         'rest 시 흐르는 부분 채널 전류'),
    ('누설전류',           'leaky current',         'rest 시 흐르는 부분 채널 전류'),
    ('누설 채널',          'leak channel',          '항상 부분 열려있는 채널'),
    ('누설채널',           'leak channel',          '항상 부분 열려있는 채널'),
    ('동질',               'homogeneous',           '우변에 강제 항이 없는 형태'),
    ('비동질',             'inhomogeneous',         '우변에 강제 항이 있는 형태'),
    ('축전기',             'capacitor',             '전하를 저장하는 회로 소자'),
    ('전기용량',           'capacitance',           '단위 전압당 저장 가능한 전하'),
    ('정전용량',           'capacitance',           '단위 전압당 저장 가능한 전하'),
    ('도전도',             'conductance',           '단위 전압차당 흐르는 전류'),
    ('전도도',             'conductance',           '단위 전압차당 흐르는 전류'),
    ('막전위',             'membrane potential',    'V_m'),
    ('휴지 막전위',        'resting membrane potential', 'V_rest'),
    ('휴지막전위',         'resting membrane potential', 'V_rest'),
    ('활동전위',           'action potential',      'spike, 신경 흥분의 단일 사건'),
    ('재분극',             'repolarization',        'V 가 rest 쪽으로 복귀'),
    ('탈분극',             'depolarization',        'V 가 양의 방향으로 이동'),
    ('과분극',             'hyperpolarization',     'V 가 rest 보다 더 음수'),
    ('불응기',             'refractory period',     'AP 후 재발화 어려운 기간'),
    ('절대 불응기',        'absolute refractory period', 'h, m 모두 죽어 발화 불가'),
    ('상대 불응기',        'relative refractory period', 'h 회복 중, 큰 자극이면 가능'),
    ('역치',               'threshold',             'AP 발화 시작 전압'),
    ('임계 전압',          'threshold voltage',     'AP 발화 시작 전압'),
    ('역치 전압',          'threshold voltage',     'AP 발화 시작 전압'),
    ('가역 전위',          'reversal potential',    'E_X, 알짜 전류 0인 전압'),
    ('반전 전위',          'reversal potential',    'E_X, 알짜 전류 0인 전압'),
    ('평형 전위',          'equilibrium potential', 'Nernst 식에 의한 단일 이온 평형 전압'),
    ('네른스트 전위',      'Nernst potential',      'E_X = (RT/zF) ln([X]_o/[X]_i)'),
    ('네른스트 식',        'Nernst equation',       'E_X = (RT/zF) ln([X]_o/[X]_i)'),
    ('구동력',             'driving force',         '(V − E_X), 이온이 움직이는 방향'),
    ('보존력',             'conservative force',    '경로 무관한 힘'),
    ('전압 클램프',        'voltage clamp',         'V 고정해 ionic 전류만 분리하는 실험'),
    ('전류 클램프',        'current clamp',         '주입 전류 통제하고 V 측정'),
    ('패치 클램프',        'patch clamp',           '단일 채널 전류 측정'),
    ('이중 펄스',          'two-pulse',             'voltage clamp 의 두 단계 protocol'),
    ('시상수',             'time constant',         'τ, exponential decay 의 e-folding'),
    ('공간상수',           'space constant',        'λ, e-folding 거리 (cable)'),
    ('길이상수',           'length constant',       'λ, e-folding 거리 (cable)'),
    ('시냅스 가소성',      'synaptic plasticity',   '시냅스 강도의 시간 변화'),
    ('흥분성',             'excitability',          '자극에 발화 가능한 정도'),
    ('흥분성 시냅스',      'excitatory synapse',    'EPSP 를 만드는 시냅스'),
    ('억제성 시냅스',      'inhibitory synapse',    'IPSP 를 만드는 시냅스'),
    ('수상돌기',           'dendrite',              '입력 받는 가지'),
    ('축삭',               'axon',                  '출력 보내는 가지'),
    ('수초',               'myelin',                'Schwann/oligodendrocyte 가 만드는 절연막'),
    ('Ranvier 결절',       'node of Ranvier',       'myelin 사이 노출된 axon 부위'),
    ('도약 전도',          'saltatory conduction',  'AP 가 노드 사이를 점프'),
    ('연속 전도',          'continuous conduction', '무수초 axon 의 점진적 전파'),
    ('이온 채널',          'ion channel',           'membrane 에 박힌 단백질 통로'),
    ('전압 의존',          'voltage-dependent',     '게이팅이 V 함수'),
    ('전압-의존',          'voltage-dependent',     '게이팅이 V 함수'),
    ('전압의존',           'voltage-dependent',     '게이팅이 V 함수'),
    ('막 방정식',          'membrane equation',     'C_m dV/dt = ... KCL form'),
    ('케이블 방정식',      'cable equation',        '공간 + 시간 PDE'),
    ('일반 균형 평행',     'permeability-weighted average', 'GHK 식의 본질'),
    ('전도도 가중 평균',   'conductance-weighted average', 'V_∞ 가 g_X·E_X 가중 평균'),
    ('투과도 가중 평균',   'permeability-weighted average', 'GHK V_m'),
]


def already_protected(text: str, eng: str) -> bool:
    """Check if `eng` already appears with parenthetical Korean."""
    pattern = rf'\b{re.escape(eng)}\s*\([가-힣 ,.]+\)'
    return bool(re.search(pattern, text))


def convert(text: str) -> tuple[str, int]:
    """Replace Korean translations with English-original (parenthetical Korean on first occurrence)."""
    n_total = 0
    for kr, eng, kr_paren in TERM_MAP:
        # Skip if user-visible English form is missing or already widespread
        # Find Korean term occurrences NOT already inside backticks/code
        # OR inside SVG/figure markup
        kr_re = re.compile(rf'(?<!\w){re.escape(kr)}(?!\w)')

        first_done = already_protected(text, eng)
        replacements_in_this_term = 0

        def repl(match):
            nonlocal first_done, replacements_in_this_term
            replacements_in_this_term += 1
            if not first_done:
                first_done = True
                return f'*{eng}* ({kr_paren})'
            return f'*{eng}*'

        # Avoid replacing inside code blocks, SVG, math
        # Simple approach: split by code+svg+math markers, only convert in non-code chunks
        chunks = re.split(r'(\$\$[^\$]*?\$\$|\$[^\$\n]*?\$|<svg[^>]*>.*?</svg>|`[^`\n]*?`|<code[^>]*>.*?</code>)', text, flags=re.DOTALL)
        new_chunks = []
        for i, chunk in enumerate(chunks):
            if i % 2 == 0:
                # Plain prose chunk → safe to replace
                new_chunks.append(kr_re.sub(repl, chunk))
            else:
                # Code/math/svg chunk → preserve untouched
                new_chunks.append(chunk)
        text = ''.join(new_chunks)
        n_total += replacements_in_this_term

    return text, n_total


def main():
    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT lecture, summary FROM lecture_summaries ORDER BY lecture")
            rows = cur.fetchall()

        total_changes = 0
        for lec, summary in rows:
            new_text, n = convert(summary)
            if n > 0:
                with conn.cursor() as cur:
                    cur.execute("UPDATE lecture_summaries SET summary=%s WHERE lecture=%s", (new_text, lec))
                conn.commit()
                total_changes += n
                print(f'  {lec}: {n} replacements ({len(summary)} → {len(new_text)} chars)')
            else:
                print(f'  {lec}: clean')

        print(f'\nTotal English-term protections applied: {total_changes}')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
