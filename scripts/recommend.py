"""
웹툰 추천 엔진 (키워드 매칭 기반)
- 입력 웹툰의 genre, tags, 줄거리에서 키워드 추출
- 전체 웹툰 DB에서 유사도 점수 계산
- 유사도 순으로 추천 결과 출력

사용법:
    python scripts/recommend.py "템빨"
    python scripts/recommend.py "나 혼자만 레벨업" --top 20
    python scripts/recommend.py "템빨" --verbose
"""

import os
import re
import sys
import argparse
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


WEBTOON_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "webtoon")

# 불용어 - 매칭에서 제외할 일반적인 단어
STOPWORDS = {
    "그리고", "하지만", "그러나", "그런데", "그래서", "그러면", "그렇게",
    "이것", "저것", "그것", "여기", "저기", "거기",
    "하는", "하고", "하면", "하지", "하여", "했다", "한다", "되는", "되고", "되어",
    "있는", "있고", "있다", "없는", "없다", "있지", "없이",
    "그의", "그녀", "그가", "그를", "나의", "나는", "나를", "내가",
    "것이", "것을", "것은", "것도", "것에",
    "이런", "저런", "어떤", "모든", "다른",
    "위해", "대한", "통해", "따라", "관한",
    "매주", "연재", "웹툰", "작가", "원작", "만화", "소설",
    "됩니다", "합니다", "입니다", "습니다", "습니까",
}

# 장르/테마 키워드 그룹 - 같은 그룹 내 키워드는 유사한 것으로 취급
# --- 테마 키워드 그룹 (소재/장르) ---
KEYWORD_GROUPS = {
    "게임": ["게임", "가상현실", "VR", "VRMMO", "VRMMORPG", "SATISFY", "아레나", "RPG"],
    "레벨업": ["레벨업", "레벨", "성장", "각성", "강해", "만렙", "초월"],
    "던전": ["던전", "게이트", "탑", "미궁", "레이드"],
    "아이템": ["아이템", "템빨", "장비", "무기", "아티팩트", "귀속"],
    "헌터": ["헌터", "각성자", "능력자", "플레이어", "용사", "영웅"],
    "먼치킨": ["먼치킨", "최강", "무쌍", "압도", "사이다", "최약에서"],
    "회귀": ["회귀", "귀환", "환생", "전생", "리셋", "돌아"],
    "대장장이": ["대장장이", "제작", "생산", "크래프트", "단조"],
    "퀘스트": ["퀘스트", "미션", "시스템", "스탯", "스킬", "스테이터스"],
    "무협": ["무협", "무림", "검", "검술", "검사", "무공", "내공", "강호", "문파", "사파"],
    "로맨스": ["로맨스", "연애", "사랑", "순정", "달달", "설레"],
    "로판": ["로판", "영애", "공녀", "황녀", "공작", "후작", "백작", "귀족", "빙의"],
    "액션": ["액션", "전투", "배틀", "격투", "싸움"],
    "스릴러": ["스릴러", "공포", "호러", "좀비", "괴물", "살인"],
    "일상": ["일상", "힐링", "코미디", "개그", "웃긴"],
    "스포츠": ["스포츠", "야구", "축구", "농구", "복싱", "격투기"],
    "학원": ["학원", "학교", "학생", "교실", "아카데미"],
    "현대판타지": ["현대판타지", "이세계", "차원", "이계", "소환"],
}

# --- 톤/분위기 키워드 그룹 ---
TONE_GROUPS = {
    "시리어스": [
        "죽음", "죽었", "처참", "비극", "절망", "고통", "복수", "배신",
        "살아남", "생존", "전쟁", "희생", "피", "암흑", "어둠", "지옥",
        "최후", "운명", "숙명", "멸망", "최악", "잔혹", "냉혹", "고독",
        "비밀", "음모", "야망", "몰락", "파멸", "죽을", "목숨",
    ],
    "코미디": [
        "코미디", "개그", "웃긴", "유쾌", "유머", "엉뚱", "병맛",
        "황당", "어이없", "웃음", "빵터", "ㅋ", "뿅", "헐",
        "불운", "노가다", "착각", "쩐다", "짤", "만렙", "치트",
        "라이프", "일상", "사기", "버그", "먹방", "식도락",
    ],
    "다크": [
        "공포", "호러", "괴물", "악마", "악몽", "저주", "피",
        "사냥", "살인", "학살", "기괴", "괴이", "미스터리", "납치",
        "감금", "추적", "살아있", "시체", "유령", "귀신", "악령",
    ],
    "열혈": [
        "열혈", "뜨거운", "불꽃", "투지", "의지", "포기하지",
        "동료", "우정", "신념", "정의", "싸움", "도전",
        "꿈", "목표", "열정", "각오", "맹세", "약속",
    ],
    "힐링": [
        "힐링", "따뜻", "평화", "행복", "귀여운", "감동",
        "치유", "위로", "쉬는", "느긋", "소소", "잔잔",
        "마을", "요리", "먹는", "일상", "소박",
    ],
}


@dataclass
class Webtoon:
    title: str = ""
    writer: str = ""
    artist: str = ""
    platform: str = ""
    genre: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    status: str = ""
    rating: float = 0.0
    subscribers: int = 0
    url: str = ""
    synopsis: str = ""
    filepath: str = ""

    # 분석 결과
    keywords: set = field(default_factory=set)
    matched_groups: set = field(default_factory=set)
    matched_tones: Dict[str, float] = field(default_factory=dict)  # 톤 이름 → 강도(0~1)


def parse_frontmatter(content: str) -> dict:
    """YAML frontmatter를 간단히 파싱 (외부 의존성 없이)"""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    fm = {}
    raw = match.group(1)

    # 단순 key: value 파싱
    for m in re.finditer(r'^(\w+):\s*"?([^"\n]*)"?\s*$', raw, re.MULTILINE):
        fm[m.group(1)] = m.group(2).strip()

    # 중첩 key (author.writer, author.artist)
    for m in re.finditer(r'^\s+(\w+):\s*"?([^"\n]*)"?\s*$', raw, re.MULTILINE):
        fm[m.group(1)] = m.group(2).strip()

    # 배열 파싱 (genre, tags)
    for key in ["genre", "tags"]:
        arr_match = re.search(rf'^{key}:\s*\[(.*?)\]', raw, re.MULTILINE)
        if arr_match:
            items = re.findall(r'"([^"]*)"', arr_match.group(1))
            fm[key] = items
        else:
            fm[key] = []

    # 숫자 필드
    for key in ["rating", "subscribers", "episodes"]:
        num_match = re.search(rf'^{key}:\s*([\d.]+)', raw, re.MULTILINE)
        if num_match:
            fm[key] = float(num_match.group(1))

    return fm


def extract_synopsis(content: str) -> str:
    """줄거리 섹션 추출"""
    match = re.search(r'## 줄거리\s*\n(.*?)(?=\n## |\n---|\Z)', content, re.DOTALL)
    if match:
        text = match.group(1).strip()
        # 안내문구 제거
        text = re.sub(r'-{3,}.*', '', text, flags=re.DOTALL)
        text = re.sub(r'\[.*?에 접속합니다\.\]', '', text)
        return text.strip()
    return ""


def extract_keywords(text: str) -> set:
    """텍스트에서 의미있는 키워드 추출"""
    if not text:
        return set()

    # 한글 2~6자 단어 추출
    words = re.findall(r'[가-힣]{2,6}', text)

    # 영문 키워드 추출 (SATISFY, VR 등)
    eng_words = re.findall(r'[A-Za-z]{2,}', text)

    keywords = set()
    for w in words:
        if w not in STOPWORDS:
            keywords.add(w)
    for w in eng_words:
        keywords.add(w.upper())

    return keywords


def match_keyword_groups(keywords: set, genre: list, tags: list) -> set:
    """키워드가 어떤 테마 그룹에 속하는지 판별"""
    matched = set()
    all_text = keywords | set(genre) | set(tags)
    all_text_lower = {k.lower() for k in all_text}

    for group_name, group_keywords in KEYWORD_GROUPS.items():
        for gk in group_keywords:
            if gk.lower() in all_text_lower:
                matched.add(group_name)
                break
            # 부분 매칭 (키워드가 텍스트 내에 포함)
            for t in all_text:
                if gk in t or t in gk:
                    matched.add(group_name)
                    break

    return matched


def match_tone_groups(keywords: set, tags: list, synopsis: str) -> Dict[str, float]:
    """텍스트의 톤/분위기 분석 → {톤이름: 강도(0~1)}"""
    all_text = synopsis.lower() + " " + " ".join(tags).lower()
    tone_scores = {}

    for tone_name, tone_keywords in TONE_GROUPS.items():
        hit_count = 0
        for tk in tone_keywords:
            if tk in all_text:
                hit_count += 1
        if hit_count > 0:
            # 매칭 키워드 수를 기반으로 강도 계산 (최대 1.0)
            intensity = min(hit_count / 5.0, 1.0)
            tone_scores[tone_name] = round(intensity, 2)

    return tone_scores


def load_all_webtoons() -> List[Webtoon]:
    """전체 웹툰 데이터 로드"""
    webtoons = []

    for platform in os.listdir(WEBTOON_DIR):
        platform_dir = os.path.join(WEBTOON_DIR, platform)
        if not os.path.isdir(platform_dir):
            continue

        for filename in os.listdir(platform_dir):
            if not filename.endswith(".md"):
                continue

            filepath = os.path.join(platform_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                fm = parse_frontmatter(content)
                synopsis = extract_synopsis(content)

                wt = Webtoon(
                    title=fm.get("title", filename.replace(".md", "")),
                    writer=fm.get("writer", ""),
                    artist=fm.get("artist", ""),
                    platform=fm.get("platform", platform),
                    genre=fm.get("genre", []),
                    tags=fm.get("tags", []),
                    status=fm.get("status", ""),
                    rating=float(fm.get("rating", 0)),
                    subscribers=int(fm.get("subscribers", 0)),
                    url=fm.get("url", ""),
                    synopsis=synopsis,
                    filepath=filepath,
                )

                # 키워드 추출
                all_text = synopsis
                for t in wt.tags:
                    all_text += " " + t
                for g in wt.genre:
                    all_text += " " + g

                wt.keywords = extract_keywords(all_text)
                wt.matched_groups = match_keyword_groups(wt.keywords, wt.genre, wt.tags)
                wt.matched_tones = match_tone_groups(wt.keywords, wt.tags, synopsis)

                webtoons.append(wt)
            except Exception:
                continue

    return webtoons


def make_abbreviation(title: str) -> str:
    """제목에서 약칭 생성 (각 단어 첫 글자 + 숫자 제거)
    예: '나 혼자만 레벨업' → '나혼레', '나혼렙'"""
    # 공백 기준 분리 후 각 단어 첫 글자
    words = title.split()
    return "".join(w[0] for w in words if w)


def get_cho(char: str) -> str:
    """한글 글자의 초성 추출"""
    CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
    code = ord(char) - 0xAC00
    if 0 <= code < 11172:
        return CHO[code // 588]
    return char


def make_chosung(text: str) -> str:
    """텍스트의 초성만 추출"""
    return "".join(get_cho(c) for c in text if c.strip())


def fuzzy_match_score(query: str, title: str) -> float:
    """약칭/퍼지 매칭 점수 (0~1)"""
    q = query.replace(" ", "").lower()
    t = title.replace(" ", "").lower()

    # 정확 일치
    if q == t:
        return 1.0

    # 부분 포함
    if q in t or t in q:
        return 0.9

    # 약칭 매칭 (단어 첫 글자 기반)
    # 예: "나혼렙" → "나 혼자만 레벨업" (각 단어 첫 글자: 나혼레 → 초성 'ㄹ'='렙'의 초성)
    words = title.split()
    if len(words) >= 2:
        # 각 단어 첫 글자로 약칭 생성
        word_initials = "".join(w[0] for w in words if w)
        # 쿼리의 각 글자가 단어 첫 글자의 초성과 매칭되는지
        qi = 0
        wi = 0
        while qi < len(q) and wi < len(word_initials):
            qc = q[qi]
            wc = word_initials[wi]
            if qc == wc or get_cho(wc) == get_cho(qc):
                qi += 1
                wi += 1
            else:
                wi += 1
        if qi == len(q) and len(q) >= 2:
            # 단어 첫 글자 매칭 성공 → 높은 점수
            return 0.85

    # 순차 글자 매칭: 쿼리의 각 글자가 제목에 순서대로 포함
    title_no_space = title.replace(" ", "")
    pos = 0
    matched = 0
    for qc in q:
        found = False
        while pos < len(title_no_space):
            tc = title_no_space[pos]
            pos += 1
            if tc == qc or get_cho(tc) == get_cho(qc):
                matched += 1
                found = True
                break
        if not found:
            break

    if matched == len(q) and len(q) >= 2:
        return 0.7 + (0.1 * matched / len(title_no_space))

    # 초성 매칭
    q_cho = make_chosung(q)
    t_cho = make_chosung(title_no_space)
    if q_cho in t_cho and len(q_cho) >= 2:
        return 0.5

    return 0.0


def find_webtoon(webtoons: List[Webtoon], query: str) -> Optional[Webtoon]:
    """제목으로 웹툰 검색 (약칭/퍼지 매칭 지원)"""
    query_clean = query.strip()

    # 1단계: 정확히 일치
    for wt in webtoons:
        if wt.title == query_clean:
            return wt

    # 2단계: 대소문자 무시 일치
    query_lower = query_clean.lower()
    for wt in webtoons:
        if wt.title.lower() == query_lower:
            return wt

    # 3단계: 퍼지 매칭 (약칭, 부분 일치 등)
    scored = []
    for wt in webtoons:
        score = fuzzy_match_score(query_clean, wt.title)
        if score > 0:
            scored.append((wt, score))

    if scored:
        # 점수순 정렬, 동점이면 tags/genre 풍부한 쪽
        scored.sort(key=lambda x: (x[1], len(x[0].tags) + len(x[0].genre)), reverse=True)
        best = scored[0]
        if best[1] >= 0.5:
            return best[0]

    return None


def calculate_similarity(target: Webtoon, candidate: Webtoon) -> float:
    """두 웹툰 간 유사도 점수 계산"""
    score = 0.0

    # 1. 테마 그룹 매칭 (가장 중요: 가중치 높음)
    if target.matched_groups and candidate.matched_groups:
        group_overlap = target.matched_groups & candidate.matched_groups
        group_union = target.matched_groups | candidate.matched_groups
        if group_union:
            group_score = len(group_overlap) / len(target.matched_groups)
            score += group_score * 50  # 최대 50점

    # 2. 장르 매칭
    if target.genre and candidate.genre:
        target_genres = {g.lower() for g in target.genre if g}
        cand_genres = {g.lower() for g in candidate.genre if g}
        genre_overlap = target_genres & cand_genres
        if genre_overlap:
            score += len(genre_overlap) * 10  # 장르당 10점

    # 3. 태그 매칭
    if target.tags and candidate.tags:
        target_tags = {t.lower() for t in target.tags}
        cand_tags = {t.lower() for t in candidate.tags}
        tag_overlap = target_tags & cand_tags
        score += len(tag_overlap) * 5  # 태그당 5점

    # 4. 줄거리 키워드 매칭
    if target.keywords and candidate.keywords:
        kw_overlap = target.keywords & candidate.keywords
        if kw_overlap:
            kw_score = len(kw_overlap) / max(len(target.keywords), 1)
            score += kw_score * 30  # 최대 30점

    # 5. 톤/분위기 매칭 (강도 비례 가중치)
    #    - 대상의 톤 강도(%)에 비례해서 보너스/페널티 결정
    #    - 템빨 코미디 40% → 톤 매칭이 총점의 ~40% 영향
    #    - 나혼렙 시리어스 20% → 톤 매칭이 총점의 ~20% 영향
    if target.matched_tones:
        # 대상의 최대 톤 강도 = 톤 가중치 비율
        max_target_intensity = max(target.matched_tones.values())
        tone_weight = max_target_intensity  # 0.0~1.0 (=0%~100%)

        if candidate.matched_tones:
            # 코사인 유사도 방식: 각 톤 차원의 벡터 비교
            all_tones = set(target.matched_tones) | set(candidate.matched_tones)
            dot_product = 0.0
            t_magnitude = 0.0
            c_magnitude = 0.0
            for tone in all_tones:
                t_val = target.matched_tones.get(tone, 0.0)
                c_val = candidate.matched_tones.get(tone, 0.0)
                dot_product += t_val * c_val
                t_magnitude += t_val ** 2
                c_magnitude += c_val ** 2

            if t_magnitude > 0 and c_magnitude > 0:
                cosine_sim = dot_product / (t_magnitude ** 0.5 * c_magnitude ** 0.5)
                # -1~1 범위를 0~1로 변환 후, 가중치 적용
                # cosine_sim=1(완전 일치) → 보너스, 0(무관) → 0, 음수(반대) → 페널티
                tone_score = (cosine_sim * 2 - 1) * 20 * tone_weight
                score += tone_score
        else:
            # 후보에 톤 데이터 없음 → 대상 톤이 강할수록 페널티
            score -= 5 * tone_weight

    # 6. 인기도 보너스 (0~8점)
    if candidate.subscribers > 100000:
        score += 5
    elif candidate.subscribers > 50000:
        score += 3
    elif candidate.subscribers > 10000:
        score += 1

    if candidate.rating >= 9.5:
        score += 3
    elif candidate.rating >= 9.0:
        score += 2
    elif candidate.rating >= 8.0:
        score += 1

    return round(score, 2)


def recommend(query: str, top_n: int = 10, verbose: bool = False) -> List[Tuple[Webtoon, float]]:
    """메인 추천 함수"""
    print(f"웹툰 데이터 로딩 중...")
    webtoons = load_all_webtoons()
    print(f"총 {len(webtoons)}개 웹툰 로드 완료\n")

    # 대상 웹툰 찾기
    target = find_webtoon(webtoons, query)
    if not target:
        print(f"'{query}'를 찾을 수 없습니다.")
        print("비슷한 제목:")
        query_lower = query.lower()
        for wt in webtoons:
            if any(c in wt.title.lower() for c in query_lower if c.strip()):
                print(f"  - {wt.title} ({wt.platform})")
        return []

    # 대상 웹툰 정보 출력
    print(f"{'='*60}")
    print(f"  기준 작품: {target.title}")
    print(f"  플랫폼: {target.platform}")
    print(f"  장르: {', '.join(target.genre) if target.genre else '-'}")
    print(f"  태그: {', '.join(target.tags[:8]) if target.tags else '-'}")
    print(f"  테마: {', '.join(target.matched_groups) if target.matched_groups else '-'}")
    tone_str = ", ".join(f"{k}({v:.0%})" for k, v in sorted(target.matched_tones.items(), key=lambda x: -x[1])) if target.matched_tones else "-"
    print(f"  분위기: {tone_str}")
    if verbose:
        print(f"  키워드({len(target.keywords)}개): {', '.join(sorted(target.keywords)[:20])}")
    print(f"{'='*60}\n")

    # 유사도 계산
    scores = []
    for wt in webtoons:
        if wt.title == target.title and wt.platform == target.platform:
            continue
        # 같은 작품 다른 플랫폼 제외 (제목 동일)
        if wt.title == target.title:
            continue

        sim = calculate_similarity(target, wt)
        if sim > 0:
            scores.append((wt, sim))

    # 점수순 정렬
    scores.sort(key=lambda x: x[1], reverse=True)
    results = scores[:top_n]

    # 결과 출력
    print(f"추천 결과 (상위 {min(top_n, len(results))}개)")
    print(f"{'-'*60}")
    print(f"{'순위':>4}  {'점수':>5}  {'제목':<24} {'분위기':<14} {'테마'}")
    print(f"{'-'*70}")

    for i, (wt, score) in enumerate(results, 1):
        themes = ", ".join(sorted(wt.matched_groups)[:4]) if wt.matched_groups else "-"
        title_display = wt.title[:22] if len(wt.title) > 22 else wt.title
        top_tone = max(wt.matched_tones, key=wt.matched_tones.get) if wt.matched_tones else "-"
        print(f"  {i:>2}.  {score:>5.1f}  {title_display:<24} {top_tone:<14} {themes}")

    if verbose and results:
        print(f"\n{'='*60}")
        print("상세 정보")
        print(f"{'='*60}")
        for i, (wt, score) in enumerate(results[:5], 1):
            overlap_groups = target.matched_groups & wt.matched_groups
            overlap_kw = target.keywords & wt.keywords
            print(f"\n{i}. {wt.title} (점수: {score})")
            print(f"   줄거리: {wt.synopsis[:80]}..." if len(wt.synopsis) > 80 else f"   줄거리: {wt.synopsis}")
            print(f"   공통 테마: {', '.join(overlap_groups) if overlap_groups else '-'}")
            print(f"   공통 키워드: {', '.join(sorted(overlap_kw)[:10]) if overlap_kw else '-'}")
            print(f"   URL: {wt.url}")

    return results


def main():
    parser = argparse.ArgumentParser(description="웹툰 추천 엔진 (키워드 매칭)")
    parser.add_argument("query", help="추천 기준 웹툰 제목")
    parser.add_argument("--top", type=int, default=10, help="추천 개수 (기본: 10)")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 출력")
    args = parser.parse_args()

    recommend(args.query, top_n=args.top, verbose=args.verbose)


if __name__ == "__main__":
    main()
