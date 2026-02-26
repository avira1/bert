#!/usr/bin/env python3
"""Fetch latest Medicare news from KFF Health News and send digest notifications."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import html
import os
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import urljoin

import requests

TOPIC_URL = "https://kffhealthnews.org/topics/medicare/"
USER_AGENT = "medicare-news-digest/1.0 (+https://kffhealthnews.org/topics/medicare/)"
TIMEOUT_SECONDS = 20


@dataclasses.dataclass
class Article:
    title: str
    url: str
    published: str | None = None
    summary: str | None = None


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.current_href: str | None = None
        self.current_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attr_map = dict(attrs)
        href = attr_map.get("href")
        if href:
            self.current_href = href
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.current_href:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self.current_href:
            return
        text = clean_text(" ".join(self.current_text))
        if text:
            self.links.append((self.current_href, text))
        self.current_href = None
        self.current_text = []


def get_html(url: str) -> str:
    response = requests.get(
        url,
        timeout=TIMEOUT_SECONDS,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    return response.text


def extract_article_candidates(topic_html: str, base_url: str = TOPIC_URL) -> list[Article]:
    parser = AnchorParser()
    parser.feed(topic_html)

    seen_urls: set[str] = set()
    candidates: list[Article] = []

    for href, title in parser.links:
        article_url = urljoin(base_url, href)
        if not article_url.startswith("https://kffhealthnews.org/"):
            continue
        if "/topics/medicare/" in article_url:
            continue
        if article_url in seen_urls:
            continue
        if len(title) < 15:
            continue

        candidates.append(Article(title=title, url=article_url))
        seen_urls.add(article_url)

    return candidates


def clean_text(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_article_body(article_html: str) -> str:
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", article_html, flags=re.IGNORECASE | re.DOTALL)
    cleaned: list[str] = []

    for raw_paragraph in paragraphs:
        without_tags = re.sub(r"<[^>]+>", " ", raw_paragraph)
        paragraph = clean_text(without_tags)
        if len(paragraph.split()) > 8:
            cleaned.append(paragraph)

    return "\n".join(cleaned)


def summarize_text(text: str, max_sentences: int = 3) -> str:
    if not text:
        return "Summary unavailable."

    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if len(s.split()) >= 8]
    if not sentences:
        return "Summary unavailable."

    return " ".join(sentences[:max_sentences])


def build_digest(articles: Iterable[Article]) -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"KFF Medicare News Digest ({timestamp})",
        "",
    ]

    for index, article in enumerate(articles, start=1):
        lines.append(f"{index}. {article.title}")
        lines.append(f"   Link: {article.url}")
        lines.append(f"   Summary: {article.summary or 'Summary unavailable.'}")
        lines.append("")

    if len(lines) <= 2:
        lines.append("No matching articles were found.")

    return "\n".join(lines).strip()


def send_email(message: str) -> None:
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    sender = os.environ["EMAIL_FROM"]
    recipient = os.environ["EMAIL_TO"]

    email_message = MIMEMultipart("alternative")
    email_message["Subject"] = "KFF Medicare News Digest"
    email_message["From"] = sender
    email_message["To"] = recipient
    email_message.attach(MIMEText(message, "plain", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(sender, [recipient], email_message.as_string())


def send_to_teams(message: str) -> None:
    webhook_url = os.environ["TEAMS_WEBHOOK_URL"]
    response = requests.post(webhook_url, json={"text": message}, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()


def collect_articles(topic_url: str, max_articles: int) -> list[Article]:
    topic_html = get_html(topic_url)
    candidates = extract_article_candidates(topic_html, base_url=topic_url)
    selected = candidates[:max_articles]

    for article in selected:
        article_html = get_html(article.url)
        body = extract_article_body(article_html)
        article.summary = summarize_text(body)

    return selected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-url", default=TOPIC_URL, help="KFF topic page URL")
    parser.add_argument("--max-articles", type=int, default=5, help="Maximum number of articles")
    parser.add_argument(
        "--delivery",
        choices=["none", "email", "teams", "both"],
        default="none",
        help="Send digest via email, Teams, both, or print only",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    articles = collect_articles(topic_url=args.topic_url, max_articles=args.max_articles)
    digest = build_digest(articles)
    print(digest)

    if args.delivery in {"email", "both"}:
        send_email(digest)
    if args.delivery in {"teams", "both"}:
        send_to_teams(digest)


if __name__ == "__main__":
    main()
