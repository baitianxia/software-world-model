package dev.acme.auth;

public final class LoginService {
    // 多字节字符只用于验证 frontend 的 UTF-8 byte range 规范化。
    public boolean authenticate(boolean credentialsValid) {
        if (!credentialsValid) {
            recordFailure();
            recordFailure();
            throw new IllegalStateException();
        }
        return issueSession();
    }

    private void recordFailure() {
        return;
    }

    private boolean issueSession() {
        return true;
    }
}
