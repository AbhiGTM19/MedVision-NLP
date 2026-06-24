import time

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # In-memory dictionary mapping IP to request counts
        # Structure: { "ip_address": {"count": int, "start_time": float} }
        self.request_counts = {}

    def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {"count": 0, "start_time": current_time}

        user_data = self.request_counts[client_ip]

        # Reset the counter if the time window has expired
        if current_time - user_data["start_time"] > self.window_seconds:
            user_data["count"] = 0
            user_data["start_time"] = current_time

        # Block the request if they exceeded the limit
        if user_data["count"] >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="This is a portfolio demo project and hence rate limiting has been implemented accordingly."
            )

        # Increment counter
        user_data["count"] += 1

# Global dependency instance
rate_limit_dependency = RateLimiter(max_requests=10, window_seconds=3600)
