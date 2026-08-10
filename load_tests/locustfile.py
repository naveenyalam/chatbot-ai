from locust import HttpUser, task, between, events
import random

class NovaUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        """Register/Login a load test user to obtain authentication token."""
        user_id = random.randint(1000, 999999)
        email = f"loadtest_user_{user_id}@nova-ai.local"
        password = "Password123!"
        
        reg_res = self.client.post("/api/auth/register", json={"email": email, "password": password, "name": f"User {user_id}"})
        if reg_res.status_code == 201 and "access_token" in reg_res.cookies:
            self.token = reg_res.cookies["access_token"]
        else:
            login_res = self.client.post("/api/auth/login", json={"email": email, "password": password})
            if login_res.status_code == 200 and "access_token" in login_res.cookies:
                self.token = login_res.cookies["access_token"]

    @task(3)
    def health_check(self):
        self.client.get("/health")

    @task(2)
    def user_me(self):
        if self.token:
            self.client.get("/api/auth/me", cookies={"access_token": self.token})

    @task(4)
    def chat_stream(self):
        if self.token:
            payload = {
                "messages": [{"role": "user", "content": "Benchmark chat streaming response speed"}],
                "stream": True,
                "mode": "chat"
            }
            self.client.post("/api/chat/stream", json=payload, cookies={"access_token": self.token}, name="/api/chat/stream")

    @task(2)
    def document_list(self):
        if self.token:
            self.client.get("/api/documents", cookies={"access_token": self.token})

    @task(1)
    def agent_execution(self):
        if self.token:
            payload = {
                "messages": [{"role": "user", "content": "Calculate 125 * 8"}],
                "stream": True,
                "mode": "agent"
            }
            self.client.post("/api/chat/stream", json=payload, cookies={"access_token": self.token}, name="/api/chat/stream [agent]")
