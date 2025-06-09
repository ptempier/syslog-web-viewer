FROM fedora:42
#RUN dnf --setopt=install_weak_deps='False' install -y systemd

#RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
#systemd-tmpfiles-setup.service ] || rm -f $i; done); \
#rm -f /lib/systemd/system/multi-user.target.wants/*;\
#rm -f /etc/systemd/system/*.wants/*;\
#rm -f /lib/systemd/system/local-fs.target.wants/*; \
#rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
#rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
#rm -f /lib/systemd/system/basic.target.wants/*;\
#rm -f /lib/systemd/system/anaconda.target.wants/*;

RUN dnf --setopt=install_weak_deps='False' install -y syslog-ng
#ENTRYPOINT /usr/lib/systemd/systemd-journald
#RUN /usr/lib/systemd/systemd-journald
RUN dnf --setopt=install_weak_deps='False' install -y procps pkill
#RUN dnf -y install wget curl
#RUN mkdir -p /github && cd /github &&  git clone https://github.com/gdraheim/docker-systemctl-replacement.git
#RUN cd / && wget "https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/refs/heads/master/files/docker/systemctl.py" && chmod ugo+x /systemctl.py
#RUN dnf --setopt=install_weak_deps='False' install -y python3

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


#COPY ./syslog /var/log/syslog
#RUN cd / && wget "https://raw.githubusercontent.com/gdraheim/docker-systemctl-replacement/refs/heads/master/files/docker/systemctl3.py"  && chmod ugo+x /systemctl3.py  && rm -f /usr/bin/systemctl && ln -s /systemctl3.py /usr/bin/systemctl


#    system();
#    internal();
#    # udp(ip(0.0.0.0) port(514));
#RUN sed -i 's/system();//' /etc/syslog-ng/syslog-ng.conf
#RUN sed -i 's/# udp(ip(0.0.0.0) port(514))\;/udp(ip(0.0.0.0) port(7322));/' /etc/syslog-ng/syslog-ng.conf

COPY ./syslog-ng.conf  /etc/syslog-ng/syslog-ng.conf


#RUN sed -i 's/DEBUG_AFTER = False/DEBUG_AFTER = True/' /systemctl3.py
#RUN sed -i 's/DEBUG_STATUS = False/DEBUG_STATUS = True'/ /systemctl3.py
#RUN sed -i 's/DEBUG_BOOTTIME = False/DEBUG_BOOTTIME = True/' /systemctl3.py
#RUN sed -i 's/DEBUG_INITLOOP = False/DEBUG_INITLOOP = True/' /systemctl3.py
#RUN sed -i 's/DEBUG_KILLALL = False/DEBUG_KILLALL = True/' /systemctl3.py
#RUN sed -i 's/DEBUG_FLOCK = False/DEBUG_FLOCK = True/' /systemctl3.py
#RUN sed -i 's/DebugPrintResult = False/DebugPrintResult = True/' /systemctl3.py


#RUN sed -i 's/Wants=local-fs.target swap.target/Wants=local-fs.target swap.target systemd-journald.service/' /lib/systemd/system/sysinit.target
#RUN sed -i 's/After=local-fs.target swap.target/After=local-fs.target swap.target systemd-journald.service/' /lib/systemd/system/sysinit.target

#RUN sed -i 's/DefaultDependencies=no//' /usr/lib/systemd/system/systemd-journald.service

#RUN /systemctl3.py disable rpmdb-rebuild.service
#RUN /systemctl3.py enable systemd-journald.socket || true
#RUN /systemctl3.py enable systemd-journald.socket || true
#RUN ln -s /usr/lib/systemd/system/systemd-journald.service   /etc/systemd/system/systemd-journald.service
#RUN ln -s /usr/lib/systemd/system/systemd-journald.socket   /etc/systemd/system/systemd-journald.socket
#RUN ln -s ./systemd-journald.service /usr/lib/systemd/system/sysinit.target.wants/systemd-journald.service 
#ENTRYPOINT /github/docker-systemctl-replacement/files/docker/systemctl.py
#CMD /systemctl3.py
#CMD /sbin/init
CMD /logserver.py
#STOPSIGNAL SIGRTMIN+3
