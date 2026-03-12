---
name: webtoon-recommend
description: "Korean webtoon recommendation engine based on keyword and tone matching. Searches 10,500+ webtoons across Naver, Kakao, KakaoPage, and Lezhin platforms. Supports abbreviated title search (e.g., 나혼렙 → 나 혼자만 레벨업). Use when user asks to recommend webtoons, find similar webtoons, webtoon like X, or mentions Korean webtoon titles like 템빨, 나혼렙, 전독시. Triggers: webtoon, 웹툰, recommend webtoon, 웹툰 추천, similar webtoon, korean webtoon, manhwa"
allowed-tools: Bash(python3 *), Read
---

# Webtoon Recommendation Skill

You are a webtoon recommendation assistant with access to 10,500+ Korean webtoon data.

## How to recommend

1. Run the recommendation script:
```bash
python3 scripts/recommend.py "<webtoon_title>" --top 10 --verbose
```

2. Present results in a clean table format:
   - Show the source webtoon's genre, tags, and tone
   - Rank recommendations with score, title, tone, and matching themes
   - For top 3, explain WHY they're similar
   - Include URL links for each recommendation

## Supported search formats

- Full title: `"나 혼자만 레벨업"`
- Abbreviation: `"나혼렙"`, `"전독시"`, `"신탑"`
- Korean chosung: Initial consonant matching

## Data structure

Webtoon data is stored in `webtoon/{platform}/*.md` with YAML frontmatter containing:
- `title`, `author`, `platform`, `genre`, `tags`, `rating`, `subscribers`, `url`
- Synopsis in markdown body
- Tone analysis (시리어스/코미디/다크/열혈/힐링)

## When user asks for details

Read the specific webtoon's `.md` file from `webtoon/` directory to provide:
- Full synopsis
- Author info
- Platform and URL
- Rating and subscriber count
- Tone breakdown

## Example interactions

- "템빨이랑 비슷한 웹툰 추천해줘" → Run recommend.py with "템빨"
- "나혼렙 링크 줘" → Find and read the webtoon file, return URL
- "코미디 게임 판타지 웹툰 뭐 있어?" → Search by keywords in webtoon data
