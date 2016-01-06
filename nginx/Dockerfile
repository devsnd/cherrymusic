FROM tutum/nginx

# Locales
RUN (apt-get clean \
    && apt-key update \
    && apt-get -q -y update --fix-missing \
    && apt-get -q -y update \
    && apt-get install -q -y apt-utils \
    && apt-get install -q -y locales)

ADD conf/locale.gen /etc/locale.gen
RUN (locale-gen \
    && locale-gen es_ES.UTF-8  \
    && dpkg-reconfigure locales)

ENV LANGUAGE es_ES.UTF-8 
ENV LANG es_ES.UTF-8 
ENV LC_ALL es_ES.UTF-8 
ENV LC_CTYPE es_ES.UTF-8 


RUN rm /etc/nginx/sites-enabled/default
ADD sites-enabled/ /etc/nginx/sites-enabled
