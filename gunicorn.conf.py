worker_class = "uvicorn.workers.UvicornWorker"
workers = 2
timeout = 180        # must be > openai timeout (120s)
graceful_timeout = 30
keepalive = 5
