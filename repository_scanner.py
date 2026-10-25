import re
from urllib.parse import quote, urlparse

import requests

git_raw_url = "https://raw.githubusercontent.com"
git_api_url = "https://api.github.com"
REQUEST_TIMEOUT = 15
MAX_FILE_SIZE = 1024 * 1024
headers = {"Accept": "application/vnd.github+json", "User-Agent": "HUB-KUCIS-Repository-Scanner"}


def parse_repository_url(url):
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or parsed.hostname not in ("github.com", "www.github.com"):
        raise ValueError("GitHub 저장소 URL을 입력해 주세요.")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        raise ValueError("URL은 https://github.com/사용자/저장소 형식이어야 합니다.")
    owner, repo = parts
    repo = repo[:-4] if repo.endswith(".git") else repo
    if not owner or not repo or not re.fullmatch(r"[A-Za-z0-9_.-]+", owner + repo):
        raise ValueError("올바른 GitHub 저장소 URL이 아닙니다.")
    return owner, repo


def _get_json(url):
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    if response.status_code == 404:
        raise ValueError("저장소를 찾을 수 없거나 비공개 저장소입니다.")
    response.raise_for_status()
    return response.json()


def repository_info(url):
    owner, repo = parse_repository_url(url)
    data = _get_json(f"{git_api_url}/repos/{owner}/{repo}")
    return owner, repo, data["default_branch"]


def git_parser(url):
    owner, repo, branch = repository_info(url)
    tree = _get_json(f"{git_api_url}/repos/{owner}/{repo}/git/trees/{quote(branch, safe='')}?recursive=1")
    if tree.get("truncated"):
        raise ValueError("저장소가 너무 커서 GitHub가 전체 파일 목록을 제공하지 않았습니다.")
    return [item["path"] for item in tree.get("tree", [])
            if item.get("type") == "blob" and item.get("size", 0) <= MAX_FILE_SIZE]


def code_parser(user_url, code_url):
    total_code = []
    owner, repo, branch = repository_info(user_url)
    for path in code_url:
        raw_url = "/".join([git_raw_url, quote(owner), quote(repo), quote(branch, safe=""), quote(path)])
        response = requests.get(raw_url, headers=headers, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200 or b"\x00" in response.content[:1024]:
            total_code.append([])
            continue
        total_code.append(response.text.replace(" ", "").split())
    return total_code


def _mask_openai_key(value):
    if len(value) <= 12:
        return value[:4] + "*" * max(0, len(value) - 4)
    return value[:8] + "*" * (len(value) - 12) + value[-4:]


def code_regex(code_data, code_url):
    detect_data = {
        'reg': [], 'call': [], 'aws_access': [], 'aws_secret': [], 'ip': [],
        'ssh_private_key': [], 'openai_api_key': []
    }
    patterns = (
        ('reg', re.compile(r"(?:[0-9]{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01]))-[1-4][0-9]{6}")),
        ('call', re.compile(r"01[016789]\D\d{3,4}\D\d{4}")),
        ('aws_access', re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])")),
        ('aws_secret', re.compile(r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])")),
        ('ip', re.compile(r"(?<![\d.])(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?![\d.])")),
        ('ssh_private_key', re.compile(r"-----BEGIN(?:OPENSSH|RSA|EC|DSA)PRIVATEKEY-----")),
        ('openai_api_key', re.compile(r"(?<![A-Za-z0-9_-])sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}(?![A-Za-z0-9_-])")),
    )
    count = sum(len(file_data) for file_data in code_data)
    detect_count = 0
    for index, file_data in enumerate(code_data):
        for code_str in file_data:
            for key, pattern in patterns:
                match = pattern.search(str(code_str))
                if match is not None:
                    content = str(code_str)
                    if key == 'ssh_private_key':
                        content = match.group(0)
                    elif key == 'openai_api_key':
                        content = _mask_openai_key(match.group(0))
                    item = [content, code_url[index]]
                    if item not in detect_data[key]:
                        detect_data[key].append(item)
                    detect_count += 1
    return detect_data, detect_count, count
