# Webtoon Recommander - 웹툰 소믈리에

## 📌 프로젝트 개요
> 마치 **웹툰 소믈리에**를 만드는 프로젝트.
> 모든 플랫폼의 웹툰 데이터를 수집·분석하고, 사용자의 자연어 요청에 딱 맞는 웹툰을 추천하는 AI 서비스.

## 🎯 목표
- 주요 웹툰 플랫폼의 작품 메타데이터를 체계적으로 수집
- 키워드/태그/감성 분석으로 각 웹툰의 DNA 추출
- RAG 기반 자연어 추천 엔진 구축
- "복수극인데 로맨스도 있고 그림 예쁜 웹툰" 같은 질의에 정확한 추천

## 🏗️ 아키텍처

```mermaid
flowchart TB
    subgraph DataCollection["Phase 1: 데이터 수집"]
        A1[네이버 웹툰] --> C[Crawler/Scraper]
        A2[카카오 웹툰] --> C
        A3[카카오페이지] --> C
        A4[레진코믹스] --> C
        C --> D[(webtoon/{platform}/*.md)]
    end

    subgraph Analysis["Phase 2: 데이터 분석/가공"]
        D --> E1[키워드 추출]
        D --> E2[장르/태그 분류]
        D --> E3[감성 분석]
        D --> E4[줄거리 요약]
        D --> E5[유사작품 매핑]
        E1 & E2 & E3 & E4 & E5 --> F[(Enriched Data)]
    end

    subgraph RAG["Phase 3: RAG 파이프라인"]
        F --> G1[Embedding 생성]
        G1 --> G2[(Vector DB)]
        F --> G3[(Metadata DB)]
    end

    subgraph Service["Phase 4: 추천 서비스"]
        U[사용자] -->|자연어 질의| H[LLM + RAG]
        H --> G2
        H --> G3
        H -->|추천 결과| U
    end
```

## 📊 Phase 로드맵

| Phase | 목표 | 상태 |
|-------|------|------|
| **Phase 1** | 데이터 수집 (4개 플랫폼) | ✅ 1,770개 수집 |
| **Phase 2** | 키워드/태그 분석 + Enriched DB | ⬜ 대기 |
| **Phase 3** | RAG 파이프라인 구축 | ⬜ 대기 |
| **Phase 4** | 추천 API + UI | ⬜ 대기 |

## 📁 데이터 구조

```
webtoon/
├── naver/           # 네이버 웹툰
├── kakao-webtoon/   # 카카오 웹툰
├── kakaopage/       # 카카오페이지
└── lezhin/          # 레진코믹스
```

각 웹툰은 `webtoon/{platform}/{title-slug}.md` 형식으로 저장.

## 📋 웹툰 데이터 포맷

```yaml
---
title: "작품 제목"
author:
  writer: "글 작가"
  artist: "그림 작가"
platform: "naver | kakao-webtoon | kakaopage | lezhin"
genre: ["장르1", "장르2"]
tags: ["태그1", "태그2", "태그3"]
status: "연재중 | 완결 | 휴재"
episodes: 총화수
period:
  start: "YYYY-MM-DD"
  end: "YYYY-MM-DD"
rating: 별점
subscribers: 구독자수/관심수
---
```

## 📅 변경 이력

### 2026-03-12 - Phase 1 데이터 수집 완료
- 참조: action/phase1-data-collection-20260312-174700.md
- 네이버 웹툰 API 크롤러 작성 → 1,642개 수집
- 카카오페이지 SSR 파싱 크롤러 작성 → 74개 수집 (기존 에이전트 수집 포함 90개)
- 카카오웹툰/레진코믹스 에이전트 수동 수집 → 37개
- 총 1,770개 웹툰 메타데이터 확보
- 핵심 발견: 네이버 `/api/webtoon/titlelist/*`, 카카오페이지 `__NEXT_DATA__` SSR

### 2026-03-12 - 프로젝트 초기화
- 데이터 포맷 확정 (YAML frontmatter + markdown)
- 4개 플랫폼 디렉토리 구조 생성
