FROM fedora:42

RUN dnf --setopt=install_weak_deps='False' install -y syslog-ng
RUN dnf --setopt=install_weak_deps='False' install -y procps pkill
#RUN dnf -y install wget curl
RUN dnf --setopt=install_weak_deps='False' install -y python3-flask python3-inotify


RUN mkdir -p /logserver/

COPY ./main.py  ./front.py  ./back.py  ./conf.py  ./rotate.py  /logserver/


COPY ./base.html  ./logtable_live.html  ./search_archive.py  ./search_live.py ./back_client.py /logserver/



RUN mkdir -p  /logserver/static/
#RUN mkdir -p  /logserver/templates

RUN mkdir -p /var/log/logserver/

COPY ./logtable.html  ./login.html /logserver/
COPY ./logtable.js  ./logtable.css /logserver/static/
#COPY ./logtable_archive.html /logserver/templates/
COPY ./logtable_archive.html /logserver/

COPY ./syslog-ng.conf  /etc/syslog-ng/syslog-ng.conf

CMD /logserver/main.py
#STOPSIGNAL SIGRTMIN+3
