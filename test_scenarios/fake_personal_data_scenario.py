"""HUB Repository Scanner 탐지 기능 확인용 가상 데이터입니다.

아래 값은 형식 탐지 테스트만을 위해 만든 예시이며 실제 개인정보나
사용 가능한 인증정보가 아닙니다. 운영 코드에 복사하지 마세요.
"""


FAKE_CUSTOMER = {
    "name": "테스트사용자",
    "resident_registration_number": "991231-4999999",
    "phone": "010-1234-5678",
    "server_ip": "192.0.2.10",
}

# 형식 탐지 전용 가짜 키입니다. 실제 AWS에서는 사용할 수 없습니다.
FAKE_AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
FAKE_AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# 형식 탐지 전용 가짜 OpenAI 키입니다. 실제 API에서는 사용할 수 없습니다.
FAKE_OPENAI_API_KEY = "sk-proj-FAKEKEYFORSCANNERTESTONLY1234567890"

# 본문이 완전한 개인키가 아닌 탐지용 더미 블록입니다.
FAKE_SSH_PRIVATE_KEY = """-----BEGIN OPENSSH PRIVATE KEY-----
THIS_IS_NOT_A_REAL_PRIVATE_KEY_AND_CANNOT_BE_USED
-----END OPENSSH PRIVATE KEY-----"""


def print_test_scenario():
    """가상 고객과 가짜 키의 존재 여부만 출력합니다."""
    print("[TEST DATA] 고객:", FAKE_CUSTOMER)
    print("[TEST DATA] AWS 키 포함:", bool(FAKE_AWS_ACCESS_KEY and FAKE_AWS_SECRET_KEY))
    print("[TEST DATA] OpenAI 키 포함:", bool(FAKE_OPENAI_API_KEY))
    print("[TEST DATA] SSH 개인키 헤더 포함:", "BEGIN OPENSSH PRIVATE KEY" in FAKE_SSH_PRIVATE_KEY)


if __name__ == "__main__":
    print_test_scenario()
