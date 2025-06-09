FROM fedora:42

RUN dnf --setopt=install_weak_deps='False' install -y syslog-ng
RUN dnf --setopt=install_weak_deps='False' install -y procps pkill
#RUN dnf -y install wget curl
RUN dnf --setopt=install_weak_deps='False' install -y python3-flask python3-inotify

RUN mkdir -p /logserver/
RUN mkdir -p /logserver/static/
RUN mkdir -p /logserver/templates/
RUN mkdir -p /var/log/logserver/

COPY ./logserver/*.py /logserver/
COPY ./logserver/templates/*.html /logserver/templates/
COPY ./logserver/static/*.css /logserver/static/
COPY ./logserver/static/*.js /logserver/static/

COPY ./syslog-ng.conf /etc/syslog-ng/syslog-ng.conf

CMD /logserver/main.py
#STOPSIGNAL SIGRTMIN+3
