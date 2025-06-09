FROM fedora:42

RUN dnf --setopt=install_weak_deps='False' install -y syslog-ng
RUN dnf --setopt=install_weak_deps='False' install -y procps pkill
#RUN dnf -y install wget curl
RUN dnf --setopt=install_weak_deps='False' install -y python3-flask python3-inotify
#COPY ./logserver.py /logserver.py
COPY ./main.py /logserver.py
COPY ./front.py /front.py
COPY ./back.py /back.py
COPY ./conf.py /conf.py

RUN mkdir -p  /static/
COPY ./logtable.html /logtable.html
COPY ./login.html /login.html
COPY ./logtable.js /static/logtable.js
COPY ./logtable.css /static/logtable.css

COPY ./syslog-ng.conf  /etc/syslog-ng/syslog-ng.conf

CMD /logserver.py
#STOPSIGNAL SIGRTMIN+3
