FROM debian:latest

RUN apt-get update && \
    apt-get install -y softflowd && \
    rm -rf /var/lib/apt/lists/*

CMD ["softflowd", "-i", "eth0", "-n", "127.0.0.1:2055", "-v", "10", "-d"]
