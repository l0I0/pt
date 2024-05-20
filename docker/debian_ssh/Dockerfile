FROM debian:latest

RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    && apt-get clean

RUN mkdir /var/run/sshd

RUN useradd -ms /bin/bash admin && echo "admin:admin" | chpasswd && adduser admin sudo

RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
